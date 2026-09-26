from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    gemini_api_key: str
    gemini_workout_model: str = "gemini-3.1-pro-preview"
    gemini_tip_model: str = "gemini-3.8-flash"

    database_url: str = "sqlite:///./fitbuddy.db"

    admin_token: str = "fitbuddy-admin-123"
    session_secret: str = "fitbuddy-session-secret-change-this"

    app_name: str = "FitBuddy"
    debug: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()