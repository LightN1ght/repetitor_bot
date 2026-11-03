import importlib

from repetitor_bot import config


def test_configuration_uses_environment_over_dotenv(monkeypatch):
    with monkeypatch.context() as env:
        env.setenv("BOT_TOKEN", "environment-bot-token")
        env.setenv("GEMINI_API_KEY", "environment-api-key")
        importlib.reload(config)
        assert config.BOT_TOKEN == "environment-bot-token"
        assert config.GEMINI_API_KEY == "environment-api-key"
    importlib.reload(config)
