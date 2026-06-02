# Gmail Cleanup

Инструмент для автоматической чистки Gmail: удаляет промо-рассылки и спам, отписывается от ненужных листов, защищает важные письма (чеки, заказы, бронирования).

*A tool for automated Gmail cleanup: trashes promo newsletters and spam, auto-unsubscribes, and protects important emails (receipts, orders, bookings).*

---

## Два режима / Two modes

| | Python-скрипт | AI-агент |
|---|---|---|
| Файл | `cleanup.py` | `run.sh` + `cleanup_agent.md` |
| Требует | Gmail API OAuth | Claude Code CLI + Gmail MCP |
| Скорость | Быстро (API) | Медленнее (LLM) |
| Гибкость | Правила в коде | Можно менять промпт |

---

## Python-скрипт (`cleanup.py`)

### Установка

```bash
pip install google-api-python-client google-auth-oauthlib requests
```

Скопируй `credentials.json.example` → `credentials.json` и заполни своими данными из [Google Cloud Console](https://console.cloud.google.com/):
1. Создай проект → включи Gmail API
2. Создай OAuth-credentials (Desktop app)
3. Скачай как `credentials.json` и положи рядом со скриптом

### Запуск

```bash
# Превью — ничего не удаляет
python cleanup.py --dry-run

# Чистка + отписка от рассылок
python cleanup.py

# Только чистка, без отписки
python cleanup.py --no-unsubscribe
```

### Что делает

- Ищет письма по категориям: `promotions`, `updates`, `spam`
- Удаляет письма от отправителей из списка `TRASH_SENDERS`
- Отписывается через `List-Unsubscribe` (mailto или HTTP)
- **Пропускает** письма с ключевыми словами из `SAFETY_KEYWORDS`

### Настройка (`cleanup.py`)

```python
# Поисковые запросы
SEARCH_QUERIES = [
    "category:promotions in:inbox",
    "category:updates in:inbox",
    "in:spam",
]

# Конкретные отправители для удаления
TRASH_SENDERS = [
    "news.ozon.ru",
    "newsletter.trip.com",
    # ...
]

# Ключевые слова — такие письма никогда не удаляются
SAFETY_KEYWORDS = [
    "receipt", "invoice", "order", "чек", "квитанция", "заказ",
    # ...
]

# Домены, письма с которых никогда не удаляются
SAFE_SENDERS = [
    # "tinkoff.ru",
    # "sberbank.ru",
]
```

---

## AI-агент (`run.sh`)

Запускает Claude Code как агента, который чистит почту через Gmail MCP.

### Требования

- [Claude Code CLI](https://claude.ai/code) (`claude`)
- Gmail MCP, подключённый в настройках Claude Code

### Запуск

```bash
./run.sh
```

Агент сам ищет письма, проверяет тему по правилам безопасности и перемещает в корзину. Живой прогресс в терминале.

Настроить категории можно в `cleanup_agent.md`:

```
TRASH_PROMOTIONS=true
TRASH_SPAM=true
TRASH_UPDATES=false
TRASH_SOCIAL=false
```

---

## Безопасность / Safety

Оба режима **никогда не удаляют** письма, если в теме есть:

`receipt` · `invoice` · `order` · `booking` · `confirmation` · `ticket` · `2fa` · `password reset` · `чек` · `квитанция` · `заказ` · `оплата` · `подтверждение` · `бронирование` · `билет` · `транзакция` · `перевод` · `списание`

---

## Файлы / Files

```
cleanup.py              — основной Python-скрипт
run.sh                  — запуск AI-агента
cleanup_agent.md        — промпт для AI-агента
credentials.json.example — шаблон OAuth-credentials
.gitignore              — credentials.json и token.pickle исключены из git
```
