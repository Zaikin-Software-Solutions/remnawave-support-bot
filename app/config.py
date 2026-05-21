from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Конфиг бота, читается из переменных окружения / .env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    bot_token: str = Field(..., alias="BOT_TOKEN")
    owner_tg_id: int = Field(..., alias="OWNER_TG_ID")

    remnawave_base_url: str = Field(..., alias="REMNAWAVE_BASE_URL")
    remnawave_api_token: str = Field(..., alias="REMNAWAVE_API_TOKEN")

    db_path: str = Field("/data/bot.db", alias="DB_PATH")

    autoreply_text: str = Field(
        "Принято! Администратор скоро вернётся с обратной связью.",
        alias="AUTOREPLY_TEXT",
    )


settings = Settings()  # type: ignore[call-arg]
