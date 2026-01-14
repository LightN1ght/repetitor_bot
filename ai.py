from google import genai
from config import GEMINI_API_KEY

client = genai.Client(api_key=GEMINI_API_KEY)

MODEL_NAME = "gemini-3-flash-preview"

def ask_gemini_with_history(history: list[dict]) -> str:
    """
    history = [
        {"role": "user", "content": "..."},
        {"role": "model", "content": "..."},
        ...
    ]
    """
    # ✅ Конкатенируем историю в одну строку
    texts = []
    for msg in history:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "user":
            texts.append(f"Пользователь: {content}")
        else:
            texts.append(f"ИИ: {content}")

    full_prompt = "\n".join(texts)

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=full_prompt  # <- просто строка
        )

        if not response or not response.text:
            return "Пустой ответ от Gemini 😢"

        return response.text

    except Exception as e:
        return f"Ошибка Gemini: {e}"

