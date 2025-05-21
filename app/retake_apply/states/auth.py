import typing
import functools
import reflex as rx
from reflex_google_auth import GoogleAuthState

from ..models.users import User, UserGroup
from ..utils.funcs import get_now
from beanie.operators import Set
from reflex.utils import console

class AuthState(GoogleAuthState):
    """應用程式的身分驗證狀態，整合 Google 身分驗證與本地角色管理"""
    REDIRECT_URI_ON_LOGIN_REQUIRED = "/"
    REDIRECT_URI_ON_UNAUTHORIZED_REQUEST = '/dashboard'
    DEFAULT_UNAUTHORIZED_REDIRECT_PATH = '/unauthorized'
    DEFAULT_GROUP_ON_NO_GROUP = UserGroup.STUDENT.value

    # 使用 rx.Var 來儲存從資料庫同步的應用程式特定使用者群組，以實現反應式更新
    _app_user_groups_var: rx.Var[list[UserGroup]] = rx.Var([])
    are_groups_loaded_for_session: bool = False

    @rx.var
    def current_user_google_id(self) -> str | None:
        """獲取當前使用者的 Google ID"""
        if self.user_info and isinstance(self.user_info, dict):
            return self.user_info.get("sub")
        return None
    
    @rx.var(cache=True)
    def protected_content(self) -> str:
        """顯示受保護內容，僅限已登入使用者查看"""
        if self.token_is_valid:
            return f"此內容僅限已登入使用者查看。很高興見到您，{self.tokeninfo.get('name', '使用者')}！"
        return "尚未登入。"

    async def on_success(self, id_token: dict[str, typing.Any]):
        """
        在 Google 登入成功後觸發。
        處理 token 驗證、使用者資料庫同步及群組更新。
        """
        async with self:  # 確保狀態更新的原子性與批次處理
            await super().on_success(id_token)  # 呼叫父類別的 on_success 處理 tokeninfo
            
            if self.token_is_valid:
                user_email = self.tokeninfo.get("email")
                google_sub = self.tokeninfo.get("sub")  # Google User ID
                user_name = self.tokeninfo.get("name")
                user_picture = self.tokeninfo.get("picture")
                
                if google_sub:
                    existing_user = await User.find_one(User.google_sub == google_sub)
                    if existing_user:
                        # 更新現有使用者資訊
                        await existing_user.update(
                            Set({
                                User.fullname: user_name,
                                User.picture: user_picture,
                                User.last_login: get_now()
                            })
                        )
                        self._app_user_groups_var = existing_user.groups
                        console.info(f"使用者 {existing_user.fullname} (ID: {google_sub}) 已存在，群組: {existing_user.groups}")
                    else:
                        # 創建新使用者
                        default_groups = [UserGroup.STUDENT, UserGroup.AUTHENTICATED_USER]
                        new_user = User(
                            email=user_email,
                            fullname=user_name,
                            picture=user_picture,
                            google_sub=google_sub,
                            groups=default_groups
                        )
                        await new_user.insert()
                        self._app_user_groups_var = new_user.groups
                        console.info(f"新使用者 {user_name} (ID: {google_sub}) 已創建，群組: {default_groups}")
                else:
                    self._app_user_groups_var = []  # Token 有效但無 google_sub，理論上不應發生
                    console.error("Google 登入成功但無法獲取 sub 欄位。")
            else:
                self._app_user_groups_var = []  # Token 無效，清除群組
                console.error("Google 登入失敗，token 無效。")

    @rx.cached_var
    def current_user_groups(self) -> list[UserGroup]:
        """獲取當前登入使用者的應用程式內部群組"""
        if not self.token_is_valid:
            return []
        return self._app_user_groups_var

    @rx.var
    def is_member_of_any(self, groups_to_check: list[UserGroup]) -> bool:
        """
        檢查當前登入使用者是否為所提供群組列表中的任何一個成員。
        此為同步的 rx.var，適合在 UI 中使用。
        """
        if not self.token_is_valid or not self.is_hydrated:
            return False
        if not groups_to_check: # 如果不需要特定群組 (例如，僅需登入)
            return True # 則已登入且水合完成的使用者即有權限
        
        # current_user_groups 已經是 @rx.cached_var，可以直接使用
        current_groups = self.current_user_groups
        return any(group in current_groups for group in groups_to_check)

    def logout(self):
        """登出使用者並清除群組資訊"""
        super().logout()
        async def reset_groups(): # 確保在 async context 中修改 rx.Var
            self._app_user_groups_var = []
        rx.call_soon_threadsafe(rx.background(reset_groups)()) # type: ignore
        self.are_groups_loaded_for_session = False

