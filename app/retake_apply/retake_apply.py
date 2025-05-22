"""校園重補修課程登記系統的主應用程式設定檔案"""

import reflex as rx

from .pages.index import index
from .pages.dashboard import dashboard_page
from .pages.course_selection import course_selection_page
from .states.auth import AuthState
from .utils.lifespan import lifespan

app = rx.App(
    lifespan_tasks=[lifespan],
)
# app.add_page(index, title="歡迎")
# app.add_page(dashboard_page, route="/dashboard", title="使用者儀表板")
# app.add_page(course_selection_page, route="/course-selection", title="課程選擇")
