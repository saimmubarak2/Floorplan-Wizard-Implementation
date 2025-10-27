import reflex as rx
from app.states.main_state import MainState


def _select_input(
    options: list[str], default_value: str, on_change: rx.event.EventType
) -> rx.Component:
    return rx.el.select(
        rx.foreach(options, lambda opt: rx.el.option(opt, value=opt)),
        default_value=default_value,
        on_change=on_change,
        class_name="w-full p-2 border border-neutral-300 rounded-md shadow-inner text-sm bg-white",
    )


def export_panel() -> rx.Component:
    return rx.el.div(
        rx.el.h3("4. Export & Save", class_name="font-semibold mb-2 text-neutral-700"),
        rx.el.div(
            rx.el.label("DPI:", class_name="text-sm font-medium"),
            _select_input(
                ["96", "150", "300", "600"],
                MainState.export_dpi.to_string(),
                MainState.set_export_dpi,
            ),
            class_name="mb-2",
        ),
        rx.el.div(
            rx.el.label("Format:", class_name="text-sm font-medium"),
            _select_input(
                ["png", "pdf"], MainState.export_format, MainState.set_export_format
            ),
            class_name="mb-4",
        ),
        sidebar_button("Export Drawing", MainState.export_drawing, "download"),
        sidebar_button(
            "Save Project",
            MainState.save_project_local,
            "save",
            class_name="!bg-blue-600 hover:!bg-blue-700 mt-2",
        ),
        sidebar_button(
            "Export Project (JSON)",
            MainState.export_project_file,
            "file-down",
            class_name="!bg-gray-500 hover:!bg-gray-600 mt-2",
        ),
        class_name="p-4 bg-neutral-50 rounded-lg border",
    )


def sidebar_button(
    text: str, on_click: rx.event.EventType, icon: str, **kwargs
) -> rx.Component:
    base_class_name = "w-full flex items-center justify-center px-4 py-2 text-sm font-semibold text-white bg-orange-600 rounded-lg shadow-sm hover:bg-orange-700 transition-colors disabled:bg-neutral-400"
    additional_class_name = kwargs.pop("class_name", "")
    return rx.el.button(
        rx.icon(icon, class_name="mr-2 size-4"),
        text,
        on_click=on_click,
        class_name=f"{base_class_name} {additional_class_name}".strip(),
        **kwargs,
    )


def sidebar() -> rx.Component:
    return rx.el.aside(
        rx.el.div(
            rx.el.h2(
                "Controls",
                class_name="text-lg font-bold text-neutral-800 border-b pb-2 mb-4",
            ),
            rx.cond(
                MainState.current_step == 1,
                rx.el.div(
                    rx.el.h3(
                        "1. Plot Size (ft)",
                        class_name="font-semibold mb-2 text-neutral-700",
                    ),
                    rx.el.div(
                        rx.el.label("Width:", class_name="text-sm font-medium"),
                        rx.el.input(
                            default_value=MainState.plot_width_ft,
                            on_change=MainState.set_plot_width_ft,
                            placeholder="e.g., 50",
                            class_name="w-full p-2 border border-neutral-300 rounded-md shadow-inner text-sm",
                        ),
                        class_name="mb-2",
                    ),
                    rx.el.div(
                        rx.el.label("Height:", class_name="text-sm font-medium"),
                        rx.el.input(
                            default_value=MainState.plot_height_ft,
                            on_change=MainState.set_plot_height_ft,
                            placeholder="e.g., 90",
                            class_name="w-full p-2 border border-neutral-300 rounded-md shadow-inner text-sm",
                        ),
                        class_name="mb-4",
                    ),
                    sidebar_button(
                        "Create Plot", MainState.create_preset_plot, "square_plus"
                    ),
                    class_name="p-4 bg-neutral-50 rounded-lg border",
                ),
                None,
            ),
            rx.cond(
                MainState.current_step == 2,
                rx.el.div(
                    rx.el.h3(
                        "2. House Shape",
                        class_name="font-semibold mb-2 text-neutral-700",
                    ),
                    rx.el.p(
                        "Use the drawing tools on the canvas to create the house outline.",
                        class_name="text-sm text-neutral-600",
                    ),
                    class_name="p-4 bg-neutral-50 rounded-lg border",
                ),
                None,
            ),
            rx.cond(
                MainState.current_step == 3,
                rx.el.div(
                    rx.el.h3(
                        "3. Details", class_name="font-semibold mb-2 text-neutral-700"
                    ),
                    rx.el.p(
                        "Add interior walls, doors, and windows.",
                        class_name="text-sm text-neutral-600",
                    ),
                    class_name="p-4 bg-neutral-50 rounded-lg border",
                ),
                None,
            ),
            rx.cond(MainState.current_step == 4, export_panel(), None),
            class_name="flex-1",
        ),
        rx.el.div(
            sidebar_button(
                "Reset",
                MainState.reset_canvas,
                "trash-2",
                class_name="!bg-gray-600 hover:!bg-gray-700",
            ),
            rx.el.div(
                rx.el.button(
                    "Back",
                    on_click=MainState.prev_step,
                    disabled=MainState.current_step == 1,
                    class_name="w-full text-center px-4 py-2 text-sm font-semibold text-neutral-700 bg-neutral-200 rounded-lg hover:bg-neutral-300 transition-colors disabled:opacity-50",
                ),
                rx.el.button(
                    "Next",
                    on_click=MainState.next_step,
                    disabled=~MainState.can_proceed,
                    class_name="w-full text-center px-4 py-2 text-sm font-semibold text-white bg-green-600 rounded-lg hover:bg-green-700 transition-colors disabled:bg-neutral-400",
                ),
                class_name="grid grid-cols-2 gap-2 mt-4",
            ),
            class_name="border-t pt-4 mt-4",
        ),
        class_name="w-64 bg-white p-4 flex flex-col border-r shadow-md",
        aria_label="Controls Sidebar",
    )