# default_unauthorized_view_factory 已符合 .clinerules 文件中的範例，
# 它能顯示所需群組和目前群組。
def default_unauthorized_view_factory(
    required_groups: list[UserGroup],
    current_user_groups_var: rx.Var[list[UserGroup]] # 傳入 rx.Var 以便反應式顯示
) -> rx.Component:
    """產生一個預設的未授權檢視元件。"""
    return rx.vstack(
        rx.heading("⛔ 存取權限不足", size="7", color_scheme="red"),
        rx.text("抱歉，您沒有足夠的權限來存取此頁面或功能。"),
        rx.text("所需群組：", font_weight="bold"),
        rx.hstack(
            *[rx.badge(group.value, color_scheme="amber") for group in required_groups],
            spacing="2"
        ),
        rx.text("您目前的群組：", font_weight="bold", margin_top="0.5em"),
        rx.cond(
            rx.length(current_user_groups_var) > 0,
            rx.hstack(
                rx.foreach(
                    current_user_groups_var,
                    lambda group_item: rx.badge(group_item.value, color_scheme="grass")
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
):
    """
    一個頁面裝飾器，用於限制只有特定群組的使用者才能存取某個頁面或組件。
    應在 @require_google_login 之後使用。

    參數:
        allowed_groups: 存取此頁面所需的群組列表。如果為空列表或 None，則僅檢查是否登入。
        unauthorized_view_func: 一個函式，用於在使用者權限不足時產生顯示的元件。
                                若為 None，則使用 default_unauthorized_view_factory。
    """
    actual_unauthorized_view_factory = unauthorized_view_func or default_unauthorized_view_factory

    def decorator(page_fn: typing.Callable[..., rx.Component]) -> typing.Callable[..., rx.Component]:
        @functools.wraps(page_fn)
        def wrapper(*args, **kwargs) -> rx.Component:
            # 權限檢查邏輯現在依賴 AuthState.is_member_of_any(allowed_groups)
            # 這個 @rx.var 是同步的，可以直接在 rx.cond 中使用。
            # AuthState.current_user_groups 也是 @rx.cached_var，適合在 UI 中使用。
            
            # 創建一個內部組件，以便在 rx.cond 中使用 AuthState 的屬性
            # 這是因為裝飾器本身在定義時無法直接存取 AuthState 的實例。
            # 頁面被渲染時，Reflex 會處理 State 的上下文。
            
            # 根據 .clinerules 的範例，PermissionCheckState 的方式是可行的。
            # 我們將使用 AuthState.is_member_of_any 來簡化。
            # 注意：直接在 rx.cond 中使用 AuthState.is_member_of_any(allowed_groups)
            # 可能會因為 allowed_groups 不是 rx.Var 而導致非反應式。
            # 最好的方式是讓頁面繼承一個包含此邏輯的 BasePageState，
            # 或者在 AuthState 中有一個更通用的 @rx.var，
            # 但為符合 .clinerules 的結構，我們保持 PermissionCheckState。

            class PermissionCheckState(AuthState):
                @rx.var
                def has_permission_for_this_page(self) -> bool:
                    # 使用 AuthState 中定義的 is_member_of_any
                    return self.is_member_of_any(allowed_groups)

            return rx.cond(
                AuthState.is_hydrated, # 確保 GoogleAuthState 已完成客戶端水合
                rx.cond(
                    AuthState.token_is_valid, # 先檢查是否登入
                    rx.cond(
                        PermissionCheckState.has_permission_for_this_page, # 使用內部狀態的權限檢查
                        page_fn(*args, **kwargs), # 如果有權限，渲染原始組件
                        # 將 AuthState.current_user_groups (rx.Var) 傳遞給未授權視圖
                        actual_unauthorized_view_factory(allowed_groups, AuthState.current_user_groups) 
                    ),
                    # 若未登入，require_google_login 應該會處理。
                    # 但作為防護，可以顯示未授權或導向。
                    # 這裡顯示未授權視圖，因為 require_google_login 會處理重定向。
                    # 如果 require_google_login 允許未登入者看到此頁面（例如，它僅用於獲取 tokeninfo），
                    # 那麼這裡的邏輯就很重要。
                    actual_unauthorized_view_factory(allowed_groups, AuthState.current_user_groups)
                ),
                rx.center(rx.spinner(size="3"), padding_y="5em") # 水合或檢查時的佔位符
            )
        return wrapper
    return decorator
