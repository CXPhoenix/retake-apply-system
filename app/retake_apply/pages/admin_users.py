"""使用者管理頁面模組。

此模組定義了供系統管理者管理使用者角色與權限的 Reflex 頁面。
頁面提供搜尋使用者、檢視使用者列表及其目前角色，
並允許系統管理者編輯特定使用者的角色指派。
"""
import reflex as rx
from reflex_google_auth import require_google_login
from ..states.auth import require_group # 從 auth.py 匯入權限群組檢查裝飾器
from ..models.users import UserGroup # UserGroup Enum 用於角色定義與檢查
from ..components import navbar # 引入共用的導覽列元件
from ..states.admin_users_state import AdminUsersState # 匯入此頁面專用的狀態管理類

def render_roles_badges(user_groups: rx.Var[list[UserGroup]]) -> rx.Component:
    """輔助函式，用於將使用者的角色群組列表渲染為一組徽章 (badges)。

    Args:
        user_groups (rx.Var[list[UserGroup]]): 一個包含使用者角色群組 (UserGroup Enum)
                                               列表的 Reflex Var。

    Returns:
        rx.Component: 一個包含多個 `rx.badge` 的 `rx.hstack` 元件，
                      每個徽章代表一個角色。
    """
    return rx.hstack(
        rx.foreach(
            user_groups,
            lambda group: rx.badge(group.value, color_scheme="blue", margin_right="0.25em")
        ),
        spacing="1" # badge 之間的間距
    )

@rx.page(
    route="/admin/users", # 建議使用 admin/ 前綴
    title="使用者管理",
    on_load=AdminUsersState.on_page_load # 頁面載入時觸發的事件
)
@require_google_login # 要求使用者必須先登入 Google 帳號
@require_group(allowed_groups=[UserGroup.SYSTEM_ADMIN]) # 要求使用者必須屬於 SYSTEM_ADMIN 群組
def admin_users_page() -> rx.Component:
    """系統管理者管理使用者角色與權限的頁面元件。

    此頁面允許管理者搜尋使用者、檢視使用者列表及其目前角色，
    並透過彈出視窗編輯個別使用者的角色指派。

    Returns:
        rx.Component: 組建完成的使用者管理頁面。
    """
    return rx.vstack(
        navbar(), # 頁面頂部導覽列
        rx.box(
            rx.heading("使用者角色管理", size="7", margin_bottom="1em"),
            rx.hstack(
                rx.input(
                    placeholder="依姓名、Email或學號搜尋...",
                    value=AdminUsersState.search_term,
                    on_change=AdminUsersState.set_search_term, # type: ignore
                    on_blur=AdminUsersState.load_all_users, # 失焦時觸發搜尋
                    width="300px"
                ),
                rx.button("搜尋", on_click=AdminUsersState.load_all_users, size="2"), # type: ignore
                spacing="3",
                margin_bottom="1.5em"
            ),

            rx.cond(
                AdminUsersState.users_list.length() > 0,
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("姓名/Email"),
                            rx.table.column_header_cell("學號"),
                            rx.table.column_header_cell("目前角色"),
                            rx.table.column_header_cell("操作"),
                        )
                    ),
                    rx.table.body(
                        rx.foreach(
                            AdminUsersState.users_list,
                            lambda user: rx.table.row(
                                rx.table.cell(user.fullname or user.email),
                                rx.table.cell(user.student_id or "N/A"),
                                rx.table.cell(render_roles_badges(user.groups)), # type: ignore
                                rx.table.cell(
                                    rx.button(
                                        "編輯角色", 
                                        on_click=lambda: AdminUsersState.start_edit_user_roles(user), # type: ignore
                                        size="1"
                                    )
                                ),
                            )
                        )
                    ),
                    variant="surface",
                    width="100%",
                ),
                rx.text("找不到符合條件的使用者，或尚無使用者。", color_scheme="gray", margin_top="1em")
            ),
            
            # 角色編輯 Modal
            rx.dialog.root(
                rx.dialog.trigger(
                    # Modal 由 AdminUsersState.show_edit_user_modal 控制開啟，無需額外 trigger
                    # rx.button("Open Dialog") 
                    rx.fragment("") # 空片段，因為 trigger 由 state 控制
                ),
                rx.dialog.content(
                    rx.dialog.title(f"編輯使用者角色 - {AdminUsersState.editing_user_display_name}"),
                    rx.dialog.description("請選擇使用者的新角色組合。系統管理員角色請謹慎操作。"),
                    rx.scroll_area( # 如果角色過多，可以滾動
                        rx.checkbox_group.root(
                            rx.flex(
                                rx.foreach(
                                    AdminUsersState.get_all_manageable_roles_for_checkbox(),
                                    lambda role_option: rx.checkbox_group.item(
                                        role_option["value"], # checkbox value
                                        rx.text(role_option["label"]), # checkbox label
                                        padding_y="0.25em"
                                    )
                                ),
                                direction="column",
                                spacing="2",
                            ),
                            value=AdminUsersState.roles_for_edit_modal,
                            on_change=AdminUsersState.set_roles_for_edit_modal, # type: ignore
                            margin_top="1em",
                            margin_bottom="1em",
                        ),
                        type="auto", scrollbars="vertical", style={"height": "200px"}
                    ),
                    rx.flex(
                        rx.dialog.close(
                            rx.button(
                                "取消",
                                on_click=AdminUsersState.close_edit_user_modal, # type: ignore
                                variant="soft",
                                color_scheme="gray",
                            )
                        ),
                        rx.button("儲存變更", on_click=AdminUsersState.handle_save_user_roles), # type: ignore
                        spacing="3",
                        margin_top="1em",
                        justify="end",
                    ),
                ),
                open=AdminUsersState.show_edit_user_modal, # 綁定 Modal 開啟狀態
                on_open_change=AdminUsersState.set_show_edit_user_modal, # type: ignore # 允許點擊外部關閉
            ),
            width="100%",
            padding_x="2em",
            padding_y="1em",
            max_width="container.lg",
            margin="0 auto",
        ),
        align_items="center",
        width="100%",
    )
