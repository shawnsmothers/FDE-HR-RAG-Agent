from app.core.config import get_settings

settings = get_settings()
print(f"App Name: {settings.app_name}")
print(f"openai api key: {settings.openai_api_key}")

