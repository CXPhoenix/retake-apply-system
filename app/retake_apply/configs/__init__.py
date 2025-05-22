from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvSetting(BaseSettings):
    """所有環境變數設定類的基底類別。

    透過 `model_config` 設定 Pydantic 的行為：
    - `extra="ignore"`: 忽略環境變數中未在模型中定義的額外欄位。
    - `case_sensitive=False`: 環境變數名稱不區分大小寫。
    """
    model_config = SettingsConfigDict(extra="ignore", case_sensitive=False)


class DbEnv(EnvSetting):
    """MongoDB 資料庫連線相關的環境變數設定。

    使用 `env_prefix="MONGODB_"` 指定所有相關環境變數都應以 "MONGODB_" 開頭。
    例如，`url` 欄位會對應到 `MONGODB_URL` 環境變數。

    Attributes:
        url (str): MongoDB 連線 URL (不含協定，例如 'localhost' 或 'mongo_server')。
                   對應環境變數 `MONGODB_URL`。
        port (int): MongoDB 服務的連接埠號。預設為 27017。
                    對應環境變數 `MONGODB_PORT`。
        username (str): 用於連線 MongoDB 的使用者名稱。
                        對應環境變數 `MONGODB_USERNAME`。
        password (str): 用於連線 MongoDB 的使用者密碼。
                        對應環境變數 `MONGODB_PASSWORD`。
        authSource (str): MongoDB 驗證時使用的資料庫名稱。預設為 "admin"。
                          對應環境變數 `MONGODB_AUTHSOURCE`。
        db_name (str): 應用程式將使用的 MongoDB 資料庫名稱。
                       對應環境變數 `MONGODB_DB_NAME`。
    """
    model_config = SettingsConfigDict(env_prefix="MONGODB_")

    url: str  # 例如: "localhost" 或 "your_mongo_host"
    port: int = 27017
    username: str
    password: str
    authSource: str = "admin"  # 驗證資料庫
    
class AppEnv(EnvSetting):
    model_config = SettingsConfigDict(env_prefix="FHSH_")
    
    managers_store: str = "managers"
    system_configs_store: str = "system_configs"
    default_year: int = 114