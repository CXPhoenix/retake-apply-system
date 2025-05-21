"""校園重補修課程登記系統的 Reflex 狀態管理模組。

此模組包含應用程式中所有頁面和可互動元件的後端狀態 (rx.State) 定義。
每個子模組通常對應一個特定頁面或一組相關功能的狀態邏輯。
基礎的身份驗證狀態 (AuthState) 也在此模組或其子模組中定義。
"""

# 預期將來可能會從此處匯出 states 子模組中的特定狀態類別。
# 例如:
# from .auth import AuthState
# from .dashboard_state import DashboardState

# __all__ = [
#     "AuthState",
#     "DashboardState",
# ]
