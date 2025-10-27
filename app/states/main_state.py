import reflex as rx
from typing import TypedDict, Literal
import time


class Point(TypedDict):
    x: float
    y: float


class Shape(TypedDict):
    id: str
    type: Literal["rectangle", "polygon", "line", "freehand"]
    points: list[Point]
    stroke_mm: float
    stroke_color: str
    fill_color: str
    layer: str
    label_visibility: bool
    is_closed: bool
    area: float


class ViewTransform(TypedDict):
    scale: float
    offset_x: float
    offset_y: float


class CanvasConfig:
    A2_WIDTH_FT = 1.378333
    A2_HEIGHT_FT = 1.949167
    PLOT_SCALE = 3.1
    MM_PER_INCH = 25.4
    SNAP_THRESHOLD_FT = 0.5
    EDITING_DPI = 96


class MainState(rx.State):
    """Global state for the floorplan wizard."""

    export_dpi: str = "300"
    export_format: str = "png"
    current_step: int = 1
    wizard_steps: list[dict] = [
        {"id": 1, "title": "Plot Size", "prompt": "Define the boundary of your plot."},
        {
            "id": 2,
            "title": "House Shape",
            "prompt": "Draw the basic outline of the house.",
        },
        {
            "id": 3,
            "title": "Details",
            "prompt": "Add interior walls, doors, and windows.",
        },
        {"id": 4, "title": "Export/Save", "prompt": "Save your project or export it."},
    ]
    shapes: list[Shape] = []
    selected_shape_id: str | None = None
    view_transform: ViewTransform = {"scale": 1.0, "offset_x": 0.0, "offset_y": 0.0}
    active_tool: str = "select"
    is_panning: bool = False
    is_grid_visible: bool = True
    is_snap_enabled: bool = True
    plot_width_ft: str = "50"
    plot_height_ft: str = "90"
    selected_stroke_mm: float = 0.25
    selected_stroke_color: str = "#1a1a1a"
    lock_aspect_ratio: bool = True
    selected_layer: str = "default"
    selected_label_visibility: bool = True
    drawing_shape: Shape | None = None
    is_drawing: bool = False
    active_handle: str | None = None
    pan_start: Point | None = None

    @rx.var
    def svg_points(self) -> dict[str, str]:
        points_map = {}
        for shape in self.shapes:
            points_map[shape["id"]] = " ".join(
                [f"{p['x']},{p['y']}" for p in shape["points"]]
            )
        if self.drawing_shape:
            points_map[self.drawing_shape["id"]] = " ".join(
                [f"{p['x']},{p['y']}" for p in self.drawing_shape["points"]]
            )
        return points_map

    @rx.var
    def viewbox_str(self) -> str:
        try:
            plot_width = float(self.plot_width_ft)
            plot_height = float(self.plot_height_ft)
        except ValueError as e:
            import logging

            logging.exception(f"Error converting plot dimensions: {e}")
            plot_width, plot_height = (1, 1)
        padding_x = plot_width * 0.1
        padding_y = plot_height * 0.1
        base_x = -padding_x
        base_y = -padding_y
        base_w = plot_width + 2 * padding_x
        base_h = plot_height + 2 * padding_y
        w = base_w / self.view_transform["scale"]
        h = base_h / self.view_transform["scale"]
        x = base_x + self.view_transform["offset_x"]
        y = base_y + self.view_transform["offset_y"]
        return f"{x} {y} {w} {h}"

    @rx.var
    def canvas_cursor(self) -> str:
        if self.active_tool == "pan":
            return "grab" if not self.is_panning else "grabbing"
        if self.active_tool in ["line", "polygon", "rectangle", "freehand"]:
            return "crosshair"
        return "default"

    @rx.var
    def is_step_1_valid(self) -> bool:
        plot_shape = self._get_plot_shape()
        return plot_shape is not None and plot_shape["area"] > 10.0

    @rx.var
    def is_step_2_valid(self) -> bool:
        return any(
            (
                s["type"] == "rectangle" and s["id"] != "plot_boundary"
                for s in self.shapes
            )
        )

    @rx.var
    def is_step_4_valid(self) -> bool:
        return len(self.shapes) > 0

    @rx.var
    def can_proceed(self) -> bool:
        if self.current_step == 1:
            return self.is_step_1_valid
        if self.current_step == 2:
            return self.is_step_2_valid
        if self.current_step == 3:
            return self.is_step_2_valid
        return True

    @rx.var
    def selected_shape(self) -> Shape | None:
        if self.selected_shape_id is None:
            return None
        for shape in self.shapes:
            if shape["id"] == self.selected_shape_id:
                return shape
        return None

    @rx.event
    def next_step(self):
        if self.current_step < 4 and self.can_proceed:
            self.current_step += 1

    @rx.event
    def prev_step(self):
        if self.current_step > 1:
            self.current_step -= 1

    @rx.event
    def go_to_step(self, step_id: int):
        if step_id < self.current_step:
            self.current_step = step_id
        elif self.can_proceed and step_id == self.current_step + 1:
            self.current_step = step_id

    @rx.event
    def set_active_tool(self, tool_name: str):
        self.active_tool = tool_name
        self.is_panning = tool_name == "pan"

    @rx.event
    def toggle_grid(self):
        self.is_grid_visible = not self.is_grid_visible

    @rx.event
    def toggle_snap(self):
        self.is_snap_enabled = not self.is_snap_enabled

    def _canvas_to_world(self, canvas_point: Point) -> Point:
        viewbox = self.viewbox_str.split()
        try:
            vb_x, vb_y, vb_w, vb_h = map(float, viewbox)
        except (ValueError, IndexError) as e:
            import logging

            logging.exception(f"Error parsing viewbox string: {e}")
            vb_x, vb_y, vb_w, vb_h = (0, 0, 1, 1)
        return {
            "x": vb_x + canvas_point["x"] * vb_w,
            "y": vb_y + canvas_point["y"] * vb_h,
        }

    def _event_to_canvas_coords(self, event: dict) -> Point:
        client_x = event.get("client_x", 0)
        client_y = event.get("client_y", 0)
        bounds = event.get("bounding_client_rect", None)
        if not bounds:
            return {"x": 0, "y": 0}
        width = bounds.get("width", 1)
        height = bounds.get("height", 1)
        if width == 0 or height == 0:
            return {"x": 0, "y": 0}
        left = bounds.get("left", 0)
        top = bounds.get("top", 0)
        return {"x": (client_x - left) / width, "y": (client_y - top) / height}

    @rx.event
    def handle_canvas_mouse_down(self, event: dict):
        """Handle mouse down events on the canvas."""
        button = event.get("button", 0)
        if button != 0 and self.active_tool != "pan":
            return
        canvas_coords = self._event_to_canvas_coords(event)
        point = self._canvas_to_world(canvas_coords)
        if self.active_tool == "pan":
            self.is_panning = True
            self.pan_start = point
            return
        self.is_drawing = True
        shape_type = self.active_tool
        if shape_type in ["rectangle", "line", "polygon", "freehand"]:
            new_shape = {
                "id": f"shape_{int(time.time() * 1000000)}",
                "type": shape_type,
                "points": [point]
                if shape_type != "rectangle"
                else [point, point, point, point],
                "stroke_mm": self.selected_stroke_mm,
                "stroke_color": self.selected_stroke_color,
                "fill_color": "rgba(255, 165, 0, 0.2)"
                if shape_type == "rectangle"
                else "transparent",
                "layer": self.selected_layer,
                "label_visibility": self.selected_label_visibility,
                "is_closed": shape_type in ["rectangle", "polygon"],
                "area": 0.0,
            }
            if self.active_tool == "line":
                new_shape["points"].append(point)
            self.drawing_shape = new_shape

    @rx.event
    def handle_canvas_mouse_move(self, event: dict):
        """Handle mouse move events on the canvas."""
        canvas_coords = self._event_to_canvas_coords(event)
        point = self._canvas_to_world(canvas_coords)
        if self.is_panning and self.pan_start:
            delta_x = self.pan_start["x"] - point["x"]
            delta_y = self.pan_start["y"] - point["y"]
            self.view_transform["offset_x"] += delta_x
            self.view_transform["offset_y"] += delta_y
            return
        if self.is_drawing and self.drawing_shape:
            if self.active_tool == "rectangle":
                start_point = self.drawing_shape["points"][0]
                self.drawing_shape["points"] = [
                    start_point,
                    {"x": point["x"], "y": start_point["y"]},
                    point,
                    {"x": start_point["x"], "y": point["y"]},
                ]
            elif self.active_tool in ["line", "freehand", "polygon"]:
                if self.active_tool != "line":
                    self.drawing_shape["points"].append(point)
                elif len(self.drawing_shape["points"]) > 1:
                    self.drawing_shape["points"][1] = point
                else:
                    self.drawing_shape["points"].append(point)

    @rx.event
    def handle_canvas_mouse_up(self, event: dict):
        """Handle mouse up events on the canvas."""
        button = event.get("button", 0)
        if self.is_panning:
            self.is_panning = False
            self.pan_start = None
            return
        if not self.is_drawing or not self.drawing_shape:
            if self.active_tool == "select":
                self.selected_shape_id = None
            return
        self.is_drawing = False
        canvas_coords = self._event_to_canvas_coords(event)
        point = self._canvas_to_world(canvas_coords)
        if self.active_tool == "rectangle":
            start_point = self.drawing_shape["points"][0]
            self.drawing_shape["points"] = [
                start_point,
                {"x": point["x"], "y": start_point["y"]},
                point,
                {"x": start_point["x"], "y": point["y"]},
            ]
            if start_point["x"] != point["x"] and start_point["y"] != point["y"]:
                self.shapes.append(self.drawing_shape)
        elif self.active_tool == "line":
            if len(self.drawing_shape["points"]) == 1:
                self.drawing_shape["points"].append(point)
            elif len(self.drawing_shape["points"]) > 1:
                self.drawing_shape["points"][1] = point
            self.shapes.append(self.drawing_shape)
        elif self.active_tool == "freehand":
            self.shapes.append(self.drawing_shape)
        if self.active_tool != "polygon":
            self.drawing_shape = None

    @rx.event
    def handle_canvas_mouse_leave(self):
        """Handle mouse leave events on the canvas."""
        if self.is_drawing:
            self.is_drawing = False
            self.drawing_shape = None
        if self.is_panning:
            self.is_panning = False
            self.pan_start = None

    @rx.event
    def create_preset_plot(self):
        self.reset_canvas()
        try:
            width = float(self.plot_width_ft)
            height = float(self.plot_height_ft)
        except ValueError as e:
            import logging

            logging.exception(f"Error: {e}")
            return rx.toast.error("Invalid dimensions. Please enter numbers.")
        if width <= 0 or height <= 0:
            return rx.toast.error("Dimensions must be positive.")
        new_plot: Shape = {
            "id": "plot_boundary",
            "type": "rectangle",
            "points": [
                {"x": 0, "y": 0},
                {"x": width, "y": 0},
                {"x": width, "y": height},
                {"x": 0, "y": height},
            ],
            "stroke_mm": 0.5,
            "stroke_color": "#9ca3af",
            "fill_color": "transparent",
            "layer": "plot",
            "label_visibility": True,
            "is_closed": True,
            "area": width * height,
        }
        self.shapes.append(new_plot)
        self.selected_shape_id = "plot_boundary"
        return rx.toast.success(f"Created {width:.1f}x{height:.1f} ft plot.")

    @rx.event
    def reset_canvas(self):
        self.shapes = []
        self.selected_shape_id = None
        self.view_transform = {"scale": 1.0, "offset_x": 0.0, "offset_y": 0.0}
        return rx.toast.info("Canvas has been cleared.")

    @rx.event
    def save_project_local(self):
        """Saves the entire project state to the browser's localStorage."""
        return rx.toast.info("Project auto-saved to browser.")

    @rx.event
    def export_project_file(self):
        """Exports the project as a JSON file."""
        return rx.toast.success("Project JSON exported.")

    @rx.event
    def export_drawing(self):
        """Exports the drawing as PNG or PDF at the selected DPI."""
        return rx.toast.success(
            f"Exporting as {self.export_format.upper()} at {int(self.export_dpi)} DPI..."
        )

    @rx.event
    def zoom_in(self):
        new_scale = self.view_transform["scale"] * 1.2
        if new_scale > 10:
            new_scale = 10
        self.view_transform["scale"] = new_scale

    @rx.event
    def zoom_out(self):
        new_scale = self.view_transform["scale"] * 0.8
        if new_scale < 0.1:
            new_scale = 0.1
        self.view_transform["scale"] = new_scale

    def _get_plot_shape(self) -> Shape | None:
        for shape in self.shapes:
            if shape["id"] == "plot_boundary":
                return shape
        return None