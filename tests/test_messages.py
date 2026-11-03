import pytest

from repetitor_bot.bot import get_reset_keyboard, markdown_to_html, send_long_message


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("", ""),
        ("Обычный текст", "Обычный текст"),
        ("**жирный**", "<b>жирный</b>"),
        ("__жирный__", "<b>жирный</b>"),
        ("*курсив*", "<i>курсив</i>"),
        ("_курсив_", "<i>курсив</i>"),
        ("`code`", "<code>code</code>"),
        ("a & b", "a &amp; b"),
        ('"пример"', "&quot;пример&quot;"),
        ("<b>текст</b>", "<b>текст</b>"),
    ],
)
def test_markdown_conversion(text, expected):
    assert markdown_to_html(text) == expected


def test_reset_keyboard():
    keyboard = get_reset_keyboard()
    assert keyboard.keyboard[0][0].text == "Начать с начала"
    assert keyboard.resize_keyboard is True
    assert keyboard.one_time_keyboard is False


@pytest.mark.parametrize("length", [0, 1, 4096, 4097, 9000])
@pytest.mark.parametrize("reset", [False, True])
async def test_chunk_boundaries_and_keyboard(message, length, reset):
    text = "я" * length
    await send_long_message(message, text, include_reset_button=reset)

    calls = message.answer.call_args_list
    assert len(calls) == (length + 4095) // 4096
    assert "".join(call.args[0] for call in calls) == text
    for index, call in enumerate(calls):
        assert len(call.args[0]) <= 4096
        assert call.kwargs["parse_mode"] == "HTML"
        assert ("reply_markup" in call.kwargs) == (reset and index == len(calls) - 1)


@pytest.mark.parametrize("reset", [False, True])
async def test_failed_html_send_falls_back_to_original_text(message, reset):
    message.answer.side_effect = [RuntimeError("Invalid HTML"), None]
    await send_long_message(message, "**текст**", include_reset_button=reset)

    first, fallback = message.answer.call_args_list
    assert first.args == ("<b>текст</b>",)
    assert fallback.args == ("**текст**",)
    assert fallback.kwargs["parse_mode"] is None
    assert ("reply_markup" in fallback.kwargs) == reset


async def test_plain_text_send_error_propagates(message):
    message.answer.side_effect = RuntimeError("Telegram unavailable")
    with pytest.raises(RuntimeError, match="Telegram unavailable"):
        await send_long_message(message, "текст")
