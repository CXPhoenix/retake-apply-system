import reflex as rx
from reflex_google_auth import require_google_login
from ..states.auth import AuthState, authorize_by_groups
from ..models.users import UserGroup, User
from ..components import navbar

# TODO: 建立 AdminUsersState，繼承 AuthState。
#       應包含：
#       - users_list: rx.Var[list[User]]
#       - search_term: rx.Var[str]
#       - selected_user_for_role_update: rx.Var[Optional[User]]
#       - new_roles_for_selected_user: rx.Var[list[UserGroup]]
#       - async def load_users(self):
#       - async def handle_update_user_roles(self, user_id: str, new_roles_values: list[str]):
#       - (可選) async def handle_remove_user_role(self, user_id: str, role_to_remove: str):

# class AdminUsersState(AuthState):
#     users_list: rx.Var[list[User]] = []
#     search_term: rx.Var[str] = ""
#     # ... 其他 rx.Var 和事件處理器 ...
#
#     async def on_load(self):
#         # await self.load_all_users()
#         print("TODO: AdminUsersState.on_load 載入使用者列表")
#
#     async def load_all_users(self):
#         # query = {}
#         # if self.search_term:
#         #     # 實現搜尋邏輯，可搜尋 fullname, email, student_id
#         #     query["$or"] = [
#         #         {"fullname": {"$regex": self.search_term, "$options": "i"}},
#         #         {"email": {"$regex": self.search_term, "$options": "i"}},
#         #         {"student_id": {"$regex": self.search_term, "$options": "i"}},
#         #     ]
#         # self.users_list = await User.find(query).to_list()
#         print(f"TODO: AdminUsersState.load_all_users 載入使用者 (搜尋: {self.search_term})")
#
#     async def handle_role_update(self, user_id_str: str, selected_roles_str: list[str]):
#         # user_to_update = await User.get(PydanticObjectId(user_id_str))
#         # if user_to_update:
#         #     # 將選擇的角色字串轉換為 UserGroup Enum
#         #     # new_user_groups = [UserGroup(role_val) for role_val in selected_roles_str if role_val in UserGroup._value2member_map_]
#         #     # # 確保 AUTHENTICATED_USER 角色始終存在 (如果適用)
#         #     # if UserGroup.AUTHENTICATED_USER not in new_user_groups:
#         #     #    new_user_groups.append(UserGroup.AUTHENTICATED_USER)
#         #     # user_to_update.groups = new_user_groups
#         #     # await user_to_update.save()
#         #     # await self.load_all_users() # 重新載入列表
#         #     # return rx.toast.success(f"使用者 {user_to_update.email} 的角色已更新。")
#         # return rx.toast.error("找不到使用者。")
#         print(f"TODO: AdminUsersState.handle_role_update 更新使用者 {user_id_str} 角色為 {selected_roles_str}")

@rx.page(route="/admin-users", title="使用者管理") # 路由根據 dashboard.py 中的連結調整
@require_google_login
# @authorize_by_groups(required_groups=[UserGroup.SYSTEM_ADMIN]) # 改由 State 控制權限
def admin_users() -> rx.Component:
    """
    系統管理者頁面，用於管理使用者角色與權限。
    TODO: 此頁面應綁定到 AdminUsersState。
    """
    # TODO: 角色選擇應使用多選組件 (e.g., rx.checkbox_group or custom multi-select)
    #       或者，提供新增/移除單一角色的按鈕。
    #       目前 rx.select 是單選，不適合多角色指派。

    return rx.vstack(
        navbar(),
        rx.heading("使用者角色管理", size="lg", margin_bottom="1em"),
        rx.text("（TODO: 此頁面應綁定到 AdminUsersState）"),
        rx.hstack(
            # rx.input(placeholder="搜尋使用者...", value=AdminUsersState.search_term, on_change=AdminUsersState.set_search_term),
            # rx.button("搜尋", on_click=AdminUsersState.load_all_users),
            rx.input(placeholder="搜尋使用者... (TODO)"),
            rx.button("搜尋 (TODO)"),
            spacing="1em",
            margin_bottom="1em"
        ),
        # rx.foreach(
        #     AdminUsersState.users_list,
        #     lambda user: rx.box(
        #         rx.text(f"姓名：{user.fullname or '未知'} (Email: {user.email})"),
        #         rx.text(f"學號：{user.student_id or 'N/A'}"),
        #         rx.text(f"目前角色：{', '.join(sorted([group.value for group in user.groups])) or '無'}"),
        #         # TODO: 使用 rx.checkbox_group 或類似組件來修改 user.groups
        #         # 例如，為每個 UserGroup Enum 成員創建一個 checkbox
        #         # rx.checkbox_group(
        #         #     items=[(ug.value, ug.name) for ug in UserGroup if ug != UserGroup.AUTHENTICATED_USER], # 不讓手動移除 AUTHENTICATED_USER
        #         #     value=[ug.value for ug in user.groups if ug != UserGroup.AUTHENTICATED_USER],
        #         #     on_change=lambda new_selected_values: AdminUsersState.handle_role_update(str(user.id), new_selected_values)
        #         # ),
        #         rx.text("（TODO: 角色修改 UI，建議使用 Checkbox Group）"),
        #         border="1px solid #ddd", padding="1em", margin="0.5em 0", border_radius="5px",
        #     )
        # ),
        rx.text("（TODO: 使用者列表顯示區，應使用 rx.data_table 或 rx.foreach）"),
        align_items="center",
        padding="2em",
        # on_mount=AdminUsersState.on_load
    )

# 以下 TODO 函式應移至 AdminUsersState 中
# TODO: filter_users(value) -> AdminUsersState.set_search_term(value)
# TODO: update_user_role(user_id, value) -> AdminUsersState.handle_role_update(user_id, [value]) (若為單選) 或處理多選
# TODO: remove_user_role(user_id) -> AdminUsersState.handle_role_update(user_id, [UserGroup.AUTHENTICATED_USER.value]) (僅保留基礎角色)
