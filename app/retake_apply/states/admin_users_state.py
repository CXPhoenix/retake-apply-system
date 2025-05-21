"""使用者管理頁面的狀態管理模組。

此模組定義了 `AdminUsersState` 類別，繼承自 `AuthState`，
負責處理系統管理者管理使用者角色頁面的所有後端邏輯，包括：
- 載入和搜尋使用者列表。
- 控制編輯使用者角色的彈出視窗。
- 處理使用者角色的儲存與更新。
"""
import reflex as rx
from typing import List, Optional, Dict, Any # Set is not used directly for rx.Var, Any for query_conditions
from beanie.odm.fields import PydanticObjectId # type: ignore # 用於將字串 ID 轉換為 ObjectId

from .auth import AuthState # 基礎身份驗證狀態
from ..models.users import User, UserGroup # User 模型及 UserGroup Enum

class AdminUsersState(AuthState):
    """管理系統管理者操作使用者角色的狀態與相關邏輯。

    Attributes:
        users_list (rx.Var[List[User]]): 從資料庫載入的使用者列表。
        search_term (rx.Var[str]): 用於搜尋使用者列表的關鍵字。
        editing_user_id (rx.Var[Optional[str]]): 當前正在編輯角色的使用者 ID (字串形式)。
        editing_user_display_name (rx.Var[str]): 當前正在編輯角色的使用者顯示名稱 (用於 Modal 標題)。
        roles_for_edit_modal (rx.Var[List[str]]): 綁定到角色編輯 Modal 中 CheckboxGroup 的值列表，
                                                 存儲所選角色的 `UserGroup.value`。
        show_edit_user_modal (rx.Var[bool]): 控制是否顯示編輯使用者角色的彈出視窗。
    """

    users_list: List[User] = []
    search_term: str = ""
    
    # --- 角色修改 Modal 相關狀態 ---
    editing_user_id: Optional[str] = None
    editing_user_display_name: str = "" # 用於在 Modal 標題顯示
    roles_for_edit_modal: List[str] = [] # 綁定 CheckboxGroup (存儲 UserGroup.value)
    show_edit_user_modal: bool = False

    async def on_page_load(self):
        """頁面載入時執行的非同步操作。

        檢查使用者登入狀態和權限 (必須是系統管理員)，若符合則載入所有使用者列表。
        若未登入或權限不足，則導向至未授權頁面。
        """
        if not self.is_hydrated or not self.token_is_valid:
            return # 等待客戶端水合或 token 驗證完成
        # 權限檢查，確保是系統管理員 (UserGroup.SYSTEM_ADMIN)
        if not self.is_member_of_any([UserGroup.SYSTEM_ADMIN]):
            # 導向至預設的未授權頁面路徑 (應在 AuthState 中定義)
            return rx.redirect(getattr(self, "DEFAULT_UNAUTHORIZED_REDIRECT_PATH", "/")) # type: ignore
        await self.load_all_users()

    async def load_all_users(self):
        """根據 `search_term` 從資料庫非同步載入或篩選使用者列表。

        如果 `search_term` 為空，則載入所有使用者。
        否則，會根據姓名、Email 或學號進行模糊查詢 (不區分大小寫)。
        查詢結果按創建時間降序排列，並更新 `self.users_list`。
        """
        query_conditions: Dict[str, Any] = {}
        if self.search_term:
            search_regex = {"$regex": self.search_term, "$options": "i"}
            query_conditions["$or"] = [
                {"fullname": search_regex},
                {"email": search_regex},
                {"student_id": search_regex},
            ]
        
        self.users_list = await User.find(query_conditions).sort("-created_at").to_list()

    async def handle_search_term_change(self, term: str):
        """處理搜尋關鍵字變更的事件。

        更新 `search_term` 狀態變數，並觸發重新載入使用者列表。

        Args:
            term (str): 新的搜尋關鍵字。
        """
        self.search_term = term
        await self.load_all_users()

    def start_edit_user_roles(self, user: User):
        """準備並開啟編輯指定使用者角色的彈出視窗。

        Args:
            user (User): 要編輯其角色的使用者物件。
        """
        self.editing_user_id = str(user.id)
        self.editing_user_display_name = user.fullname or user.email
        # get_user_role_values 輔助函式返回 List[str]，用於 CheckboxGroup
        self.roles_for_edit_modal = self.get_user_role_values(user)
        self.show_edit_user_modal = True
    
    def close_edit_user_modal(self):
        """關閉編輯使用者角色的彈出視窗，並重設相關狀態。"""
        self.show_edit_user_modal = False
        self.editing_user_id = None
        self.editing_user_display_name = ""
        self.roles_for_edit_modal = []

    async def handle_save_user_roles(self):
        """處理儲存使用者角色變更的邏輯。

        從 Modal 中獲取選定的角色，轉換為 `UserGroup` Enum 列表，
        更新使用者的 `groups` 欄位，並儲存至資料庫。
        包含一些業務邏輯檢查，例如確保 `AUTHENTICATED_USER` 角色始終存在，
        以及防止系統管理員移除自身的管理員權限。
        """
        if not self.editing_user_id:
            return rx.toast.error("錯誤：未指定要編輯的使用者。") # type: ignore

        try:
            user_to_update = await User.get(PydanticObjectId(self.editing_user_id))
            if not user_to_update:
                return rx.toast.error("錯誤：找不到指定的使用者。") # type: ignore

            # 將 self.roles_for_edit_modal (List[str] of role values) 轉換為 List[UserGroup]
            new_groups_enum: List[UserGroup] = []
            for role_value_str in self.roles_for_edit_modal:
                try:
                    group_enum = UserGroup(role_value_str) # 從角色字串值轉換回 UserGroup Enum 成員
                    new_groups_enum.append(group_enum)
                except ValueError:
                    # 理論上不應發生，因為 CheckboxGroup 的 value 來自 UserGroup.value
                    return rx.toast.error(f"錯誤：無效的角色值 '{role_value_str}'。") # type: ignore
            
            # 確保 AUTHENTICATED_USER 角色始終存在於使用者的群組中
            if UserGroup.AUTHENTICATED_USER not in new_groups_enum:
                new_groups_enum.append(UserGroup.AUTHENTICATED_USER)
            
            # 安全性檢查：防止系統管理員移除自身的 SYSTEM_ADMIN 角色
            # (假設 UserGroup.SYSTEM_ADMIN 是枚舉中的管理員角色)
            if UserGroup.SYSTEM_ADMIN in user_to_update.groups and \
               user_to_update.email == self.tokeninfo.get("email") and \
               UserGroup.SYSTEM_ADMIN not in new_groups_enum:
                return rx.toast.error("操作不允許：系統管理員無法移除自身的管理員權限。") # type: ignore

            user_to_update.groups = new_groups_enum
            await user_to_update.save()
            
            await self.load_all_users() # 重新載入使用者列表以更新 UI
            self.close_edit_user_modal() # 關閉 Modal
            return rx.toast.success(f"使用者 {user_to_update.email} 的角色已成功更新。") # type: ignore
        except Exception as e:
            # 應記錄更詳細的錯誤日誌
            # await SystemLog.log(LogLevel.ERROR, f"更新使用者角色失敗: {e}", source="AdminUsersState", user_email=self.tokeninfo.get("email"), details={"editing_user_id": self.editing_user_id})
            return rx.toast.error(f"更新角色時發生錯誤：{str(e)}") # type: ignore

    # --- 輔助 getter 方法 ---
    def get_user_role_values(self, user: User) -> List[str]:
        """獲取指定使用者當前角色的字串值列表。

        此列表主要用於初始化角色編輯 Modal 中的 CheckboxGroup。
        會排除 `UserGroup.AUTHENTICATED_USER`，因為此角色是所有已登入使用者的基礎角色，
        不應在 UI 中作為可選項單獨管理。

        Args:
            user (User): 要獲取其角色值的使用者物件。

        Returns:
            List[str]: 使用者目前擁有的角色對應的 `UserGroup.value` 字串列表
                       (不含 `AUTHENTICATED_USER`)。
        """
        return [g.value for g in user.groups if g != UserGroup.AUTHENTICATED_USER]

    def get_all_manageable_roles_for_checkbox(self) -> List[Dict[str, str]]:
        """獲取所有可在 UI (CheckboxGroup) 中管理的角色選項。

        排除 `UserGroup.AUTHENTICATED_USER`，因為它不是一個可直接指派或移除的角色。
        其他所有在 `UserGroup` Enum 中定義的角色都會被包含。

        Returns:
            List[Dict[str, str]]: 用於 CheckboxGroup 的選項列表，
                                 每個選項是一個包含 "label" 和 "value" 的字典，
                                 兩者均為角色的 `UserGroup.value`。
        """
        # 排除 AUTHENTICATED_USER，因為它應由系統自動管理（所有登入者皆有）。
        # 系統管理員 (SYSTEM_ADMIN) 角色是否應在此處列出讓其他管理員指派，
        # 取決於具體的權限設計。此處假設所有非 AUTHENTICATED_USER 的角色均可被管理。
        return [
            {"label": ug.value, "value": ug.value} 
            for ug in UserGroup 
            if ug != UserGroup.AUTHENTICATED_USER
        ]
