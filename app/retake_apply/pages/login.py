import reflex as rx
from reflex_google_auth import google_login, google_oauth_provider

from ..states.auth import AuthState


class LoginState(AuthState):
    """Login State: 處理登入狀態（使用 Google Oauth）"""

    # TODO: State design
    ...


def login_page() -> rx.Component:
    """Login page: 使用 Google 帳號登入頁面"""
    # TODO: Use Tailwindcss to refactor
    return rx.el.div(
        rx.card(
            rx.vstack(
                rx.center(
                    rx.image(
                        src="/retake_apply_sys_icon_rmbg.png",
                        width="25%",
                        height="auto",
                    ),
                    rx.heading(
                        "使用你的 Google 帳戶登入",
                        size="6",
                        as_="h2",
                        text_align="center",
                        width="100%",
                    ),
                    google_oauth_provider(
                        google_login(),
                    ),
                    direction="column",
                    spacing="5",
                    width="100%",
                ),
                spacing="6",
                width="100%",
            ),
            size="4",
            max_width="40rem",
            width="100%",
        ),
        class_name=["w-[100dvw]", "h-[100dvh]", "flex", "justify-center", "items-center"],
    )
