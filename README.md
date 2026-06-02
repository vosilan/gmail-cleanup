# Gmail Cleanup

Инструмент для автоматической чистки Gmail: удаляет промо-рассылки и спам, отписывается от ненужных листов, защищает важные письма (чеки, заказы, бронирования).

*A tool for automated Gmail cleanup: trashes promo newsletters and spam, auto-unsubscribes, and protects important emails (receipts, orders, bookings).*

---

## Установка / Setup

```bash
pip install google-api-python-client google-auth-oauthlib requests
```

Скопируй `credentials.json.example` → `credentials.json` и заполни своими данными из [Google Cloud Console](https://console.cloud.google.com/):

1. Создай проект → включи Gmail API
2. Создай OAuth-credentials (тип: Desktop app)
3. Скачай как `credentials.json` и положи рядом со скриптом

*Copy `credentials.json.example` → `credentials.json` and fill in your credentials from [Google Cloud Console](https://console.cloud.google.com/):*

1. *Create a project → enable Gmail API*
2. *Create OAuth credentials (Desktop app)*
3. *Download as `credentials.json` and place next to the script*

---

## Запуск / Usage

```bash
# Превью — ничего не удаляет / Preview — nothing is changed
python cleanup.py --dry-run

# Чистка + отписка от рассылок / Cleanup + unsubscribe
python cleanup.py

# Только чистка, без отписки / Cleanup only, skip unsubscribe
python cleanup.py --no-unsubscribe
```

---

## Что делает / What it does

- Ищет письма в категориях `promotions`, `updates`, `spam`
- Удаляет письма от конкретных отправителей из `TRASH_SENDERS`
- Отписывается через заголовок `List-Unsubscribe` (mailto или HTTP POST/GET)
- **Пропускает** письма с ключевыми словами из `SAFETY_KEYWORDS`

---

## Настройка / Configuration

Все параметры — в начале `cleanup.py`:

```python
# Поисковые запросы / Search queries
SEARCH_QUERIES = [
    "category:promotions in:inbox",
    "category:updates in:inbox",
    "in:spam",
]

# Конкретные отправители для удаления / Specific senders to trash
TRASH_SENDERS = [
    "news.ozon.ru",
    "newsletter.trip.com",
    # ...
]

# Ключевые слова — такие письма никогда не удаляются
# Safety keywords — emails with these in subject are never trashed
SAFETY_KEYWORDS = [
    "receipt", "invoice", "order", "чек", "квитанция", "заказ",
    # ...
]

# Домены, письма с которых никогда не удаляются
# Sender domains that are always protected
SAFE_SENDERS = [
    # "tinkoff.ru",
]
```

---

## Безопасность / Safety

Скрипт **никогда не удаляет** письма, если в теме есть:

`receipt` · `invoice` · `order` · `booking` · `confirmation` · `ticket` · `2fa` · `password reset` · `чек` · `квитанция` · `заказ` · `оплата` · `подтверждение` · `бронирование` · `билет` · `транзакция` · `перевод` · `списание`

---

## Файлы / Files

```
cleanup.py               — основной скрипт / main script
credentials.json.example — шаблон OAuth-credentials / OAuth credentials template
.gitignore               — credentials.json и token.pickle исключены из git
```
