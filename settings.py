from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
  model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

  # OpenAI API
  OPENAI_MODEL_ID: str = "gpt-4o-mini"
  OPENAI_API_KEY: str | None = "YOUR_OPENAI_API_KEY"

  # GitHub API
  GITHUB_API_TOKEN: str | None = "YOUR_GITHUB_API_TOKEN"

  # SQL Database
  POSTGRES_PASSWORD: str | None = "YOUR_POSTGRES_PASSWORD"

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