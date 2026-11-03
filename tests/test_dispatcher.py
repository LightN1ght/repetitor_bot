"""Exercise real aiogram routing and storage with Telegram calls replaced."""

from datetime import datetime, timezone

from aiogram import Bot
from aiogram.methods import SendMessage
from aiogram.types import Chat, Message, MessageEntity, Update, User

from repetitor_bot.states import StudyStates


async def test_full_lesson_routing_and_user_isolation(app, monkeypatch):
    sent = []

    async def telegram_call(self, method, **kwargs):
        assert isinstance(method, SendMessage)
        sent.append(method)
        return Message(
            message_id=len(sent),
            date=datetime.now(timezone.utc),
            chat=Chat(id=method.chat_id, type="private"),
            text=method.text,
        )

    monkeypatch.setattr(Bot, "__call__", telegram_call)

    async def send(user_id, text):
        entities = (
            [MessageEntity(type="bot_command", offset=0, length=len(text))]
            if text.startswith("/") else None
        )
        update = Update(
            update_id=len(sent) + 1,
            message=Message(
                message_id=len(sent) + 1,
                date=datetime.now(timezone.utc),
                chat=Chat(id=user_id, type="private"),
                from_user=User(id=user_id, is_bot=False, first_name="Ученик"),
                text=text,
                entities=entities,
            ),
        )
        await app.dp.feed_update(app.bot, update)

    try:
        await send(101, "/start")
        await send(101, "7")
        await send(202, "/start")
        await send(202, "9")
        await send(101, "Математика")
        await send(101, "Дроби")

        first = app.dp.fsm.get_context(bot=app.bot, chat_id=101, user_id=101)
        second = app.dp.fsm.get_context(bot=app.bot, chat_id=202, user_id=202)
        assert await first.get_state() == StudyStates.in_learning.state
        assert await second.get_state() == StudyStates.waiting_for_subject.state
        assert (await first.get_data())["subject"] == "Математика"
        assert await second.get_data() == {"user_class": "9"}
        assert app.user_classes == {101: "7", 202: "9"}

        await send(101, "Одна вторая")
        history = (await first.get_data())["history"]
        assert [item["role"] for item in history] == ["user", "model", "user", "model"]
        assert history[-2]["content"] == "Одна вторая"

        await send(101, "/restart")
        assert await first.get_state() == StudyStates.waiting_for_class.state
        assert await first.get_data() == {}
        assert sent[-1].reply_markup.keyboard[0][0].text == "7"

        # /start is registered before the state handlers and resets an unfinished lesson.
        await send(202, "/start")
        assert await second.get_state() == StudyStates.waiting_for_class.state
        assert await second.get_data() == {}
        assert sent[-1].reply_markup.keyboard[0][0].text == "9"
    finally:
        await app.dp.storage.close()
