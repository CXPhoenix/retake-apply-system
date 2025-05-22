"""應用程式生命週期管理模듈。

此模듈定義了用於 Reflex 應用程式的生命週期 (lifespan) 上下文管理器，
主要負責在應用程式啟動時初始化資料庫連線，並在應用程式關閉時妥善關閉連線。
"""
import reflex as rx
from contextlib import asynccontextmanager
from .db import MongoDbClient
from ..configs import AppEnv
from ..models import SystemConfig, Manager

@asynccontextmanager
async def lifespan(app: rx.App):
    """Reflex 應用程式的非同步上下文管理器，用於管理應用程式生命週期事件。

    Args:
        app (rx.App): Reflex 應用程式實例。雖然在此函式中未直接使用 `app` 參數，
                      但 Reflex 的生命週期管理器期望此簽名。
    """
    app_env = AppEnv()
    mclient = MongoDbClient()
    try:
        await mclient.init_database_connection(app_env.managers_store, [Manager])
        await mclient.init_database_connection(app_env.system_configs_store, [SystemConfig])
        data_year = app_env.default_year
        if len(newest_year_settings := await SystemConfig.find().to_list()) > 0:
            data_year = newest_year_settings[0].retake_year
        else:
            await SystemConfig(retake_year=app_env.default_year).insert()
        await mclient.init_database_connection(str(data_year), [])
        yield # 應用程式在此處運行
    finally:
        mclient.close_connection()
