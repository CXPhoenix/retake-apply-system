import reflex as rx
from reflex_google_auth import GoogleAuthState

class LoginState(GoogleAuthState):
    """Login State: 處理登入狀態（使用 Google Oauth）"""
    #TODO: State design
    ...

def login_page() -> rx.Component:
    """Login page: 使用 Google 帳號登入頁面"""
    #TODO: Page design
    ...