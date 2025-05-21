"""導覽列 (Navbar) 元件。

此模組定義了應用程式的通用導覽列。
導覽列的內容會根據目前登入使用者的角色動態調整。
"""
import reflex as rx
from typing import List
from retake_apply.states.auth import AuthState # 假設 AuthState 在 retake_apply.states.auth 中
from retake_apply.models.users import UserGroup # 假設 UserGroup 在 retake_apply.models.users 中

def nav_link(text: str, href: str) -> rx.Component:
    """一個輔助函式，用於創建導覽列中的連結。"""
    return rx.link(
        rx.text(text, size="4"), # Radix Theme Text size "4" is medium-large
        href=href,
        color_scheme="gray", # Radix Theme color scheme
        padding_x="1em",
        padding_y="0.5em",
        _hover={"background_color": "var(--accent-3)"} # Radix Theme accent color
    )

def navbar() -> rx.Component:
    """應用程式的導覽列元件。

    根據登入使用者的角色顯示不同的導覽選項。
    """
    return rx.box(
        rx.hstack(
            rx.link(
                rx.hstack(
                    rx.image(src="/retake_apply_sys_icon_rmbg.png", height="2.5em", width="auto", alt="App Logo"),
                    rx.heading("校園重補修課程登記系統", size="6", margin_left="0.5em"), # Radix Theme Heading size "6" is large
                    align="center",
                    spacing="3" # Radix Theme spacing
                ),
                href="/", # 連結到首頁
                style={"text_decoration": "none", "color": "inherit"}
            ),
            rx.spacer(), # 將左側標題與右側連結隔開

            # 通用連結 (所有已登入使用者可見)
            rx.cond(
                AuthState.is_hydrated & AuthState.token_is_valid, # 確保已水合且已登入
                rx.hstack(
                    nav_link("儀表板", "/dashboard"),
                    # 學生特定連結
                    rx.cond(
                        AuthState.current_user_groups.contains(UserGroup.STUDENT), # type: ignore
                        nav_link("課程查詢與選課", "/course-selection")
                    ),
                    # 課程管理者特定連結
                    rx.cond(
                        AuthState.current_user_groups.contains(UserGroup.COURSE_MANAGER), # type: ignore
                        rx.menu.root(
                            rx.menu.trigger(
                                rx.button(
                                    "課程管理", 
                                    variant="soft", # Radix Theme button variant
                                    color_scheme="gray",
                                    size="3" # Radix Theme button size
                                )
                            ),
                            rx.menu.content(
                                rx.menu.item("學年度與登記時間設定", on_click=rx.redirect("/manager/academic-year")),
                                rx.menu.item("重補修課程管理", on_click=rx.redirect("/manager/courses")),
                                rx.menu.item("學生應重補修名單管理", on_click=rx.redirect("/manager/students")),
                                rx.menu.item("學生報名資料管理", on_click=rx.redirect("/manager/enrollments")),
                                # rx.menu.separator(),
                                # rx.menu.item("TODO: 繳費相關管理"),
                                size="2" # Radix Theme menu content size
                            ),
                        )
                    ),
                    # 系統管理者特定連結
                    rx.cond(
                        AuthState.current_user_groups.contains(UserGroup.SYSTEM_ADMIN), # type: ignore
                        rx.menu.root(
                            rx.menu.trigger(
                                rx.button(
                                    "系統管理", 
                                    variant="soft", 
                                    color_scheme="gray",
                                    size="3"
                                )
                            ),
                            rx.menu.content(
                                rx.menu.item("使用者角色管理", on_click=rx.redirect("/admin/users")),
                                rx.menu.item("系統日誌查閱", on_click=rx.redirect("/admin/logs")),
                                size="2"
                            ),
                        )
                    ),
                    rx.button(
                        "登出", 
                        on_click=AuthState.logout, # type: ignore
                        variant="outline", # Radix Theme button variant
                        color_scheme="red",
                        size="3"
                    ),
                    spacing="4", # Radix Theme spacing
                    align="center"
                ),
                # 未登入時顯示登入按鈕 (通常由 require_google_login 處理，但可作為備用)
                # rx.button("使用 Google 登入", on_click=AuthState.login_with_google)
            ),
            align="center",
            justify="between", # 左右對齊
            spacing="6" # Radix Theme spacing
        ),
        position="fixed", # 固定在頂部
        top="0px",
        left="0px",
        right="0px",
        padding="1em",
        height="4.5em", # 導覽列高度
        background_color="var(--gray-2)", # Radix Theme gray color
        border_bottom="1px solid var(--gray-a6)", # Radix Theme gray accent color
        z_index="1000", # 確保在最上層
        width="100%"
    )
