import reflex as rx
from app.states.main_state import MainState


def property_input(label: str, **kwargs) -> rx.Component:
    return rx.el.div(
        rx.el.label(label, class_name="text-sm font-medium text-neutral-600 mb-1"),
        rx.el.input(
            class_name="w-full p-2 border border-neutral-300 rounded-md shadow-inner text-sm",
            **kwargs,
        ),
        class_name="mb-4",
    )


def properties_panel() -> rx.Component:
    return rx.el.aside(
        rx.el.h2(
            "Properties",
            class_name="text-lg font-bold text-neutral-800 border-b pb-2 mb-4",
        ),
        rx.cond(
            MainState.selected_shape.is_not_none(),
            rx.el.div(
                rx.el.p(
                    f"ID: {MainState.selected_shape['id']}",
                    class_name="text-xs text-neutral-500 mb-4 truncate",
                ),
                property_input(
                    "Stroke (mm)",
                    default_value=MainState.selected_shape["stroke_mm"].to_string(),
                    type="number",
                    step="0.05",
                ),
                property_input(
                    "Stroke Color",
                    type="color",
                    default_value=MainState.selected_shape["stroke_color"],
                ),
                rx.el.div(
                    rx.el.label(
                        "Dimensions (ft)",
                        class_name="text-sm font-medium text-neutral-600 mb-1",
                    ),
                    rx.el.p(
                        "W: 50.00, H: 90.00",
                        class_name="text-sm p-2 bg-neutral-100 rounded",
                    ),
                    class_name="mb-4",
                ),
                rx.el.div(
                    rx.el.label(
                        rx.el.input(
                            type="checkbox",
                            checked=MainState.lock_aspect_ratio,
                            on_change=MainState.set_lock_aspect_ratio,
                        ),
                        " Lock Aspect Ratio",
                        class_name="flex items-center gap-2 text-sm font-medium text-neutral-600 cursor-pointer",
                    ),
                    class_name="mb-4",
                ),
                property_input(
                    "Layer", default_value=MainState.selected_shape["layer"]
                ),
                rx.el.div(
                    rx.el.label(
                        rx.el.input(
                            type="checkbox",
                            checked=MainState.selected_shape["label_visibility"],
                        ),
                        " Show Labels",
                        class_name="flex items-center gap-2 text-sm font-medium text-neutral-600 cursor-pointer",
                    ),
                    class_name="mb-4",
                ),
            ),
            rx.el.div(
                rx.el.p(
                    "No object selected.", class_name="text-sm text-neutral-500 italic"
                ),
                class_name="flex items-center justify-center h-full text-center",
            ),
        ),
        class_name="w-64 bg-white p-4 border-l shadow-md",
        aria_label="Properties Panel",
    )