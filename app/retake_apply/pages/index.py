import reflex as rx
from reflex_google_auth import google_login, google_oauth_provider

def _login_form() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.flex(
                rx.image(
                    src="/retake_apply_sys_icon_rmbg.png",
                    class_name="w-[25%] mx-auto",
                ),
                rx.heading(
                    "使用校園 Google 帳號登入系統",
                    as_="h2",
                    class_name="text-center text-2xl",
                ),
                class_name="justify-center flex-col gap-4",
            ),
            rx.box(
                google_oauth_provider(
                    google_login(),
                ),
                class_name="mx-auto",
            ),
            class_name="space-y-6",
        ),
        class_name="max-w-[30rem] w-full justify-center items-center",
    )

def index() -> rx.Component:
    return rx.flex(
        _login_form(),
        class_name="h-[100dvh] justify-center items-center"
    )