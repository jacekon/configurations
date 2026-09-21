# mbox-search Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A CLI tool that filters an `.mbox` file by email address and uses a local Qwen model via Ollama to find a specific conversation, returning an LLM answer with exact email metadata (date, subject, sender) as evidence.

**Architecture:** A single Python script reads the mbox file using Python's `mailbox` module, filters messages where any specified address appears in From/To/Cc/Bcc, formats the filtered emails into a structured prompt, and sends it to Ollama's local HTTP API. A companion `SKILL.md` describes the tool for pi and Claude Code harnesses.

**Tech Stack:** Python 3 stdlib (`mailbox`, `argparse`, `urllib`), Ollama HTTP API at `http://localhost:11434`

---

## File Structure

- Create: `MacOS/Agents/mbox-search/mbox-search.py` — CLI script
- Create: `MacOS/Agents/mbox-search/SKILL.md` — pi/Claude-compatible skill descriptor
- Create: `MacOS/Agents/mbox-search/README.md` — usage reference (brief)

---

### Task 1: Scaffold the CLI and mbox filter

**Files:**
- Create: `MacOS/Agents/mbox-search/mbox-search.py`

- [ ] **Step 1: Create the file with argument parsing and filter logic**

```python
#!/usr/bin/env python3
import mailbox
import argparse
import email.header
import email.utils
import sys


def decode_header(value):
    if not value:
        return ""
    parts = email.header.decode_header(value)
    decoded = []
    for part, charset in parts:
        if isinstance(part, bytes):
            decoded.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            decoded.append(part)
    return " ".join(decoded)


def get_addresses(msg, field):
    raw = msg.get(field, "")
    if not raw:
        return []
    return [addr.lower() for _, addr in email.utils.getaddresses([raw])]


def filter_messages(mbox_path, addresses):
    mbox = mailbox.mbox(mbox_path)
    targets = {a.lower() for a in addresses}
    matched = []
    for msg in mbox:
        all_addrs = set()
        for field in ("From", "To", "Cc", "Bcc"):
            all_addrs.update(get_addresses(msg, field))
        if all_addrs & targets:
            matched.append(msg)
    return matched


def format_email(msg):
    date = decode_header(msg.get("Date", ""))
    subject = decode_header(msg.get("Subject", "(no subject)"))
    from_ = decode_header(msg.get("From", ""))
    to = decode_header(msg.get("To", ""))
    body = get_body(msg)
    return f"Date: {date}\nFrom: {from_}\nTo: {to}\nSubject: {subject}\n\n{body}"


def get_body(msg):
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    return payload.decode(charset, errors="replace")
        return "(no text body)"
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            return payload.decode(charset, errors="replace")
        return str(msg.get_payload())


def main():
    parser = argparse.ArgumentParser(
        description="Search an mbox file using a local LLM via Ollama"
    )
    parser.add_argument("--file", required=True, help="Path to .mbox file")
    parser.add_argument(
        "--address",
        action="append",
        required=True,
        metavar="EMAIL",
        help="Email address to filter by (repeatable)",
    )
    parser.add_argument("--query", required=True, help="Question to ask the LLM")
    parser.add_argument("--model", default="qwen2.5:latest", help="Ollama model name")
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Max emails to send to LLM (default: 100)",
    )
    args = parser.parse_args()

    messages = filter_messages(args.file, args.address)
    if not messages:
        print("No emails matched the specified addresses.", file=sys.stderr)
        sys.exit(1)

    if len(messages) > args.limit:
        print(
            f"Warning: {len(messages)} emails matched, truncating to {args.limit}.",
            file=sys.stderr,
        )
        messages = messages[: args.limit]

    print(f"Found {len(messages)} matching email(s). Querying LLM...", file=sys.stderr)
    query_llm(messages, args.query, args.model)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify the filter runs without error on a quick smoke test**

```bash
cd /Users/D061255/GH/jacekon/configurations/MacOS/Agents/mbox-search
python3 mbox-search.py --file /dev/null --address test@example.com --query "test" 2>&1 || true
```

Expected: error about empty/invalid mbox or "No emails matched" — not a Python traceback.

- [ ] **Step 3: Commit**

```bash
git add MacOS/Agents/mbox-search/mbox-search.py
git commit -m "feat: add mbox filter and CLI scaffold"
```

---

### Task 2: Add Ollama query function

**Files:**
- Modify: `MacOS/Agents/mbox-search/mbox-search.py` — add `query_llm()`

- [ ] **Step 1: Add the Ollama query function before `main()`**

Add this function to `mbox-search.py`, before the `main()` function:

```python
import json
import urllib.request


