"""應用程式基礎身份驗證與授權狀態管理模組。

此模組定義了 `AuthState` 類別，它繼承自 `reflex_google_auth.GoogleAuthState`，
並擴展了其功能以整合本地應用程式的使用者角色 (UserGroup) 管理。
同時，提供了 `require_group` 裝飾器，用於基於角色的頁面存取控制。
"""
import typing
import functools
import reflex as rx
from reflex_google_auth import GoogleAuthState # Google OAuth 基礎狀態

from ..models.users import User, UserGroup # 本地使用者模型與角色列舉
from ..utils.funcs import get_utc_now # 使用 UTC 時間
from beanie.operators import Set # MongoDB 更新操作符
from reflex.utils import console # Reflex 控制台日誌工具

class AuthState(GoogleAuthState):
    """應用程式的身分驗證狀態，整合 Google 身分驗證與本地角色管理。

    此狀態類別負責處理 Google 登入成功後的使用者資料同步 (創建或更新本地 User 文件)，
    並從本地資料庫載入使用者的角色群組。

    Attributes:
        REDIRECT_URI_ON_LOGIN_REQUIRED (str): 當頁面需要登入但使用者未登入時，
                                              `reflex-google-auth` 將重定向到的路徑。
        REDIRECT_URI_ON_UNAUTHORIZED_REQUEST (str): 當使用者已登入但嘗試存取未授權資源時，
                                                    `reflex-google-auth` 可能使用的重定向路徑。
        DEFAULT_UNAUTHORIZED_REDIRECT_PATH (str): 本應用程式中，當 `require_group` 檢查失敗時，
                                                  預設重定向到的未授權提示頁面路徑。
        DEFAULT_GROUP_ON_NO_GROUP (str): (此屬性目前未直接使用，但可作為未來參考)
                                         若使用者在資料庫中無任何群組時，可賦予的預設群組值。
        _app_user_groups_var (rx.Var[list[UserGroup]]): 內部狀態變數，儲存當前登入使用者
                                                       從資料庫同步的應用程式特定角色群組列表。
                                                       使用 `rx.Var` 以實現反應式更新。
        are_groups_loaded_for_session (bool): (此屬性目前未直接使用)
                                              標記當前會話是否已成功載入使用者群組。
    """
    REDIRECT_URI_ON_LOGIN_REQUIRED = "/" # 登入頁面
    REDIRECT_URI_ON_UNAUTHORIZED_REQUEST = '/dashboard' # 登入後預設跳轉儀表板
    DEFAULT_UNAUTHORIZED_REDIRECT_PATH = '/unauthorized'
    DEFAULT_GROUP_ON_NO_GROUP = UserGroup.STUDENT.value

    # 使用 rx.Var 來儲存從資料庫同步的應用程式特定使用者群組，以實現反應式更新
    _app_user_groups_var: list[UserGroup] = [] # 直接使用 Python list 初始化
    are_groups_loaded_for_session: bool = False

    @rx.var
    def current_user_google_id(self) -> typing.Optional[str]:
        """獲取當前已登入使用者的 Google ID (`sub` 欄位)。

        Returns:
            typing.Optional[str]: 若使用者已登入且 `user_info` 包含 `sub`，則返回其 Google ID；
                                  否則返回 `None`。
        """
        if self.tokeninfo and isinstance(self.tokeninfo, dict): # 改用 self.tokeninfo
            return self.tokeninfo.get("sub")
        return None
    
    @rx.var(cache=True)
    def protected_content(self) -> str:
        """一個範例受保護內容，僅限已登入使用者查看。

        Returns:
            str: 根據登入狀態顯示不同的歡迎訊息。
        """
        if self.token_is_valid:
            return f"此內容僅限已登入使用者查看。很高興見到您，{self.tokeninfo.get('name', '使用者')}！"
        return "尚未登入。"

    async def on_success(self, id_token: dict[str, typing.Any]):
        """Google 登入成功後的回呼事件處理器。

        此方法會被 `reflex-google-auth` 在成功驗證 Google ID Token 後呼叫。
        主要職責包括：
        1. 呼叫父類的 `on_success` 以處理 `tokeninfo`。
        2. 若 token 有效，則從 `tokeninfo` 中提取使用者資訊。
        3. 根據 Google `sub` ID 查找或創建本地 `User` 資料庫記錄。
        4. 更新本地使用者的資訊 (如姓名、頭像、最後登入時間)。
        5. 從本地使用者記錄中讀取其角色群組 (`groups`) 並更新 `_app_user_groups_var` 狀態。

        Args:
            id_token (dict[str, typing.Any]): 包含已驗證的 Google ID Token 資訊的字典。
        """
        async with self:  # 確保狀態更新的原子性與批次處理
            await super().on_success(id_token)  # 呼叫父類別的 on_success 以填充 self.tokeninfo
            
            if self.token_is_valid:
                user_email = self.tokeninfo.get("email")
                google_sub = self.tokeninfo.get("sub")  # Google User ID (唯一識別碼)
                user_name = self.tokeninfo.get("name")
                user_picture = self.tokeninfo.get("picture")
                
                if google_sub:
                    existing_user = await User.find_one(User.google_sub == google_sub)
                    if existing_user:
                        # 更新現有使用者的資訊
                        await existing_user.update(
                            Set({ # 使用 Set 操作符僅更新指定欄位
                                User.fullname: user_name,
                                User.picture: user_picture,
                                User.last_login: get_utc_now() # 使用 UTC 時間
                            })
                        )
                        self._app_user_groups_var = existing_user.groups
                        console.info(f"使用者 {existing_user.fullname} (ID: {google_sub}) 已登入並更新資訊。群組: {existing_user.groups}")
                    else:
                        # 創建新使用者，並賦予預設群組
                        default_groups = [UserGroup.STUDENT, UserGroup.AUTHENTICATED_USER]
                        new_user = User(
                            email=user_email, # type: ignore # Pydantic EmailStr
                            fullname=user_name,
                            picture=user_picture,
                            google_sub=google_sub,
                            groups=default_groups,
                            last_login=get_utc_now() # 設定首次登入時間
                        )
                        await new_user.insert()
                        self._app_user_groups_var = new_user.groups
                        console.info(f"新使用者 {user_name} (ID: {google_sub}) 已創建。群組: {default_groups}")
                else:
                    # 理論上，若 token_is_valid 為 True，google_sub 應該存在。
                    self._app_user_groups_var = []
                    console.error("Google 登入成功，但無法從 tokeninfo 中獲取 'sub' (Google User ID)。")
            else:
                # Token 無效，清除群組資訊
                self._app_user_groups_var = []
                console.warn("Google 登入 token 驗證失敗或已過期。")

    @rx.var
    def current_user_groups(self) -> list[UserGroup]:
        """獲取當前已登入使用者的應用程式內部角色群組列表。

        此為快取計算變數 (`@rx.cached_var`)，其值依賴於 `_app_user_groups_var`。
        若使用者未登入 (token 無效)，則回傳空列表。

        Returns:
            list[UserGroup]: 使用者目前的角色群組列表。
        """
        if not self.token_is_valid:
            return []
        # _app_user_groups_var 的值在 Reflex 中會被自動提取
        return self._app_user_groups_var

    def is_member_of_any(self, groups_to_check: list[UserGroup]) -> bool:
        """檢查當前登入使用者是否屬於提供的任一群組。

        此為一個同步的 Reflex Var (`@rx.var`)，適合在 UI 元件的 `rx.cond` 中直接使用。
        它會檢查 `current_user_groups` 是否與 `groups_to_check` 中的任何群組有交集。

        Args:
            groups_to_check (list[UserGroup]): 一個包含 `UserGroup` Enum 成員的列表，
                                               代表需要檢查的權限群組。

        Returns:
            bool: 若使用者已登入、水合完成，且其角色群組中至少有一個存在於
                  `groups_to_check` 列表中，則回傳 `True`。
                  若 `groups_to_check` 為空列表，則只要使用者已登入且水合完成即回傳 `True`。
                  其他情況（如未登入、未水合）均回傳 `False`。
        """
        if not self.token_is_valid or not self.is_hydrated:
            return False # 必須已登入且客戶端已水合
        
        if not groups_to_check: # 若未指定任何必要群組
            return True # 則只要登入即可認為有權限 (例如，訪問一般已登入頁面)
        
        current_groups = self.current_user_groups # 使用快取的群組列表
        return any(group in current_groups for group in groups_to_check)

    def logout(self):
        """執行使用者登出操作。

        除了呼叫父類的 `logout` 方法（清除 Google token 等），
        此方法還會重設本地的 `_app_user_groups_var` 為空列表。
        """
        super().logout()
        # 確保在非同步上下文中修改 rx.Var
        async def reset_groups_async():
            self._app_user_groups_var = []
        
        # 使用 rx.call_soon_threadsafe 和 rx.background 確保在事件循環中安全
        rx.call_soon_threadsafe(rx.background(reset_groups_async)()) # type: ignore
        self.are_groups_loaded_for_session = False

