# Gmail Cleanup Agent

Your task: find and trash unwanted emails in Gmail using the available Gmail MCP tools.

## Configuration (edit these to customize)

```
TRASH_PROMOTIONS=true
TRASH_SPAM=true
TRASH_UPDATES=false
TRASH_SOCIAL=false
```

## What to trash

Search queries to use (based on config above):
- Promotions: `category:promotions in:inbox`
- Spam: `in:spam`
- Updates: `category:updates in:inbox`
- Social: `category:social in:inbox`

## Safety rules — NEVER trash if subject contains:

invoice, receipt, order, shipping, payment, booking, confirmation,
reservation, ticket, password reset, verification, 2FA, security alert,
код подтверждения, подтверждение заказа, накладная, счёт, оплата

## Execution steps

1. Call `list_labels` to get the TRASH label ID (look for a label with name "TRASH" or type "system")

2. For each ENABLED category:
   a. Call `search_threads` with the query, maxResults=50
   b. For each thread returned:
      - Check thread subject against safety rules above
      - If subject matches a safety rule → SKIP, log "SKIPPED (safety): [subject]"
      - If subject is safe → call `label_thread` with TRASH label ID
      - Log "TRASHED: [subject]"
   c. If there are more pages (nextPageToken), repeat with the token until done

3. Final summary:
   - Total threads found
   - Total trashed
   - Total skipped (safety rules)
   - Breakdown by category

## Output format

Show live progress:
```
[Promotions] Searching...
  ✓ TRASHED: "50% off sale ends tonight!"
  ✓ TRASHED: "Weekly digest from ProductHunt"
  — SKIPPED: "Your order #12345 has shipped"
[Spam] Searching...
  ...

━━━━━━━━━━━━━━━━━━━━━━
Done! Trashed: 47 | Skipped: 3 | Searched: 50
```

Begin execution now. Use the Gmail MCP tools.
