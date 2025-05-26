"""校園重補修課程登記系統的主應用程式設定檔案"""

import reflex as rx

from .utils.lifespan import lifespan
from .pages import index_page, login_page

app = rx.App(
    lifespan_tasks=[lifespan],
)

app.add_page(login_page, "/login")
