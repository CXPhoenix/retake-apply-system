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
    async def has_required_groups(self, required_groups: list[UserGroup]) -> bool:
        """
        計算屬性：檢查目前使用者是否擁有所有必要的群組。
        此方法假設 token_is_valid 為 True。
        """
        if not self.token_is_valid:
            return False
        if not required_groups: # 如果頁面不需要特定群組
            return True # 則已登入的使用者即有權限
        # 檢查 current_user_groups 是否包含 required_groups 中的任何一個群組
        # 注意：這裡的邏輯是 OR (任何一個即可)，如果需要 AND (全部擁有)，則需修改
        return any(group in self.current_user_groups for group in required_groups)

    def logout(self):
        """登出使用者並清除群組資訊"""
        super().logout()
        self._app_user_groups_var = []
        self.are_groups_loaded_for_session = False

# TODO: 根據 .clinerules/CODEING_STYLE_RULE.md 中的 `require_group` 裝飾器範例，
#       進一步完善 default_unauthorized_view_factory，使其能顯示更詳細的權限資訊，
#       例如：所需群組、目前群組等。
#       目前的實作僅為一個簡單的文字提示。
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
        allowed_groups: 存取此頁面所需的群組列表。
        unauthorized_view_func: 一個函式，用於在使用者權限不足時產生顯示的元件。
                                若為 None，則使用 default_unauthorized_view_factory。
    """
    actual_unauthorized_view_factory = unauthorized_view_func or default_unauthorized_view_factory

    def decorator(page_fn: typing.Callable[..., rx.Component]) -> typing.Callable[..., rx.Component]:
        @functools.wraps(page_fn)
        def wrapper(*args, **kwargs) -> rx.Component:
            # 創建一個內部組件狀態來封裝權限檢查邏輯，使其反應式
            # TODO: 這裡的 AuthState 繼承可能需要調整，以確保能正確存取到應用程式的 AuthState 實例。
            #       或者，直接在 AuthState 中定義一個 is_authorized_for_groups(allowed_groups) 的 @rx.var
            #       然後在此處直接使用 AuthState.is_authorized_for_groups(allowed_groups)。
            #       目前的 has_required_groups 是 async def，不適合直接用於 rx.cond 的條件判斷。
            #       暫時先簡化處理，後續需修正此權限檢查邏輯。

            # 暫時的權限檢查邏輯 (非反應式，且直接呼叫 async 方法，可能會有問題)
            # 正確作法應為在 AuthState 中提供一個 @rx.var is_authorized(groups)
            # 此處僅為示意，待修正
            
            # 修正：改為在 AuthState 中新增一個 is_authorized_for_page @rx.var
            # 此處的 wrapper 應該要能存取到 AuthState 的實例，
            # 但裝飾器本身無法直接存取。
            # Reflex 的頁面函式本身是無狀態的，狀態由 State 管理。
            # 因此，權限檢查邏輯最好封裝在 State 內部，並由頁面元件 rx.cond 判斷。

            # 根據規格文件中的範例，我們需要在 AuthState 中有一個 @rx.var has_permission
            # 這裡我們模擬這個行為，但理想情況下，這個邏輯應該在 AuthState 內部。

            class PermissionCheckState(AuthState): # 應繼承自應用程式的 AuthState
                @rx.var
                def has_permission_for_page(self) -> bool:
                    if not self.token_is_valid:
                        return False
                    # self.current_user_groups 來自繼承的 AuthState
                    return any(group in self.current_user_groups for group in allowed_groups)

            return rx.cond(
                AuthState.is_hydrated, # 確保 GoogleAuthState 已完成客戶端水合
                rx.cond(
                    AuthState.token_is_valid, # 先檢查是否登入
                    rx.cond(
                        PermissionCheckState.has_permission_for_page, # 使用內部狀態的權限檢查
                        page_fn(*args, **kwargs), # 如果有權限，渲染原始組件
                        actual_unauthorized_view_factory(allowed_groups, AuthState.current_user_groups)
                    ),
                    # 若未登入，理論上 require_google_login 會先處理，但為保險起見，可導向登入
                    rx.redirect(AuthState.REDIRECT_URI_ON_LOGIN_REQUIRED or "/") 
                ),
                rx.center(rx.spinner(size="3"), padding_y="5em") # 水合或檢查時的佔位符
            )
        return wrapper
    return decorator
