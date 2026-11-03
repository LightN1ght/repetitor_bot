import html
import re
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

from .config import BOT_TOKEN
from .ai import ask_gemini_with_history
from .states import StudyStates
from .prompts import build_start_prompt


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Dictionary to store user classes (in production, use a database)
user_classes = {}

def markdown_to_html(text: str) -> str:
    """Convert basic markdown formatting to HTML"""
    # Convert **bold** or __bold__ to <b>bold</b>
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'__(.*?)__', r'<b>\1</b>', text)

    # Convert *italic* or _italic_ to <i>italic</i>
    text = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<i>\1</i>', text)
    text = re.sub(r'(?<!_)_([^_]+)_(?![^<]*>)', r'<i>\1</i>', text)

    # Convert `code` to <code>code</code>
    text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)

    # Convert ```code block``` to <pre>code block</pre>
    text = re.sub(r'```([\s\S]*?)```', r'<pre>\1</pre>', text)

    # Escape remaining special HTML characters, but leave HTML tags intact
    # Split by HTML tags, escape non-tag parts, then recombine
    parts = re.split(r'(<[^>]+>)', text)
    for i in range(len(parts)):
        if not parts[i].startswith('<'):
            parts[i] = html.escape(parts[i])

    return ''.join(parts)

def get_reset_keyboard():
    """Create a keyboard with reset button"""
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="Начать с начала")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False  # Keep the keyboard visible
    )

async def send_long_message(message, text: str, include_reset_button=False):

    if not text:
        return


    MAX_LEN = 4096  # Telegram's max message length is 4096
    for i in range(0, len(text), MAX_LEN):
        chunk = text[i:i + MAX_LEN]

        # For the last chunk, we can add the reset button if needed
        is_last_chunk = (i + MAX_LEN >= len(text))

        # Try HTML parse mode which is more forgiving for special characters
        # HTML escaping is safer and simpler
        try:
            # Convert markdown to HTML and escape remaining special characters
            converted_chunk = markdown_to_html(chunk)

            if is_last_chunk and include_reset_button:
                await message.answer(
                    converted_chunk,
                    reply_markup=get_reset_keyboard(),
                    parse_mode="HTML"
                )
            else:
                await message.answer(
                    converted_chunk,
                    parse_mode="HTML"
                )
        except Exception:
            # Fallback if HTML parsing also fails
            if is_last_chunk and include_reset_button:
                await message.answer(
                    chunk,
                    reply_markup=get_reset_keyboard(),
                    parse_mode=None
                )
            else:
                await message.answer(
                    chunk,
                    parse_mode=None
                )



@dp.message(CommandStart())
async def start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    # Remove any persistent keyboard when starting fresh
    remove_keyboard = types.ReplyKeyboardRemove()

    # Check if we have a previously saved class for this user
    if user_id in user_classes:
        previous_class = user_classes[user_id]
        keyboard = types.ReplyKeyboardMarkup(keyboard=[
            [types.KeyboardButton(text=previous_class)]
        ], resize_keyboard=True, one_time_keyboard=True)
        await message.answer("Привет! В каком ты классе?", reply_markup=keyboard)
    else:
        await message.answer("Привет! В каком ты классе?", reply_markup=remove_keyboard)

    await state.clear()
    await state.set_state(StudyStates.waiting_for_class)


@dp.message(StudyStates.waiting_for_class)
async def process_class(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_classes[user_id] = message.text  # Save the class for this user

    await state.update_data(user_class=message.text)
    await message.answer("Какой предмет?")
    await state.set_state(StudyStates.waiting_for_subject)


@dp.message(StudyStates.waiting_for_subject)
async def process_subject(message: types.Message, state: FSMContext):
    await state.update_data(subject=message.text)
    await message.answer("Какую тему будем учить?")
    await state.set_state(StudyStates.waiting_for_topic)


@dp.message(StudyStates.waiting_for_topic)
async def process_topic(message: types.Message, state: FSMContext):
    await state.update_data(topic=message.text)

    data = await state.get_data()
    user_class = data["user_class"]
    subject = data["subject"]
    topic = data["topic"]

    await message.answer("Отлично! Начинаем занятие")

    system_prompt = build_start_prompt(user_class, subject, topic)

    history = [
        {"role": "user", "content": system_prompt}
    ]

    # Send thinking message and store it for deletion
    thinking_msg = await message.answer("Думаю...")

    answer = ask_gemini_with_history(history)

    # Delete the thinking message
    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=thinking_msg.message_id)
    except:
        pass  # Message might have already been deleted or expired

    history.append({"role": "model", "content": answer})

    await state.update_data(history=history)

    await send_long_message(message, answer, include_reset_button=True)

    await state.set_state(StudyStates.in_learning)


@dp.message(StudyStates.in_learning)
async def learning_mode(message: types.Message, state: FSMContext):
    # If user sends the restart command, handle it separately
    if message.text == "/restart" or message.text == "Начать с начала":
        await restart_handler(message, state)
        return

    data = await state.get_data()
    history = data.get("history", [])

    history.append({"role": "user", "content": message.text})

    # Send thinking message and store it for deletion
    thinking_msg = await message.answer("Думаю...")

    answer = ask_gemini_with_history(history)

    # Delete the thinking message
    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=thinking_msg.message_id)
    except:
        pass  # Message might have already been deleted or expired

    history.append({"role": "model", "content": answer})

    await state.update_data(history=history)

    await send_long_message(message, answer, include_reset_button=True)



# Handler for the "Начать с начала" button
@dp.message(lambda message: message.text == "Начать с начала")
async def restart_handler(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    # Clear the state
    await state.clear()

    # Check if we have a previously saved class for this user
    if user_id in user_classes:
        previous_class = user_classes[user_id]
        keyboard = types.ReplyKeyboardMarkup(keyboard=[
            [types.KeyboardButton(text=previous_class)]
        ], resize_keyboard=True, one_time_keyboard=True)
        await message.answer("В каком ты классе?", reply_markup=keyboard)
    else:
        remove_keyboard = types.ReplyKeyboardRemove()
        await message.answer("В каком ты классе?", reply_markup=remove_keyboard)

    await state.set_state(StudyStates.waiting_for_class)


@dp.message(Command("restart"))
async def restart_command(message: types.Message, state: FSMContext):
    # Call the same handler for the command
    await restart_handler(message, state)
