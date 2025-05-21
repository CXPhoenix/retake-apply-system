"""應用程式索引頁面（登入頁面）模組。

此模組定義了應用程式的根路徑 (`/`) 對應的頁面。
主要功能是顯示一個登入表單，引導使用者透過校園 Google 帳號登入系統。
"""
import reflex as rx
from reflex_google_auth import google_login, google_oauth_provider # 從 reflex-google-auth 匯入登入元件

def _login_form() -> rx.Component:
    """渲染包含 Google 登入按鈕的登入表單元件。

    此為內部輔助函式，用於建構登入頁面的核心表單區域。

    Returns:
        rx.Component: 一個包含圖片、標題及 Google 登入按鈕的 Reflex 卡片元件。
    """
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

@rx.page(route="/", title="登入系統") # 定義為根路徑頁面
def index() -> rx.Component:
    """應用程式的索引頁面，通常作為登入頁面。

    此頁面會顯示一個置中的登入表單，要求使用者透過 Google 帳號登入。

    Returns:
        rx.Component: 組建完成的索引/登入頁面。
    """
    return rx.flex(
        _login_form(),
        class_name="h-[100dvh] justify-center items-center" # 使用 Tailwind CSS 使表單垂直和水平居中
    )
