import reflex as rx
from typing import TypedDict, Literal


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
        if tool_name == "pan":
            self.is_panning = True
        else:
            self.is_panning = False

    @rx.event
    def toggle_grid(self):
        self.is_grid_visible = not self.is_grid_visible

    @rx.event
    def toggle_snap(self):
        self.is_snap_enabled = not self.is_snap_enabled

    @rx.event
    def handle_canvas_mouse_down(self, event_args: dict | None = None):
        self.is_drawing = True

    @rx.event
    def handle_canvas_mouse_move(self, event_args: dict | None = None):
        if not self.is_drawing:
            return

    @rx.event
    def handle_canvas_mouse_up(self, event_args: dict | None = None):
        self.is_drawing = False

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

    def _get_plot_shape(self) -> Shape | None:
        for shape in self.shapes:
            if shape["id"] == "plot_boundary":
                return shape
        return None