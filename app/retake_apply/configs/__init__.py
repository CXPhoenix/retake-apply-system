from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvSetting(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore", case_sensitive=False)


class DbEnv(EnvSetting):
    model_config = SettingsConfigDict(env_prefix="MONGODB_")

    url: str
    port: int = 27017
    username: str
    password: str
    authSource: str = "admin"
    db_name: str
