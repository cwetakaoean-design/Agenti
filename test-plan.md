# Test Plan — Agenti (PR #1)

App under test: local backend `http://localhost:8000` (FastAPI), mode `gigachat` (real GigaChat).
Goal: prove the agent pipeline produces real content via the UI and that revenue/state update correctly.

## Primary flow: create client → brief → run agents → view content → revenue updates

Pre-state: fresh DB (no clients, revenue 0 ₽, 0 orders). Badge top-right = "GigaChat: подключён".

| # | Action | Pass criteria (fails if broken) |
|---|--------|---------------------------------|
| 1 | Load `/`. Observe header badge + stats cards. | Badge text = "GigaChat: подключён" (green). Stats: Заработано `0 ₽`, Выполнено `0`, Всего `0`. Orders panel shows "Заказов пока нет." |
| 2 | In "1. Клиент": name `Клиника Улыбка`, industry `стоматология`, voice `тёплый, экспертный`. Click "Добавить клиента". | Toast "Клиент добавлен". Client appears in `#order-client` dropdown as "Клиника Улыбка · стоматология". |
| 3 | In "2. Бриф": select that client; type = "Пост для соцсетей — 1 500 ₽"; topic `Акция: имплантация под ключ`; brief `Аудитория 30-50 лет, подчеркнуть рассрочку`. Click "Создать заказ". | Toast "Заказ создан". New order card shows topic, "Клиника Улыбка · Пост для соцсетей", badge "новый", price `1 500 ₽`. Stat "В работе (потенциал)" = `1 500 ₽`, "Всего заказов" = `1`, "Заработано" still `0 ₽`. |
| 4 | Click "▶ Запустить агентов" on the order. Wait for completion. | Button shows "Агенты работают…" while running. On finish: toast "Контент готов!". Order badge → "готово" (green). |
| 5 | Result panel auto-opens (or click "Посмотреть контент"). | Panel shows three non-empty blocks: 🧭 Стратегия, ✦ Финальный контент, 📝 Черновик. Final content is a real Russian social post about имплантация (NOT the offline stub text "[offline-демо]"). Footer shows "Модель: GigaChat…" with tokens > 0. |
| 6 | Observe stats after run. | "Заработано" = `1 500 ₽`, "Выполнено заказов" = `1`, "В работе (потенциал)" = `0 ₽`. |

## Adversarial notes
- A broken pipeline / LLM wiring would leave revenue at `0 ₽`, order stuck at "в работе"/"ошибка", or show empty/stub content → steps 4-6 catch this.
- Stub-mode regression check: final content containing "[offline-демо]" would mean GigaChat wasn't actually used → step 5 catches this.

## Out of scope
Article/newsletter variants (same code path), pricing edits, multi-client. Covered by unit tests.
