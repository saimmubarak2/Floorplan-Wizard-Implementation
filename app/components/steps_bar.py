import reflex as rx
from app.states.main_state import MainState


def step_item(step: dict, current_step: int, index: int) -> rx.Component:
    is_active = step["id"].to(int) == current_step
    is_done = step["id"].to(int) < current_step
    return rx.el.div(
        rx.el.div(
            rx.cond(
                is_done,
                rx.icon("check", class_name="size-5 text-white"),
                rx.el.span(
                    step["id"],
                    class_name=rx.cond(
                        is_active, "text-orange-600", "text-neutral-500"
                    ),
                ),
            ),
            class_name=rx.cond(
                is_done,
                "w-8 h-8 rounded-full bg-green-500 flex items-center justify-center font-bold",
                rx.cond(
                    is_active,
                    "w-8 h-8 rounded-full bg-orange-100 border-2 border-orange-500 flex items-center justify-center font-bold",
                    "w-8 h-8 rounded-full bg-neutral-200 flex items-center justify-center font-bold",
                ),
            ),
        ),
        rx.el.div(
            rx.el.h3(
                step["title"],
                class_name=rx.cond(
                    is_active,
                    "font-bold text-neutral-800",
                    "font-medium text-neutral-600",
                ),
            ),
            rx.el.p(step["prompt"], class_name="text-xs text-neutral-500"),
            class_name="ml-3",
        ),
        on_click=lambda: MainState.go_to_step(step["id"]),
        class_name="flex items-center cursor-pointer p-2 rounded-lg hover:bg-neutral-100 transition-colors",
    )


def steps_bar() -> rx.Component:
    return rx.el.header(
        rx.el.div(
            rx.icon("ruler", class_name="size-8 text-orange-600 mr-4"),
            rx.el.h1(
                "Floorplan Wizard", class_name="text-2xl font-bold text-neutral-800"
            ),
            class_name="flex items-center",
        ),
        rx.el.div(
            rx.foreach(
                MainState.wizard_steps,
                lambda step, index: rx.fragment(
                    step_item(step, MainState.current_step, index),
                    rx.cond(
                        index < MainState.wizard_steps.length() - 1,
                        rx.el.div(class_name="flex-1 h-px bg-neutral-300 mx-4"),
                        None,
                    ),
                ),
            ),
            class_name="flex items-center justify-center",
        ),
        class_name="flex items-center justify-between p-4 bg-white border-b border-neutral-200 shadow-sm",
    )