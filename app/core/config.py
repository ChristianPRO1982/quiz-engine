import os


def get_env(name: str, default: str) -> str:
    value = os.getenv(name)
    return value if value else default


class Settings:
    def __init__(self) -> None:
        self.database_url = get_env(
            "DATABASE_URL",
            "mysql+pymysql://quiz:quiz@db:3306/quiz_engine",
        )
        self.base_url = get_env("BASE_URL", "http://localhost:8000")
        self.log_level = get_env("LOG_LEVEL", "INFO")


settings = Settings()
