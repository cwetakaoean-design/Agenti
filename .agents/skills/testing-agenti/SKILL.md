---
name: testing-agenti
description: Test the Agenti AI content-agency dashboard end-to-end (add client, create order, run agent pipeline, verify revenue). Use when verifying Agenti UI or agent-pipeline changes.
---

# Testing Agenti (ИИ-агентство контента)

FastAPI backend + static dashboard. Agent pipeline: Strategist -> ContentWriter -> Editor, powered by GigaChat (with an offline `StubLLM` fallback).

## Run the app locally

```bash
cd backend
# Live GigaChat mode (requires GIGACHAT_AUTH_KEY in env):
GIGACHAT_AUTH_KEY="$GIGACHAT_AUTH_KEY" uv run uvicorn app.main:app --port 8000
# Offline/deterministic mode (no network, good for hermetic UI checks):
USE_STUB_LLM=true uv run uvicorn app.main:app --port 8000
```

Open http://localhost:8000. Header badge reads "GigaChat: подключён" in live mode. For a clean run, stop old server (`pkill -f uvicorn`) and delete `backend/agenti.db`.

## Lint & tests

```bash
cd backend
uv run ruff check .
uv run pytest        # tests force StubLLM via conftest, no network needed
```

## Primary E2E flow (UI)

1. Fill the **Клиент** form (name/industry/voice), click **Добавить клиента** -> toast "Клиент добавлен"; client appears in the order dropdown.
2. In **Бриф / заказ**: pick the client, pick content type (post 1500₽ / article 6000₽ / newsletter 3500₽), enter a topic, click **Создать заказ** -> order shows status `новый`; "В работе" stat = price.
3. Click **▶ Запустить агентов** -> button shows "Агенты работают…". On success the status becomes `готово` and a **Посмотреть контент** button appears.
4. Click **Посмотреть контент** -> modal shows Strategy / Draft / Final sections plus a `Модель: GigaChat:... · токенов:` footer (real output, not stub).
5. Verify stats: Заработано = sum of done orders, Выполнено = count, В работе = pending only.

Verify backend state directly: `curl -s localhost:8000/api/revenue` and `/api/orders`.

## Gotchas

- **Cyrillic text input fails with the computer `type` action** (drops Cyrillic chars, leaving only spaces/punctuation). Workaround: install `xclip`, set the clipboard from the shell, then paste with Ctrl+V:
  ```bash
  printf '%s' "Клиника Улыбка" | DISPLAY=:0 xclip -selection clipboard
  ```
  Then click the field and send `ctrl+v` via the computer tool.
- **GigaChat may throw a transient TLS handshake timeout** (`_ssl.c:983: The handshake operation timed out`) reaching `gigachat.devices.sberbank.ru`. This is flaky network, not an app bug — **simply click Запустить агентов again**; the retry usually succeeds. Confirm connectivity from the shell with `curl -sv -k https://gigachat.devices.sberbank.ru/api/v1/chat/completions` (expect HTTP 401 without a token).
- A failed run correctly marks the order `ошибка` (not stuck `in_progress`) and excludes it from pipeline revenue — this is the intended error-handling behavior, good to verify as a regression.
- GigaChat's TLS chain uses the Russian Минцифры root CA; the app defaults to `GIGACHAT_VERIFY_TLS=false` for dev, so plain `curl` to the OAuth endpoint shows a self-signed-CA error that the app does not.

## Devin Secrets Needed

- `GIGACHAT_AUTH_KEY` — base64 `client_id:secret` from Сбер; required for live GigaChat mode. Not needed for stub mode or unit tests.
