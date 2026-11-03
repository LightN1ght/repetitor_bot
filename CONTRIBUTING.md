# Разработка

## Подготовка

Создайте виртуальное окружение и установите зависимости:

```bash
python -m pip install -r requirements-dev.txt
```

Перед коммитом выполните:

```bash
python -m ruff check .
python -m pytest --cov --cov-report=term-missing
python -m build
```

Новые тесты должны работать без настоящих ключей и сетевых запросов.
Runtime-код находится в `src/repetitor_bot`, тесты — в `tests`.

## Gitflow

| Ветка | Назначение | Откуда создаётся | Куда вливается |
| --- | --- | --- | --- |
| `main` | Стабильные релизы | — | — |
| `develop` | Интеграция изменений | `main` при первоначальной настройке | через `release/*` в `main` |
| `feature/*` | Отдельная задача | `develop` | `develop` |
| `release/*` | Подготовка версии | `develop` | `main` и `develop` |
| `hotfix/*` | Срочное исправление релиза | `main` | `main` и `develop` |

Не отправляйте изменения напрямую в `main`. Проводите изменения через pull request
и дожидайтесь зелёного CI. Для сохранения ветвления Gitflow используйте merge commit.
Настройки защиты веток задаются отдельно в GitHub; наличие этого документа их не включает.

### Работа над задачей

```bash
git switch develop
git pull --ff-only origin develop
git switch -c feature/short-description
# внесите изменения и выполните проверки
git add <files>
git commit -m "refactor: describe the change"
git push -u origin feature/short-description
gh pr create --base develop --head feature/short-description
```

После проверки влейте PR в `develop` с merge commit, затем обновите локальную ветку.
Удобные префиксы коммитов: `feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `ci:`, `chore:`.

### Релиз

```bash
git switch develop
git pull --ff-only origin develop
git switch -c release/0.1.0
# обновите версию в pyproject.toml при необходимости и выполните проверки
git push -u origin release/0.1.0
gh pr create --base main --head release/0.1.0
```

После слияния релизного PR в `main`:

```bash
git switch main
git pull --ff-only origin main
git tag -a v0.1.0 -m "Release 0.1.0"
git push origin v0.1.0
gh pr create --base develop --head main
```

Последний PR возвращает релизные изменения в `develop`. Если расхождений нет,
дополнительное слияние не требуется. Номер ветки, версия пакета и тег должны совпадать.

### Срочное исправление

Создайте `hotfix/short-description` от актуального `main`, внесите исправление,
обновите версию и выполните проверки. Откройте PR в `main`, после слияния поставьте
новый тег и верните изменения из `main` в `develop` отдельным PR.

## Автор коммитов

Проверьте локальные настройки перед коммитом:

```bash
git config user.name
git config user.email
```

Email должен быть привязан к вашему GitHub-аккаунту либо быть его GitHub noreply-адресом.
Авторизация `gh` и авторство Git-коммитов настраиваются независимо.
