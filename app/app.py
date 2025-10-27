import reflex as rx
from app.states.main_state import MainState
from app.components.sidebar import sidebar
from app.components.canvas import canvas_area
from app.components.properties_panel import properties_panel
from app.components.steps_bar import steps_bar


def index() -> rx.Component:
    """The main view for the floorplan wizard."""
    return rx.el.main(
        rx.el.div(
            steps_bar(),
            rx.el.div(
                sidebar(),
                canvas_area(),
                properties_panel(),
                class_name="flex flex-1 min-h-0",
            ),
            class_name="flex flex-col h-screen w-screen bg-neutral-100",
        ),
        class_name="font-['Poppins']",
    )


app = rx.App(
    theme=rx.theme(appearance="light", accent_color="orange", radius="medium"),
    head_components=[
        rx.el.link(rel="preconnect", href="https://fonts.googleapis.com"),
        rx.el.link(rel="preconnect", href="https://fonts.gstatic.com", cross_origin=""),
        rx.el.link(
            href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap",
            rel="stylesheet",
        ),
    ],
)
app.add_page(index)