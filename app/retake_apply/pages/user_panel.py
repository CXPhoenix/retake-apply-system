import reflex as rx
from reflex_google_auth import require_google_login

class DashboardState(rx.State):
    """Dashboard State: 處理重補修申請狀態展示頁面"""
    #TODO: State design
    ...

class ApplyRetakeState(rx.State):
    """Apply retake state: 處理申請重補修課程的狀態"""
    #TODO: State design
    ...

@require_google_login
def dashboard_page() -> rx.Component:
    """Dashboard page: 重補修申請首頁"""
    #TODO: Page design
    ...

@require_google_login
def retake_apply_page() -> rx.Component:
    """Retake apply page: 申請重補修課程選課頁面"""
    #TODO: Page design
    ...