from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from repetitor_bot import ai


@pytest.fixture
def generate(monkeypatch):
    client = Mock()
    monkeypatch.setattr(ai, "client", client)
    return client.models.generate_content


@pytest.mark.parametrize(
    ("history", "prompt"),
    [
        ([], ""),
        ([{"role": "user", "content": "Вопрос"}], "Пользователь: Вопрос"),
        (
            [{"role": "user", "content": "Вопрос"}, {"role": "model", "content": "Ответ"}],
            "Пользователь: Вопрос\nИИ: Ответ",
        ),
        ([{}, {"role": "other"}], "Пользователь: \nИИ: "),
    ],
)
def test_serializes_history_without_mutating_it(generate, history, prompt):
    original = [item.copy() for item in history]
    generate.return_value = SimpleNamespace(text="Объяснение")

    assert ai.ask_gemini_with_history(history) == "Объяснение"
    generate.assert_called_once_with(model="gemini-3-flash-preview", contents=prompt)
    assert history == original


@pytest.mark.parametrize("response", [None, SimpleNamespace(text=None), SimpleNamespace(text="")])
def test_empty_response(generate, response):
    generate.return_value = response
    assert ai.ask_gemini_with_history([]) == "Пустой ответ от Gemini 😢"


def test_api_error_is_returned_as_text(generate):
    generate.side_effect = RuntimeError("service unavailable")
    assert ai.ask_gemini_with_history([]) == "Ошибка Gemini: service unavailable"
