from unittest.mock import Mock

import pytest
from aiogram.types import ReplyKeyboardRemove

from repetitor_bot.prompts import build_start_prompt
from repetitor_bot.states import StudyStates


@pytest.mark.parametrize("previous_class", [None, "7"])
async def test_start_clears_lesson_and_suggests_saved_class(app, message, state, previous_class):
    await state.update_data(history=[{"role": "model", "content": "old"}])
    if previous_class:
        app.user_classes[42] = previous_class

    await app.start(message, state)

    assert await state.get_state() == StudyStates.waiting_for_class.state
    assert await state.get_data() == {}
    assert message.answer.call_args.args == ("Привет! В каком ты классе?",)
    keyboard = message.answer.call_args.kwargs["reply_markup"]
    if previous_class:
        assert keyboard.keyboard[0][0].text == previous_class
    else:
        assert isinstance(keyboard, ReplyKeyboardRemove)


async def test_class_and_subject_transitions(app, message, state):
    message.text = "7"
    await app.process_class(message, state)
    assert app.user_classes == {42: "7"}
    assert await state.get_data() == {"user_class": "7"}
    assert await state.get_state() == StudyStates.waiting_for_subject.state
    message.answer.assert_awaited_with("Какой предмет?")

    message.text = "Математика"
    await app.process_subject(message, state)
    assert await state.get_data() == {"user_class": "7", "subject": "Математика"}
    assert await state.get_state() == StudyStates.waiting_for_topic.state
    message.answer.assert_awaited_with("Какую тему будем учить?")


@pytest.mark.parametrize("delete_fails", [False, True])
async def test_topic_starts_lesson_and_saves_history(app, message, state, monkeypatch, delete_fails):
    await state.update_data(user_class="7", subject="Математика")
    message.text = "Дроби"
    ask = Mock(return_value="Объяснение дробей")
    monkeypatch.setattr(app, "ask_gemini_with_history", ask)
    if delete_fails:
        app.bot.delete_message.side_effect = RuntimeError("Message expired")

    await app.process_topic(message, state)

    data = await state.get_data()
    assert data["topic"] == "Дроби"
    assert data["history"] == [
        {"role": "user", "content": build_start_prompt("7", "Математика", "Дроби")},
        {"role": "model", "content": "Объяснение дробей"},
    ]
    ask.assert_called_once()
    assert await state.get_state() == StudyStates.in_learning.state
    app.bot.delete_message.assert_awaited_once_with(chat_id=42, message_id=99)
    assert [call.args[0] for call in message.answer.call_args_list] == [
        "Отлично! Начинаем занятие", "Думаю...", "Объяснение дробей"
    ]
    assert message.answer.call_args.kwargs["reply_markup"].keyboard[0][0].text == "Начать с начала"


@pytest.mark.parametrize("delete_fails", [False, True])
@pytest.mark.parametrize("has_history", [False, True])
async def test_learning_appends_turns(app, message, state, monkeypatch, delete_fails, has_history):
    original = [{"role": "model", "content": "Предыдущий вопрос"}] if has_history else []
    await state.update_data(history=original.copy())
    message.text = "Ответ ученика"
    seen = []

    def ask(history):
        seen.extend(item.copy() for item in history)
        return "Следующий вопрос"

    monkeypatch.setattr(app, "ask_gemini_with_history", ask)
    if delete_fails:
        app.bot.delete_message.side_effect = RuntimeError("Message expired")

    await app.learning_mode(message, state)

    assert seen == original + [{"role": "user", "content": "Ответ ученика"}]
    assert (await state.get_data())["history"] == seen + [
        {"role": "model", "content": "Следующий вопрос"}
    ]
    assert message.answer.call_args.args == ("Следующий вопрос",)


@pytest.mark.parametrize("trigger", ["/restart", "Начать с начала"])
@pytest.mark.parametrize("previous_class", [None, "7"])
async def test_learning_restart(app, message, state, trigger, previous_class):
    await state.update_data(history=[{"role": "model", "content": "old"}])
    if previous_class:
        app.user_classes[42] = previous_class
    message.text = trigger

    await app.learning_mode(message, state)

    assert await state.get_data() == {}
    assert await state.get_state() == StudyStates.waiting_for_class.state
    assert message.answer.call_args.args == ("В каком ты классе?",)
    keyboard = message.answer.call_args.kwargs["reply_markup"]
    if previous_class:
        assert keyboard.keyboard[0][0].text == previous_class
    else:
        assert isinstance(keyboard, ReplyKeyboardRemove)


async def test_restart_command(app, message, state):
    await state.update_data(topic="old")
    await app.restart_command(message, state)
    assert await state.get_data() == {}
    assert await state.get_state() == StudyStates.waiting_for_class.state
