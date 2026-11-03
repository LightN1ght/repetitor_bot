import runpy
from unittest.mock import AsyncMock, Mock

from repetitor_bot import main


async def test_main_starts_polling(app, monkeypatch, capsys):
    polling = AsyncMock()
    monkeypatch.setattr(app.dp, "start_polling", polling)
    await main.main()
    polling.assert_awaited_once_with(app.bot)
    assert capsys.readouterr().out == "Bot started...\n"


def test_console_entry_point_runs_event_loop(monkeypatch):
    coroutine = object()
    monkeypatch.setattr(main, "main", Mock(return_value=coroutine))
    run = Mock()
    monkeypatch.setattr(main.asyncio, "run", run)
    main.run()
    run.assert_called_once_with(coroutine)


def test_module_entry_point(monkeypatch):
    run = Mock()
    monkeypatch.setattr(main, "run", run)
    runpy.run_module("repetitor_bot", run_name="__main__")
    run.assert_called_once_with()
