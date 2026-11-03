# Repetitor Bot

[![CI](https://github.com/LightN1ght/repetitor_bot/actions/workflows/ci.yml/badge.svg?branch=develop)](https://github.com/LightN1ght/repetitor_bot/actions/workflows/ci.yml)

Телеграм-бот-репетитор на Python, aiogram и Google Gemini. Ученик выбирает класс,
предмет и тему, после чего бот объясняет материал и задаёт вопросы с учётом истории
текущего занятия.

## Что умеет

- Начинает диалог по команде `/start`: класс → предмет → тема → занятие.
- Передаёт историю переписки в Gemini (`gemini-3-flash-preview`).
- Предлагает начать занятие заново кнопкой «Начать с начала» или командой `/restart`.
- Запоминает последний введённый класс до перезапуска процесса.
- Делит длинные ответы на сообщения и повторяет отправку обычным текстом при ошибке HTML.

## Быстрый старт

Нужны Python 3.11+, токен Telegram-бота от [BotFather](https://t.me/BotFather)
и ключ [Gemini API](https://aistudio.google.com/apikey).
Запускайте команды из корня репозитория.

```bash
git clone https://github.com/LightN1ght/repetitor_bot.git
cd repetitor_bot
python -m venv .venv
```

Активируйте окружение:

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

```bash
# Linux / macOS
source .venv/bin/activate
```

Установите проект с исходными зафиксированными зависимостями:

```bash
python -m pip install -r requirements.txt
python -m pip install -e .
```

Скопируйте `.env.example` в `.env`:

```powershell
# Windows PowerShell
Copy-Item .env.example .env
```

```bash
# Linux / macOS
cp .env.example .env
```

Заполните `.env`:

```dotenv
BOT_TOKEN=your_telegram_bot_token
GEMINI_API_KEY=your_gemini_api_key
```

| Переменная | Назначение |
| --- | --- |
| `BOT_TOKEN` | Токен Telegram-бота |
| `GEMINI_API_KEY` | Ключ доступа к Gemini API |

Переменные можно передать и через окружение процесса; они имеют приоритет над `.env`.
Реальные ключи не добавляются в Git.

Запустите бота одним из способов:

```bash
python -m repetitor_bot
# или
repetitor-bot
# или из корня установленного проекта
python main.py
```

Бот использует long polling. Остановить его можно сочетанием `Ctrl+C`.
Прежний запуск через `python bot.py` заменён командами выше.

## Структура

```text
.
├── .github/
│   ├── workflows/ci.yml   # Проверки push и pull request
│   └── pull_request_template.md
├── src/repetitor_bot/
│   ├── __init__.py
│   ├── __main__.py        # python -m repetitor_bot
│   ├── main.py            # Запуск polling и консольная команда
│   ├── bot.py             # Обработчики, форматирование и отправка сообщений
│   ├── ai.py              # Запрос к Gemini с историей
│   ├── config.py          # Загрузка переменных окружения
│   ├── prompts.py         # Исходный промпт репетитора
│   └── states.py          # Состояния диалога
├── tests/                 # Автономные тесты без сетевых запросов
├── .env.example
├── CONTRIBUTING.md        # Gitflow и порядок внесения изменений
├── main.py                # Запуск из корня проекта
├── pyproject.toml         # Пакет, точка входа и настройки проверок
├── requirements.txt       # Исходный список зависимостей с точными версиями
└── requirements-dev.txt   # Зависимости проекта и инструменты разработки
```

## Разработка и проверки

```bash
python -m pip install -r requirements-dev.txt
python -m pytest --cov --cov-report=term-missing
python -m ruff check .
python -m build
```

Тесты используют фиктивные ключи и подставные ответы Telegram/Gemini. Они проверяют
сценарий занятия, изоляцию пользователей, сброс, историю, ошибки Gemini,
форматирование, разбиение сообщений и запуск приложения. Подключения к внешним
сервисам в тестах запрещены. Минимальное покрытие — 90% строк кода.

GitHub Actions запускает линтер, тесты с покрытием и сборку пакета
на Python 3.11, 3.12 и 3.13, а затем проверяет установку wheel и запуск его точки входа
с подставленным polling.

Рабочая схема: `feature/*` → `develop` → `release/*` → `main`.
Подробные команды, правила для исправлений и релизов — в [CONTRIBUTING.md](CONTRIBUTING.md).

## Текущее поведение и ограничения

При реорганизации сохранены исходная логика, тексты, промпт, модель Gemini и версии
runtime-зависимостей. Добавлены структура пакета, точки запуска, документация и проверки.

- Состояния, история и классы хранятся в памяти и теряются при перезапуске.
- Вызов Gemini синхронный внутри асинхронного обработчика: ожидание ответа может
  задерживать обработку других сообщений.
- Текущая модель Gemini — preview; доступность модели зависит от Google и аккаунта.
- Диалог рассчитан на текстовые сообщения. Проверка ввода и постоянное хранилище не добавлены.
- Во время выбора класса, предмета или темы обработчик текущего состояния может
  принять `/restart` или текст кнопки за ответ. В режиме занятия сброс работает как раньше;
  `/start` позволяет начать диалог заново на любом этапе.
- Сохранён простой конвертер Markdown и разбиение по 4096 символов. Они не учитывают
  границы HTML-тегов; при ошибке разметки бот отправляет исходный текст.

Тесты не подтверждают доступность внешних сервисов: реальный запуск требует своих
ключей и доступа к Telegram и Gemini.
