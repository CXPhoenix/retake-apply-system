import reflex as rx
from reflex_google_auth import require_google_login

class SystemPanelState(rx.State):
    """System panel state: 處理系統控制頁面的狀態"""
    #TODO: State design
    ...

@require_google_login
def system_panel_page() -> rx.Component:
    """System panel page: 系統設定首頁"""
    #TODO: Page design
    ...