from pydantic import BaseModel


class Settings(BaseModel):
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "warning"

    # Application settings
    MAX_QUEUE_SIZE: int = 1
    FRAME_TIMEOUT: float = 1.0
    MAX_RETRIES: int = 5
    RETRY_DELAY: float = 0.5


# Create an instance of Settings
settings = Settings()
