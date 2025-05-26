import reflex as rx
from reflex_google_auth import require_google_login

class ManagerPanelState(rx.State):
    """Maneger panel state: 處理管理者 panel 的狀態"""
    #TODO: State design
    ...

@require_google_login
def manager_panel_page() -> rx.Component:
    """Manager panel page: 管理者 panel 首頁"""
    #TODO: Page design
    ...