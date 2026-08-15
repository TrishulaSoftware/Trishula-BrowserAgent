# 🔱 Trishula-BrowserAgent

**Sovereign Autonomous Web Browser Agent**

Trishula-BrowserAgent is a doctrine-gated web intelligence agent built on [browser-use](https://github.com/browser-use/browser-use). It controls real browsers via the Chrome DevTools Protocol (CDP) using natural language — navigating, clicking, extracting, and indexing web content into sovereign vector memory.

## Features

- 🌐 **CDP-native browser control** — no fragile CSS selectors, direct DOM awareness
- 🔒 **Tizona SOCKS5 proxy airlock** — all requests routed through ports 1080–1083
- 🛡️ **Rule 3 kinetic gate** — form submissions, payments, and deletions hard-blocked
- 🔍 **PII auto-scan** — SSN, credit card, phone, email detected and redacted before archiving
- 📦 **Qdrant indexing** — clean extractions automatically indexed to vector memory
- 📋 **Full audit trail** — shadow snapshot + JSONL ledger on every operation

## Quick Start

```bash
pip install trishula-browseragent
pip install browser-use
playwright install chromium
```

```python
from trishula_browser_agent import TrishulaBrowserAgent
import asyncio

agent = TrishulaBrowserAgent(dry_run=True)

result = asyncio.run(agent.extract(
    url="https://example.com/sports-data",
    task="Get the injury report table and all player statuses"
))

print(result["content"])
print(result["pii_clean"])   # True if no PII detected
```

## Safety Controls

| Control | Behavior |
|---|---|
| **Kinetic Gate** | Blocks: submit_form, confirm_payment, send_email, delete_account |
| **PII Scanner** | Redacts SSN, credit cards, emails, phone numbers before Qdrant index |
| **SOCKS5 Proxy** | All browser traffic routed through Tizona airlock |
| **Dry-Run Default** | Navigation previewed without executing (`dry_run=True`) |
| **Rule 0** | Pre-extraction shadow snapshot |
| **Rule 1** | JSONL ledger receipt on every extraction |

## Requirements

- Python 3.10+
- `pip install browser-use`
- `playwright install chromium`
- [Ollama](https://ollama.com) or OpenAI-compatible endpoint
- [Qdrant](https://qdrant.tech) (optional, for vector indexing)

## License

MIT — see [LICENSE](LICENSE)
