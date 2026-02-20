#!/usr/bin/env python3
"""Send a chat message into an active Opencode session (minimal example).

Usage:
  python send_opencode_message.py --text "Hello" [--base-url http://127.0.0.1:4096] [--session-id <id>]

Behavior:
 - If --session-id is provided the message is sent to that session.
 - Otherwise the script lists sessions and picks an "active" session or the first one.

Notes:
 - The Opencode SDK (opencode-ai) must be installed in the environment.
 - You can set OPENCODE_BASE_URL env var instead of --base-url.
 - This is best-effort: network errors are printed but do not raise uncaught.
"""

from __future__ import annotations

import argparse
import os
import sys
import traceback
import socket
import time
from urllib.parse import urlparse

import httpx
from typing import Any, cast

try:
    import opencode_ai
    from opencode_ai import Opencode
    from opencode_ai import APIConnectionError
except Exception:  # pragma: no cover - helpful error message for missing dependency
    print(
        "Missing dependency: install the official SDK 'opencode-ai' (pip install --pre opencode-ai)"
    )
    raise


def send_message(
    text: str,
    base_url: str | None = None,
    session_id: str | None = None,
    model_id: str | None = None,
    provider_id: str | None = None,
) -> int:
    """Send `text` into the given session or the first active session.

    Returns 0 on success, non-zero on failure.
    """
    client = Opencode(base_url=base_url) if base_url else Opencode()

    try:
        if session_id:
            target = session_id
        else:
            sessions = client.session.list()
            # sessions may be a list-like or an iterable; convert to list to inspect
            sessions = list(sessions)
            if not sessions:
                print("No sessions available on the Opencode instance.")
                return 2

            active = next(
                (s for s in sessions if getattr(s, "status", None) == "active"), None
            )
            selected = active or sessions[0]
            target = getattr(selected, "id", None) or getattr(
                selected, "session_id", None
            )
            if not target:
                print("Could not determine session id from session object:", selected)
                return 3

        # parts is the structured message payload used by the SDK
        parts = [{"type": "text", "text": text}]

        # If model/provider not provided, attempt to infer from the last message's info block
        if not model_id or not provider_id:
            try:
                msg = _get_last_message(client, target)
                inferred_model, inferred_provider = (
                    _extract_model_provider_from_message(msg)
                )
                if inferred_model and inferred_provider:
                    model_id = model_id or inferred_model
                    provider_id = provider_id or inferred_provider
                    print(
                        f"Inferred model_id={model_id} provider_id={provider_id} from last message"
                    )
                else:
                    print(
                        "Could not infer model_id/provider_id from recent messages.\n"
                        "Provide them via --model-id/--provider-id or set OPENCODE_MODEL_ID/OPENCODE_PROVIDER_ID env vars."
                    )
                    return 6
            except Exception:
                print(
                    "Failed to infer model/provider from last message; please provide --model-id and --provider-id"
                )
                return 6

        # Use session.prompt to create/send a new message in the session.
        # The SDK expects a `model` object for provider/model identifiers.
        model_obj = {"providerID": provider_id, "modelID": model_id}
        # Try preferred high-level SDK method first (session.prompt)
        try:
            if hasattr(client.session, "prompt"):
                client.session.prompt(
                    id=target, parts=cast(Any, parts), model=model_obj
                )
            else:
                raise AttributeError("session.prompt not available")
        except Exception as e:
            # Fallback: POST directly to the session prompt endpoint
            print(
                f"High-level send failed ({type(e).__name__}): {e}; trying low-level POST /session/{target}/prompt"
            )
            body = {
                "parts": parts,
                "model": {"providerID": provider_id, "modelID": model_id},
            }
            try:
                resp = client.post(f"/session/{target}/prompt", body=body, cast_to=dict)
                print("Low-level POST response type:", type(resp))
            except Exception as e2:
                print("Low-level POST failed:", type(e2).__name__, e2)
                raise
        print(f"Message sent to session {target}")
        return 0

    except APIConnectionError as e:
        print("Connection error while talking to Opencode API:", e)
        if getattr(e, "__cause__", None):
            print("Underlying cause:")
            traceback.print_exception(e.__cause__)
        return 4
    except Exception as e:
        print("Error sending message:", type(e).__name__, e)
        traceback.print_exc()
        return 5


