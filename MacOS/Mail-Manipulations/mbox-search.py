#!/usr/bin/env python3
# mbox-search.py — find a conversation in an mbox archive using a local LLM
#
# Usage:
#   python3 mbox-search.py \
#     --file ~/path/to/archive.mbox \
#     --address someone@example.com \
#     --query "find the conversation about the apartment contract"
#
# --address can be repeated to match multiple addresses (any match counts)
# --limit   caps how many emails are sent to the LLM (default: 100)
# --model   overrides the default model (see DEFAULT_MODEL below)

import mailbox
import argparse
import email.header
import email.utils
import json
import urllib.request
import sys

# --- Configuration ---
OMLX_URL = "http://localhost:8000/api/generate"
DEFAULT_MODEL = "mlx-community/Qwen3-8B-8bit"
DEFAULT_PROMPT_TEMPLATE = (
    "You are analyzing a set of emails. Based on the emails below, answer the following question:\n\n"
    "QUESTION: {query}\n\n"
    "In your answer, quote the most relevant email(s) and include their exact date, subject, and sender.\n\n"
    "EMAILS:\n\n{emails}"
)
# --- End Configuration ---


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


def get_body(msg):
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    return payload.decode(charset, errors="replace")
        return "(no text body)"
    payload = msg.get_payload(decode=True)
    if payload:
        charset = msg.get_content_charset() or "utf-8"
        return payload.decode(charset, errors="replace")
    return str(msg.get_payload())


def format_email(msg):
    return (
        f"Date: {decode_header(msg.get('Date', ''))}\n"
        f"From: {decode_header(msg.get('From', ''))}\n"
        f"To: {decode_header(msg.get('To', ''))}\n"
        f"Subject: {decode_header(msg.get('Subject', '(no subject)'))}\n\n"
        f"{get_body(msg)}"
    )


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


def query_llm(messages, user_query, model):
    email_blocks = "\n\n---\n\n".join(format_email(m) for m in messages)
    prompt = DEFAULT_PROMPT_TEMPLATE.format(query=user_query, emails=email_blocks)

    payload = json.dumps({"model": model, "prompt": prompt, "stream": True}).encode()
    req = urllib.request.Request(
        OMLX_URL,
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
        print(f"\nError connecting to OMLX: {e}", file=sys.stderr)
        print(f"Make sure OMLX is running at {OMLX_URL}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Search an mbox file for a conversation using a local LLM via OMLX"
    )
    parser.add_argument("--file", required=True, help="Path to .mbox file")
    parser.add_argument(
        "--address",
        action="append",
        required=True,
        metavar="EMAIL",
        help="Email address to filter by (repeatable, matches any field)",
    )
    parser.add_argument("--query", required=True, help="Question to ask the LLM")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="OMLX model name")
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
