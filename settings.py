from pydantic_settings import BaseSettings, SettingsConfigDict

# class Settings(BaseSettings):
#   model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


class Settings(BaseSettings):
  model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
  hume_api_key: str
  hume_secret_key: str
  hume_config_id: str

  # OpenAI API
  OPENAI_MODEL_ID: str = "gpt-4o-mini"
  OPENAI_API_KEY: str | None = "YOUR_OPENAI_API_KEY"

  # MongoDB database
  DATABASE_HOST: str = "YOUR_MONGODB_DATABASE_HOST"
  DATABASE_NAME: str = "YOUR_MONGODB_DATABASE_NAME"

  @property
  def OPENAI_MAX_TOKEN_WINDOW(self) -> int:
    official_max_token_window = {
      "gpt-3.5-turbo": 16385,
      "gpt-4-turbo": 128000,
      "gpt-4o": 128000,
      "gpt-4o-mini": 128000,
    }.get(self.OPENAI_MODEL_ID, 128000)

    max_token_window = int(official_max_token_window * 0.90)

    return max_token_window

settings = Settings()