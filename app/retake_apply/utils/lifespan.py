"""應用程式生命週期管理模듈。

此模듈定義了用於 Reflex 應用程式的生命週期 (lifespan) 上下文管理器，
主要負責在應用程式啟動時初始化資料庫連線，並在應用程式關閉時妥善關閉連線。
"""
import reflex as rx
# from reflex.utils import console # console 未在此檔案中直接使用
from contextlib import asynccontextmanager
from .db import init_db, close_db # 從同目錄的 db.py 匯入資料庫處理函式

@asynccontextmanager
async def lifespan(app: rx.App):
    """Reflex 應用程式的非同步上下文管理器，用於管理應用程式生命週期事件。

    在應用程式啟動 (`startup`) 時，此函式會呼叫 `init_db()` 來初始化
    MongoDB 資料庫連線並設定 Beanie ODM。
    在應用程式關閉 (`shutdown`) 時，它會確保透過 `close_db()` 關閉資料庫連線。

    Args:
        app (rx.App): Reflex 應用程式實例。雖然在此函式中未直接使用 `app` 參數，
                      但 Reflex 的生命週期管理器期望此簽名。
    """
    client = None # 初始化 client 變數
    try:
        client = await init_db()
        yield # 應用程式在此處運行
    finally:
        if client:
            await close_db(client=client)
