import reflex as rx
from app.states.main_state import MainState


def tool_button(label: str, icon: str, tool_name: str, **kwargs) -> rx.Component:
    is_active = MainState.active_tool == tool_name
    return rx.el.button(
        rx.icon(icon, class_name="size-5"),
        on_click=lambda: MainState.set_active_tool(tool_name),
        class_name=rx.cond(
            is_active,
            "p-2 rounded-md bg-orange-200 text-orange-700 shadow-inner",
            "p-2 rounded-md hover:bg-neutral-200",
        ),
        title=label,
        aria_label=label,
        **kwargs,
    )


def canvas_toolbar() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            tool_button("Select", "mouse-pointer-2", "select"),
            tool_button("Line", "minus", "line"),
            tool_button("Polygon", "hexagon", "polygon"),
            tool_button("Rectangle", "square", "rectangle"),
            tool_button("Freehand", "pencil", "freehand"),
            class_name="flex items-center gap-1 p-1 bg-neutral-100 rounded-lg border",
        ),
        rx.el.div(
            tool_button("Pan", "hand", "pan"),
            rx.el.button(
                rx.icon("zoom-in", class_name="size-5"),
                title="Zoom In",
                class_name="p-2 rounded-md hover:bg-neutral-200",
            ),
            rx.el.button(
                rx.icon("zoom-out", class_name="size-5"),
                title="Zoom Out",
                class_name="p-2 rounded-md hover:bg-neutral-200",
            ),
            class_name="flex items-center gap-1 p-1 bg-neutral-100 rounded-lg border",
        ),
        rx.el.div(
            rx.el.button(
                rx.icon("grid_3x3", class_name="size-5"),
                on_click=MainState.toggle_grid,
                class_name=rx.cond(
                    MainState.is_grid_visible,
                    "p-2 rounded-md bg-orange-100 text-orange-600",
                    "p-2 rounded-md hover:bg-neutral-200",
                ),
                title="Toggle Grid",
            ),
            rx.el.button(
                rx.icon("magnet", class_name="size-5"),
                on_click=MainState.toggle_snap,
                class_name=rx.cond(
                    MainState.is_snap_enabled,
                    "p-2 rounded-md bg-orange-100 text-orange-600",
                    "p-2 rounded-md hover:bg-neutral-200",
                ),
                title="Toggle Snap",
            ),
            class_name="flex items-center gap-1 p-1 bg-neutral-100 rounded-lg border",
        ),
        rx.el.div(
            rx.el.button(
                rx.icon("undo-2", class_name="size-5"),
                title="Undo",
                class_name="p-2 rounded-md hover:bg-neutral-200",
            ),
            rx.el.button(
                rx.icon("redo-2", class_name="size-5"),
                title="Redo",
                class_name="p-2 rounded-md hover:bg-neutral-200",
            ),
            class_name="flex items-center gap-1 p-1 bg-neutral-100 rounded-lg border",
        ),
        rx.el.div(
            rx.el.button(
                rx.icon("download", class_name="size-5"),
                title="Export",
                class_name="p-2 rounded-md hover:bg-neutral-200",
            ),
            rx.el.button(
                rx.icon("save", class_name="size-5"),
                title="Save",
                class_name="p-2 rounded-md hover:bg-neutral-200",
            ),
            class_name="flex items-center gap-1 p-1 bg-neutral-100 rounded-lg border",
        ),
        class_name="absolute top-2 left-1/2 -translate-x-1/2 z-10 flex items-center gap-4 bg-white p-2 rounded-xl shadow-lg border",
    )


from app.states.main_state import Shape


def shape_renderer(shape: Shape) -> rx.Component:
    return rx.el.g(
        rx.match(
            shape["type"],
            (
                "rectangle",
                rx.el.polygon(
                    points=MainState.svg_points[shape["id"]],
                    stroke=shape["stroke_color"],
                    stroke_width=shape["stroke_mm"],
                    fill=shape["fill_color"],
                ),
            ),
            (
                "line",
                rx.el.svg.polyline(
                    points=MainState.svg_points[shape["id"]],
                    stroke=shape["stroke_color"],
                    stroke_width=shape["stroke_mm"],
                    fill="none",
                ),
            ),
            rx.el.g(),
        )
    )


def canvas_area() -> rx.Component:
    """The main drawing canvas area with toolbar."""
    return rx.el.div(
        canvas_toolbar(),
        rx.el.div(
            rx.el.svg(
                rx.el.g(
                    rx.foreach(MainState.shapes, shape_renderer),
                    rx.cond(
                        MainState.drawing_shape.is_not_none(),
                        shape_renderer(MainState.drawing_shape),
                        rx.el.g(),
                    ),
                ),
                on_mouse_down=MainState.handle_canvas_mouse_down,
                on_mouse_move=MainState.handle_canvas_mouse_move,
                on_mouse_up=MainState.handle_canvas_mouse_up,
                on_mouse_leave=MainState.handle_canvas_mouse_up,
                viewBox=f"0 0 {MainState.plot_width_ft} {MainState.plot_height_ft}",
                preserve_aspect_ratio="xMidYMid meet",
                class_name="w-full h-full bg-white shadow-inner border border-neutral-300",
            ),
            class_name="w-full h-full",
            style={"aspect-ratio": "1.414"},
        ),
        class_name="flex-1 p-8 flex items-center justify-center relative bg-neutral-200",
        aria_label="Drawing Canvas",
    )