def _diagnose_base_url(base_url: str) -> None:
    """Perform lightweight diagnostics for base_url: DNS, TCP connect and optional health endpoint.

    Prints findings to stdout to help debug connection issues.
    """
    print(f"Diagnostic: probing {base_url}")
    parsed = urlparse(base_url)
    host = parsed.hostname or parsed.path
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    print(f"Resolved host={host} port={port} scheme={parsed.scheme}")

    try:
        infos = socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
        addrs = sorted({str(ai[4][0]) for ai in infos})
        print("Address(es):", ", ".join(addrs))
    except Exception as e:
        print("getaddrinfo failed:", e)

    health_url = base_url.rstrip("/") + "/health"
    for attempt in range(1, 4):
        try:
            print(f"HTTP probe attempt {attempt} -> {health_url}")
            with httpx.Client(timeout=5.0) as c:
                r = c.get(health_url)
            print("HTTP probe status:", r.status_code)
            break
        except Exception as e:
            print(f"Probe attempt {attempt} failed: {e}")
            time.sleep(0.5)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Send a message into an Opencode session (minimal example)"
    )
    p.add_argument("--text", required=True, help="Text to send into the session")
    p.add_argument(
        "--base-url",
        default=os.environ.get("OPENCODE_BASE_URL", "http://127.0.0.1:4096"),
        help="Opencode base URL (default: http://127.0.0.1:4096)",
    )
    p.add_argument(
        "--debug",
        action="store_true",
        help="Enable lightweight diagnostics before sending",
    )
    p.add_argument(
        "--model-id",
        default=os.environ.get("OPENCODE_MODEL_ID"),
        help="Model id to use for session.chat (or set OPENCODE_MODEL_ID)",
    )
    p.add_argument(
        "--provider-id",
        default=os.environ.get("OPENCODE_PROVIDER_ID"),
        help="Provider id to use for session.chat (or set OPENCODE_PROVIDER_ID)",
    )
    p.add_argument(
        "--session-id",
        help="If provided, send to this session id instead of selecting an active session",
    )
    args = p.parse_args(argv)

    if args.debug and args.base_url:
        _diagnose_base_url(args.base_url)

    return send_message(
        text=args.text,
        base_url=args.base_url,
        session_id=args.session_id,
        model_id=args.model_id,
        provider_id=args.provider_id,
    )


def _get_last_message(client: Opencode, session_id: str):
    """Try to fetch recent messages for a session using a few possible call signatures.

    Returns the last message object or None.
    """
    # The SDK exposes session.messages(id=...) which returns a list of message items.
    try:
        res = client.session.messages(id=session_id)
        # res may already be a list
        try:
            messages = list(res)
        except Exception:
            messages = res
        if messages:
            return messages[-1]
    except TypeError:
        # signature mismatch; fall through
        pass
    except Exception:
        # network or other error
        return None

    # If above failed, try message resource if present
    msg_resource = getattr(client, "message", None)
    if not msg_resource:
        return None

    try:
        func = getattr(msg_resource, "list")
        messages = func(session_id=session_id)
        messages = list(messages)
        if messages:
            return messages[-1]
    except Exception:
        return None

    return None


def _extract_model_provider_from_message(msg) -> tuple[str | None, str | None]:
    """Extract model_id and provider_id from a message object `info` block.

    Returns (model_id, provider_id) or (None, None).
    """
    if not msg:
        return None, None

    # Try pydantic helpers first
    data = None
    try:
        data = msg.to_dict()
    except Exception:
        try:
            data = getattr(msg, "model_dump", lambda: None)()
        except Exception:
            data = getattr(msg, "__dict__", None)

    if not data or not isinstance(data, dict):
        return None, None

    # info blocks may live under several keys
    info = (
        data.get("info")
        or data.get("metadata")
        or data.get("meta")
        or data.get("extras")
    )
    if isinstance(info, dict):
        # accept multiple casing conventions used in the SDK responses
        model_id = (
            info.get("model_id")
            or info.get("modelId")
            or info.get("modelID")
            or info.get("model")
        )
        provider_id = (
            info.get("provider_id")
            or info.get("providerId")
            or info.get("providerID")
            or info.get("provider")
        )
        return model_id, provider_id

    # fallback: check top-level keys
    model_id = (
        data.get("model_id")
        or data.get("modelId")
        or data.get("modelID")
        or data.get("model")
    )
    provider_id = (
        data.get("provider_id")
        or data.get("providerId")
        or data.get("providerID")
        or data.get("provider")
    )
    return model_id, provider_id


if __name__ == "__main__":
    sys.exit(main())