# default_unauthorized_view_factory 已符合 .clinerules 文件中的範例，
# 它能顯示所需群組和目前群組。
def default_unauthorized_view_factory(
    required_groups: list[UserGroup],
    current_user_groups_var: rx.Var[list[UserGroup]] # 傳入 rx.Var 以便反應式顯示
) -> rx.Component:
    """產生一個預設的未授權檢視元件。

    Args:
        required_groups (list[UserGroup]): 存取受限資源所需的群組列表。
        current_user_groups_var (rx.Var[list[UserGroup]]): 代表當前使用者群組的 Reflex Var，
                                                          用於在 UI 中反應式地顯示。

    Returns:
        rx.Component: 一個提示使用者權限不足的 Reflex UI 元件。
    """
    return rx.vstack(
        rx.heading("⛔ 存取權限不足", size="7", color_scheme="red"),
        rx.text("抱歉，您沒有足夠的權限來存取此頁面或功能。"),
        rx.text("所需群組：", font_weight="bold"),
        rx.hstack(
            *[rx.badge(group, color_scheme="amber") for group in required_groups], # 直接使用 group
            spacing="2"
        ),
        rx.text("您目前的群組：", font_weight="bold", margin_top="0.5em"),
        rx.cond(
            current_user_groups_var.length() > 0, # 使用 .length() 方法
            rx.hstack(
                rx.foreach(
                    current_user_groups_var,
                    lambda group_item: rx.badge(group_item, color_scheme="grass") # 直接使用 group_item
                ),
                spacing="2"
            ),
            rx.text("(無群組或未載入)", color_scheme="gray")
        ),
        rx.link("返回首頁", href="/", margin_top="1.5em", color_scheme="blue"),
        align="center",
        spacing="3",
        padding="2em",
        border="1px solid var(--gray-a6)", # 使用 Radix Theme token
        border_radius="var(--radius-3)",
        box_shadow="var(--shadow-3)",
        max_width="500px",
        margin="2em auto",
    )

