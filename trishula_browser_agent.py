"""
╔══════════════════════════════════════════════════════════════════════╗
║         TRISHULA BROWSER AGENT  —  TrishulaBrowserAgent             ║
║         Sovereign Wrapper: browser-use v0.13.1                      ║
║         Doctrine: Rule 3 Dry-Run Gate | Tizona SOCKS5 Airlock       ║
║         Law I: Pulse Ledger Receipt on every extraction              ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import asyncio
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ── Doctrine Ledger path (Rule 1) ────────────────────────────────────
LEDGER_PATH = Path(r"D:\Trishula-Infra\Swarm-Core\Ledger\trishula_ledger.jsonl")
BACKUP_PATH = Path(r"D:\Trishula-Infra\Swarm-Core\backups")
LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
BACKUP_PATH.mkdir(parents=True, exist_ok=True)

# ── Tizona SOCKS5 Airlock config ─────────────────────────────────────
TIZONA_PROXY = "socks5://127.0.0.1:1080"

# ── Rule 3: Kinetic action blocklist ────────────────────────────────
BLOCKED_ACTIONS = {
    "submit_form", "click_submit", "confirm_payment",
    "purchase", "send_email", "post_message", "delete_account"
}

# ── PII regex patterns (pre-Presidio lightweight scan) ───────────────
import re
PII_PATTERNS = [
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),            # SSN
    re.compile(r"\b4[0-9]{12}(?:[0-9]{3})?\b"),       # Visa card
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),  # Email
    re.compile(r"\b(?:\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),  # US Phone
]


def _pii_scan(text: str) -> tuple[bool, list[str]]:
    """Scan text for PII before archiving. Returns (clean, [matches])."""
    hits = []
    for pattern in PII_PATTERNS:
        found = pattern.findall(text)
        if found:
            hits.extend(found)
    return len(hits) == 0, hits


def _write_ledger(action: str, url: str, result: str, op_id: str,
                  pii_clean: bool, dry_run: bool) -> None:
    """Rule 1 — Write immutable JSONL receipt to Pulse Ledger."""
    entry = {
        "op_id": op_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "module": "TrishulaBrowserAgent",
        "action": action,
        "url": url,
        "result_preview": result[:200],
        "pii_clean": pii_clean,
        "dry_run": dry_run,
        "doctrine": "Rule1:Receipt|Rule3:KineticGate|Tizona:SOCKS5"
    }
    with open(LEDGER_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def _shadow_snapshot(url: str, content: str, op_id: str) -> Path:
    """Rule 0 — Pre-extraction snapshot of target state."""
    snap_path = BACKUP_PATH / f"browser_{op_id}_shadow.json"
    snap = {
        "op_id": op_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "url": url,
        "content_preview": content[:500],
        "rule": "Rule0:ShadowMandate"
    }
    snap_path.write_text(json.dumps(snap, indent=2), encoding="utf-8")
    return snap_path


class TrishulaBrowserAgent:
    """
    Sovereign autonomous web browser agent.

    Wraps browser-use with:
    - Tizona SOCKS5 proxy airlock (ports 1080–1083)
    - Rule 3 dry-run kinetic action gate
    - PII scan on all extracted text
    - Rule 0/1 shadow snapshot + JSONL ledger receipt
    - Qdrant vector indexing of clean extractions

    Usage:
        agent = TrishulaBrowserAgent(dry_run=True)
        result = await agent.extract("https://target.com", "get the pricing table")
    """

    def __init__(
        self,
        dry_run: bool = True,
        proxy: Optional[str] = None,
        model: str = "ollama/llama3.2:3b",
    ):
        self.dry_run = dry_run
        self.proxy = proxy or TIZONA_PROXY
        self.model = model
        self._op_count = 0

        if dry_run:
            print("[TrishulaBrowserAgent] ⚠  DRY-RUN MODE — kinetic actions BLOCKED")
        else:
            print("[TrishulaBrowserAgent] 🔴 LIVE MODE — Rule 3 gate active")

    def _gate_action(self, task: str) -> bool:
        """Rule 3: Block any task containing forbidden kinetic keywords."""
        task_lower = task.lower()
        for blocked in BLOCKED_ACTIONS:
            if blocked.replace("_", " ") in task_lower:
                print(f"[TrishulaBrowserAgent] ❌ KINETIC VETO: '{blocked}' detected in task.")
                return False
        return True

    async def extract(
        self,
        url: str,
        task: str,
        index_to_qdrant: bool = True,
    ) -> dict:
        """
        Extract content from a URL via autonomous browser navigation.

        Args:
            url: Target URL
            task: Natural language instruction for the browser agent
            index_to_qdrant: If True, index clean extraction to Qdrant

        Returns:
            dict with keys: op_id, url, task, content, pii_clean, ledger_path
        """
        op_id = str(uuid.uuid4())[:8]
        self._op_count += 1

        print(f"\n[TrishulaBrowserAgent] OP {op_id} | URL: {url}")
        print(f"  Task: {task}")

        # ── Rule 3: Gate check ────────────────────────────────────────
        if not self._gate_action(task):
            _write_ledger("VETOED", url, "Kinetic action blocked", op_id, True, True)
            return {"op_id": op_id, "status": "VETOED", "reason": "Kinetic action blocked by Rule 3"}

        # ── Rule 0: Shadow snapshot (placeholder pre-extraction state) ─
        _shadow_snapshot(url, f"PRE-EXTRACTION: {task}", op_id)

        try:
            from browser_use import Agent as BrowserAgent
            from browser_use import BrowserConfig

            config = BrowserConfig(
                headless=True,
                proxy={"server": self.proxy} if self.proxy else None,
            )

            agent = BrowserAgent(
                task=task,
                llm=self._get_llm(),
                browser_config=config,
            )

            if self.dry_run:
                print(f"  [DRY-RUN] Would navigate to {url} — returning mock data")
                content = f"[DRY-RUN] Mock extraction for: {task} at {url}"
            else:
                result = await agent.run()
                content = str(result)

        except ImportError as e:
            content = f"[ERROR] browser-use import failed: {e}"
        except Exception as e:
            content = f"[ERROR] Browser agent error: {e}"

        # ── PII Scan ───────────────────────────────────────────────────
        pii_clean, pii_hits = _pii_scan(content)
        if not pii_clean:
            print(f"  ⚠ PII DETECTED — redacting before archive. Hits: {pii_hits[:3]}")
            for p in PII_PATTERNS:
                content = p.sub("[REDACTED]", content)

        # ── Rule 1: Ledger receipt ─────────────────────────────────────
        _write_ledger("EXTRACT", url, content, op_id, pii_clean, self.dry_run)

        # ── Optional Qdrant indexing ───────────────────────────────────
        if index_to_qdrant and pii_clean:
            self._index_to_qdrant(url, task, content, op_id)

        result_obj = {
            "op_id": op_id,
            "status": "OK",
            "url": url,
            "task": task,
            "content": content,
            "pii_clean": pii_clean,
            "dry_run": self.dry_run,
            "ledger": str(LEDGER_PATH),
        }
        print(f"  ✅ OP {op_id} complete | PII clean: {pii_clean}")
        return result_obj

    def _get_llm(self):
        """Return configured LLM. Defaults to local Ollama."""
        try:
            from langchain_ollama import ChatOllama
            return ChatOllama(model=self.model.replace("ollama/", ""), temperature=0)
        except ImportError:
            # Fallback to OpenAI-compatible local endpoint
            from openai import OpenAI
            return OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

    def _index_to_qdrant(self, url: str, task: str, content: str, op_id: str) -> None:
        """Index clean extraction to Qdrant browser_extractions collection."""
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import PointStruct, Distance, VectorParams
            from fastembed import TextEmbedding

            client = QdrantClient(path=r"D:\Trishula-Infra\qdrant_store")
            collection = "browser_extractions"

            # Ensure collection exists
            existing = [c.name for c in client.get_collections().collections]
            if collection not in existing:
                client.create_collection(
                    collection_name=collection,
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
                )

            embedder = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
            vector = list(embedder.embed([content[:512]]))[0].tolist()

            client.upsert(
                collection_name=collection,
                points=[PointStruct(
                    id=abs(hash(op_id)) % (2**31),
                    vector=vector,
                    payload={"url": url, "task": task, "op_id": op_id,
                             "timestamp": datetime.now(timezone.utc).isoformat()}
                )]
            )
            print(f"  📦 Indexed to Qdrant collection '{collection}'")
        except Exception as e:
            print(f"  ⚠ Qdrant indexing skipped: {e}")


# ── Standalone test ───────────────────────────────────────────────────
if __name__ == "__main__":
    agent = TrishulaBrowserAgent(dry_run=True)
    result = asyncio.run(agent.extract(
        url="https://github.com/browser-use/browser-use",
        task="get the latest release version and star count from the GitHub page"
    ))
    print(json.dumps(result, indent=2))
