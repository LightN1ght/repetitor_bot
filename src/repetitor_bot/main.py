"""Application entry point."""

import asyncio


async def main():
    from .bot import bot, dp

    print("Bot started...")
    await dp.start_polling(bot)


def run():
    """Start the bot's event loop."""
    asyncio.run(main())


if __name__ == "__main__":
    run()