def require_group(
    allowed_groups: list[UserGroup],
    unauthorized_view_func: typing.Callable[[list[UserGroup], rx.Var[list[UserGroup]]], rx.Component] | None = None
) -> typing.Callable[[typing.Callable[..., rx.Component]], typing.Callable[..., rx.Component]]:
    """一個頁面裝飾器，用於實現基於角色的存取控制 (RBAC)。

    此裝飾器應在 `@require_google_login` 之後套用。它會檢查當前登入的使用者
    是否屬於 `allowed_groups` 中定義的任何一個角色群組。
    若權限不足，則顯示由 `unauthorized_view_func` （或預設的工廠函式）產生的未授權頁面。

    設計考量 (參考 .clinerules):
    - 權限檢查核心邏輯依賴 `AuthState.is_member_of_any`。
    - 為了在 `rx.cond` 中反應式地使用 `AuthState` 的屬性，同時保持裝飾器的通用性，
      此處採用了在 `wrapper` 函式內部定義一個臨時的 `PermissionCheckState` 類別。
      這個內部類別繼承自 `AuthState`，使其能夠存取當前的驗證和群組狀態。
      `PermissionCheckState.has_permission_for_this_page` 是一個 `@rx.var`，
      它封裝了對 `self.is_member_of_any(allowed_groups)` 的呼叫，確保了反應性。

    Args:
        allowed_groups (list[UserGroup]): 一個包含允許存取此頁面的 `UserGroup` Enum 成員的列表。
                                          若此列表為空，則僅檢查使用者是否已登入。
        unauthorized_view_func (typing.Callable, optional):
            一個函式，用於在使用者權限不足時產生自訂的未授權檢視元件。
            此函式應接受 `required_groups` 和 `current_user_groups_var` 作為參數。
            若為 `None`，則使用 `default_unauthorized_view_factory`。

    Returns:
        typing.Callable: 一個裝飾器函式，它會包裝原始的頁面函式 (`page_fn`)
                         並加入權限檢查邏輯。
    """
    actual_unauthorized_view_factory = unauthorized_view_func or default_unauthorized_view_factory

    def decorator(page_fn: typing.Callable[..., rx.Component]) -> typing.Callable[..., rx.Component]:
        @functools.wraps(page_fn)
        def wrapper(*args, **kwargs) -> rx.Component:
            
            # 內部狀態類別，用於在 rx.cond 中進行反應式權限檢查
            class PermissionCheckState(AuthState):
                @rx.var
                def has_permission_for_this_page(self) -> bool:
                    # 呼叫 AuthState 中已定義的 is_member_of_any 進行實際檢查
                    return self.is_member_of_any(allowed_groups)

            return rx.cond(
                AuthState.is_hydrated, # 步驟 1: 確保 GoogleAuthState 已完成客戶端水合
                rx.cond(
                    AuthState.token_is_valid, # 步驟 2: 確保使用者已登入 (token 有效)
                    rx.cond(
                        PermissionCheckState.has_permission_for_this_page, # 步驟 3: 檢查角色權限
                        page_fn(*args, **kwargs), # 若所有檢查通過，渲染原始頁面元件
                        # 若權限不足，顯示未授權視圖
                        actual_unauthorized_view_factory(allowed_groups, AuthState.current_user_groups) 
                    ),
                    # 若 token 無效 (未登入)，理論上 @require_google_login 會處理重定向。
                    # 但作為額外防護，或在 @require_google_login 設定為非強制時，
                    # 此處也顯示未授權視圖。
                    actual_unauthorized_view_factory(allowed_groups, AuthState.current_user_groups)
                ),
                # 在水合或 token 驗證完成前，顯示載入指示器
                rx.center(rx.spinner(size="3"), padding_y="5em") 
            )
        return wrapper
    return decorator
