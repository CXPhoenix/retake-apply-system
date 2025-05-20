import reflex as rx
from typing import List, Optional, Set, Dict # 匯入 Dict
from beanie.odm.fields import PydanticObjectId

from .auth import AuthState
from ..models.users import User, UserGroup

class AdminUsersState(AuthState):
    """管理系統管理者操作使用者角色的狀態與邏輯"""

    users_list: rx.Var[List[User]] = rx.Var([])
    search_term: rx.Var[str] = ""
    
    # 用於角色修改的 rx.Var
    # 當點擊某個使用者的角色進行修改時，可以將該使用者的 ID 和當前角色填充到這裡
    # selected_user_id_for_role_edit: rx.Var[Optional[str]] = None
    # roles_for_edit: rx.Var[Set[UserGroup]] = rx.Var(set()) # 使用 Set 存儲角色以方便操作

    async def on_page_load(self):
        """頁面載入時執行的操作"""
        if not self.is_hydrated or not self.token_is_valid:
            return
        if UserGroup.SYSTEM_ADMIN not in self.current_user_groups:
            # return rx.redirect("/unauthorized")
            pass
        await self.load_all_users()

    async def load_all_users(self):
        """載入或篩選使用者列表"""
        query_conditions = {}
        if self.search_term:
            # 實現多欄位模糊搜尋
            search_regex = {"$regex": self.search_term, "$options": "i"}
            query_conditions["$or"] = [
                {"fullname": search_regex},
                {"email": search_regex},
                {"student_id": search_regex},
            ]
        
        # self.users_list = await User.find(query_conditions).to_list()
        print(f"TODO: AdminUsersState.load_all_users 尚未從資料庫載入，搜尋: {self.search_term}")
        # 模擬資料
        # self.users_list = [
        #     User(id=PydanticObjectId(), fullname="管理員A", email="admin@example.com", groups=[UserGroup.SYSTEM_ADMIN, UserGroup.AUTHENTICATED_USER]),
        #     User(id=PydanticObjectId(), fullname="課程管理員B", email="manager@example.com", groups=[UserGroup.COURSE_MANAGER, UserGroup.AUTHENTICATED_USER]),
        #     User(id=PydanticObjectId(), fullname="學生C", email="student@example.com", student_id="S001", groups=[UserGroup.STUDENT, UserGroup.AUTHENTICATED_USER]),
        # ]

    async def handle_search_term_change(self, term: str):
        self.search_term = term
        # await self.load_all_users() # 可選擇即時更新或按鈕觸發

    async def update_user_roles(self, user_id_str: str, new_roles_values: List[str]):
        """
        更新指定使用者的角色列表。
        new_roles_values 是角色值的列表，例如 ["學生", "課程管理者"]。
        """
        # user_to_update = await User.get(PydanticObjectId(user_id_str))
        # if not user_to_update:
        #     return rx.toast.error("找不到指定的使用者。")

        # valid_new_groups = set()
        # for role_val in new_roles_values:
        #     try:
        #         # 將字串值轉換為 UserGroup Enum 成員
        #         group_enum = UserGroup(role_val)
        #         valid_new_groups.add(group_enum)
        #     except ValueError:
        #         # return rx.toast.error(f"無效的角色值：{role_val}")
        #         print(f"無效的角色值：{role_val}")
        #         return
        
        # # 確保 AUTHENTICATED_USER 始終存在 (如果這是系統設計)
        # valid_new_groups.add(UserGroup.AUTHENTICATED_USER)
        
        # user_to_update.groups = list(valid_new_groups)
        # await user_to_update.save()
        # await self.load_all_users() # 更新列表顯示
        # return rx.toast.success(f"使用者 {user_to_update.email} 的角色已更新。")
        print(f"TODO: update_user_roles 尚未實作。使用者ID: {user_id_str}, 新角色: {new_roles_values}")
        await self.load_all_users() # 模擬重新載入

    # 輔助函式，用於在 UI 中綁定 CheckboxGroup
    def get_user_role_values(self, user: User) -> List[str]:
        """獲取使用者當前角色的字串值列表 (排除 AUTHENTICATED_USER)"""
        return [g.value for g in user.groups if g != UserGroup.AUTHENTICATED_USER]

    def get_all_manageable_roles(self) -> List[Dict[str, str]]:
        """獲取所有可管理的角色選項 (排除 AUTHENTICATED_USER)"""
        return [{"label": ug.value, "value": ug.value} for ug in UserGroup if ug != UserGroup.AUTHENTICATED_USER]
