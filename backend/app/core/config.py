from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "Automark"
    api_prefix: str = "/api"
    allow_origins: list[str] = ["*"]
    storage_dir: str = "storage"


settings = Settings()
