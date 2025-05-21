import reflex as rx
from typing import List, Optional, Dict # Set is not used directly for rx.Var
from beanie.odm.fields import PydanticObjectId # type: ignore

from .auth import AuthState
from ..models.users import User, UserGroup

class AdminUsersState(AuthState):
    """管理系統管理者操作使用者角色的狀態與邏輯"""

    users_list: rx.Var[List[User]] = rx.Var([])
    search_term: rx.Var[str] = ""
    
    # 用於角色修改 Modal
    editing_user_id: rx.Var[Optional[str]] = None
    editing_user_display_name: rx.Var[str] = "" # 用於在 Modal 標題顯示
    roles_for_edit_modal: rx.Var[List[str]] = rx.Var([]) # 綁定 CheckboxGroup (存儲 UserGroup.value)
    show_edit_user_modal: rx.Var[bool] = False

    async def on_page_load(self):
        """頁面載入時執行的操作"""
        if not self.is_hydrated or not self.token_is_valid:
            return
        # 權限檢查，假設 UserGroup.ADMIN 是系統管理員角色
        if not self.is_member_of_any([UserGroup.ADMIN]):
            return rx.redirect(self.DEFAULT_UNAUTHORIZED_REDIRECT_PATH) # type: ignore
        await self.load_all_users()

    async def load_all_users(self):
        """載入或篩選使用者列表"""
        query_conditions = {}
        if self.search_term:
            search_regex = {"$regex": self.search_term, "$options": "i"}
            query_conditions["$or"] = [
                {"fullname": search_regex},
                {"email": search_regex},
                {"student_id": search_regex},
            ]
        
        self.users_list = await User.find(query_conditions).sort("-created_at").to_list()

    async def handle_search_term_change(self, term: str):
        self.search_term = term
        await self.load_all_users()

    def start_edit_user_roles(self, user: User):
        """開啟編輯使用者角色的 Modal"""
        self.editing_user_id = str(user.id)
        self.editing_user_display_name = user.fullname or user.email
        # get_user_role_values 輔助函式返回 List[str]
        self.roles_for_edit_modal = self.get_user_role_values(user)
        self.show_edit_user_modal = True
    
    def close_edit_user_modal(self):
        """關閉編輯使用者角色的 Modal"""
        self.show_edit_user_modal = False
        self.editing_user_id = None
        self.editing_user_display_name = ""
        self.roles_for_edit_modal = []

    async def handle_save_user_roles(self):
        """儲存使用者角色的變更"""
        if not self.editing_user_id:
            return rx.toast.error("未選擇要編輯的使用者。") # type: ignore

        try:
            user_to_update = await User.get(PydanticObjectId(self.editing_user_id))
            if not user_to_update:
                return rx.toast.error("找不到指定的使用者。") # type: ignore

            # 將 self.roles_for_edit_modal (List[str]) 轉換為 List[UserGroup]
            new_groups_enum: List[UserGroup] = []
            for role_value_str in self.roles_for_edit_modal:
                try:
                    group_enum = UserGroup(role_value_str) # 從 value 轉換回 Enum 成員
                    new_groups_enum.append(group_enum)
                except ValueError:
                    # 理論上不應發生，因為 CheckboxGroup 的 value 來自 UserGroup.value
                    return rx.toast.error(f"無效的角色值：{role_value_str}") # type: ignore
            
            # 確保 AUTHENTICATED_USER 始終存在
            if UserGroup.AUTHENTICATED_USER not in new_groups_enum:
                new_groups_enum.append(UserGroup.AUTHENTICATED_USER)
            
            # 如果使用者是系統管理員 (ADMIN)，則不允許移除 ADMIN 角色，除非是其他系統管理員操作
            # 這裡簡化：不允許自己移除自己的 ADMIN 角色
            if UserGroup.ADMIN in user_to_update.groups and \
               user_to_update.email == self.tokeninfo.get("email") and \
               UserGroup.ADMIN not in new_groups_enum:
                return rx.toast.error("系統管理員無法移除自己的管理員權限。") # type: ignore


            user_to_update.groups = new_groups_enum
            await user_to_update.save()
            
            await self.load_all_users() # 更新列表顯示
            self.close_edit_user_modal()
            return rx.toast.success(f"使用者 {user_to_update.email} 的角色已更新。") # type: ignore
        except Exception as e:
            return rx.toast.error(f"更新角色失敗：{str(e)}") # type: ignore

    # 輔助函式，用於在 UI 中綁定 CheckboxGroup
    def get_user_role_values(self, user: User) -> List[str]:
        """獲取使用者當前角色的字串值列表 (排除 AUTHENTICATED_USER，因為它總是存在)"""
        return [g.value for g in user.groups if g != UserGroup.AUTHENTICATED_USER]

    def get_all_manageable_roles_for_checkbox(self) -> List[Dict[str, str]]:
        """獲取所有可管理的角色選項 (排除 AUTHENTICATED_USER)，用於 CheckboxGroup"""
        # 排除 AUTHENTICATED_USER 因為它總是隱含存在
        # 系統管理員 (ADMIN) 角色通常也不能隨意賦予或移除，但此處允許UI選擇
        return [
            {"label": ug.value, "value": ug.value} 
            for ug in UserGroup 
            if ug != UserGroup.AUTHENTICATED_USER
        ]