def query_llm(messages, user_query, model):
    email_blocks = "\n\n---\n\n".join(format_email(m) for m in messages)
    prompt = (
        f"You are analyzing a set of emails. Based on the emails below, answer the following question:\n\n"
        f"QUESTION: {user_query}\n\n"
        f"In your answer, quote the most relevant email(s) and include their exact date, subject, and sender.\n\n"
        f"EMAILS:\n\n{email_blocks}"
    )

    payload = json.dumps({"model": model, "prompt": prompt, "stream": True}).encode()
    req = urllib.request.Request(
        "http://localhost:11434/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(req) as resp:
            for line in resp:
                if line:
                    chunk = json.loads(line.decode())
                    print(chunk.get("response", ""), end="", flush=True)
                    if chunk.get("done"):
                        print()
                        break
    except OSError as e:
        print(f"\nError connecting to Ollama: {e}", file=sys.stderr)
        print("Make sure Ollama is running: ollama serve", file=sys.stderr)
        sys.exit(1)
```

Also add `import json` and `import urllib.request` to the top of the file (merge with existing imports).

- [ ] **Step 2: Verify imports are clean**

```bash
python3 -c "import MacOS.Agents.mbox-search" 2>/dev/null || python3 MacOS/Agents/mbox-search/mbox-search.py --help
```

Expected: prints usage/help with no import errors.

- [ ] **Step 3: Commit**

```bash
git add MacOS/Agents/mbox-search/mbox-search.py
git commit -m "feat: add Ollama streaming query to mbox-search"
```

---

### Task 3: Write the SKILL.md

**Files:**
- Create: `MacOS/Agents/mbox-search/SKILL.md`

- [ ] **Step 1: Create SKILL.md**

```markdown
---
name: mbox-search
description: Search an mbox email archive for a specific conversation using a local LLM. Use when the user wants to find an email, conversation, or topic in a .mbox file and can't locate it by keyword search.
---

# mbox-search

Search an `.mbox` file by email address and find a conversation using a local Qwen model via Ollama.

## Usage

```bash
python3 /path/to/mbox-search.py \
  --file <path-to-file.mbox> \
  --address <email@example.com> \
  [--address <another@example.com>] \
  --query "<natural language question>" \
  [--model qwen2.5:latest] \
  [--limit 100]
```

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `--file` | yes | Path to the `.mbox` file |
| `--address` | yes, repeatable | Filter: keep emails where this address appears in From, To, Cc, or Bcc |
| `--query` | yes | Natural language question — what conversation to find |
| `--model` | no | Ollama model name (default: `qwen2.5:latest`) |
| `--limit` | no | Max emails to pass to LLM, warns if truncated (default: 100) |

## Requirements

- Python 3 (stdlib only, no pip install needed)
- Ollama running locally: `ollama serve`
- Qwen model pulled: `ollama pull qwen2.5:latest`

## Example

```bash
python3 ~/GH/jacekon/configurations/MacOS/Agents/mbox-search/mbox-search.py \
  --file ~/Downloads/archive.mbox \
  --address alice@example.com \
  --address bob@example.com \
  --query "find the conversation about the apartment contract in early 2024"
```

The LLM will respond with a natural language answer quoting the most relevant emails, including their date, subject, and sender.
```

- [ ] **Step 2: Commit**

```bash
git add MacOS/Agents/mbox-search/SKILL.md
git commit -m "feat: add pi/Claude-compatible SKILL.md for mbox-search"
```

---

### Task 4: Manual end-to-end test

**Files:** none (verification only)

- [ ] **Step 1: Confirm Ollama is running and Qwen is available**

```bash
ollama list | grep qwen
```

Expected: at least one `qwen` model listed. If not: `ollama pull qwen2.5:latest`

- [ ] **Step 2: Run against a real mbox file**

```bash
python3 MacOS/Agents/mbox-search/mbox-search.py \
  --file <path-to-your.mbox> \
  --address <known-address@example.com> \
  --query "summarize the most recent conversation" \
  --limit 5
```

Expected: stderr shows count of matched emails, then LLM streams a response quoting email metadata.

- [ ] **Step 3: Test truncation warning**

```bash
python3 MacOS/Agents/mbox-search/mbox-search.py \
  --file <path-to-your.mbox> \
  --address <address-with-many-emails> \
  --query "test" \
  --limit 2
```

Expected: stderr shows "Warning: N emails matched, truncating to 2."

- [ ] **Step 4: Test no-match case**

```bash
python3 MacOS/Agents/mbox-search/mbox-search.py \
  --file <path-to-your.mbox> \
  --address nobody@nowhere.invalid \
  --query "test"
```

Expected: stderr shows "No emails matched..." and exits with code 1.
