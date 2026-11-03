"""Offline fixtures: no real credentials or API requests are needed."""

import os
import socket
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage

# Set before test modules import the application, even if a local .env exists.
os.environ["BOT_TOKEN"] = "123456789:offline-test-token"
os.environ["GEMINI_API_KEY"] = "offline-test-key"


@pytest.fixture(autouse=True)
def block_network(monkeypatch):
    original_connect = socket.socket.connect
    original_connect_ex = socket.socket.connect_ex

    def guard(method):
        def connect(sock, address):
            # Windows asyncio uses a loopback socket pair for its event loop.
            if isinstance(address, tuple) and address[0] in {"127.0.0.1", "::1"}:
                return method(sock, address)
            raise AssertionError("Tests must not access external services")

        return connect

    monkeypatch.setattr(socket.socket, "connect", guard(original_connect))
    monkeypatch.setattr(socket.socket, "connect_ex", guard(original_connect_ex))


@pytest.fixture
def message():
    return SimpleNamespace(
        from_user=SimpleNamespace(id=42),
        chat=SimpleNamespace(id=42),
        text="Тест",
        answer=AsyncMock(return_value=SimpleNamespace(message_id=99)),
    )


@pytest.fixture
async def state():
    storage = MemoryStorage()
    context = FSMContext(storage=storage, key=StorageKey(bot_id=123456789, chat_id=42, user_id=42))
    yield context
    await storage.close()


@pytest.fixture
def app(monkeypatch):
    from repetitor_bot import bot

    bot.user_classes.clear()
    monkeypatch.setattr(bot, "ask_gemini_with_history", lambda history: "Ответ репетитора")
    monkeypatch.setattr(bot.bot, "delete_message", AsyncMock())
    yield bot
    bot.user_classes.clear()
