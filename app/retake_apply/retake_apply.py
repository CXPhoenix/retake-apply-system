"""校園重補修課程登記系統的主應用程式設定檔案"""

import reflex as rx


from .utils.lifespan import lifespan

app = rx.App(
    lifespan_tasks=[lifespan],
)
