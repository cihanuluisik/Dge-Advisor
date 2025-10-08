import argparse
import json
import sys
import time
from typing import Tuple

import requests
import uuid


def build_payload(question: str, stream: bool) -> dict:
    return {
        "model": "dge-policy-rag",
        "messages": [{"role": "user", "content": question}],
        "stream": stream,
        "citations": False,
    }


def _parse_sse_text(body: str) -> str:
    chunks = []
    for line in body.splitlines():
        line = line.strip()
        if not line or not line.startswith("data: "):
            continue
        if line == "data: [DONE]":
            break
        try:
            payload = json.loads(line[len("data: ") :])
            delta = payload.get("choices", [{}])[0].get("delta", {}).get("content", "")
            if delta:
                chunks.append(delta)
        except Exception:
            # Ignore malformed lines
            pass
    return "".join(chunks)


def run_non_stream(base_url: str, question: str) -> Tuple[float, float, str]:
    url = f"{base_url.rstrip('/')}/v1/chat/completions"
    payload = build_payload(question, stream=False)
    headers = {"Content-Type": "application/json"}

    t0 = time.perf_counter()
    resp = requests.post(url, data=json.dumps(payload), headers=headers, timeout=600)
    t1 = time.perf_counter()

    resp.raise_for_status()
    ctype = resp.headers.get("Content-Type", "")
    if "event-stream" in ctype or resp.text.strip().startswith("data: "):
        # Server streamed SSE even for non-stream request
        text = _parse_sse_text(resp.text)
        return 0.0, t1 - t0, text
    else:
        body = resp.json()
        text = body.get("choices", [{}])[0].get("message", {}).get("content", "") or body.get(
            "choices", [{}]
        )[0].get("delta", {}).get("content", "")
        return 0.0, t1 - t0, text


def run_stream(base_url: str, question: str, pga4_session: str) -> Tuple[float, float, str]:
    url = f"{base_url.rstrip('/')}/v1/chat/completions"
    payload = build_payload(question, stream=True)
    headers = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Cookie": f"pga4_session={pga4_session}",
    }

    t0 = time.perf_counter()
    first_byte = 0.0
    collected = []

    with requests.post(url, data=json.dumps(payload), headers=headers, stream=True, timeout=600) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines(decode_unicode=True):
            if not line:
                continue
            if line.startswith("data: "):
                if first_byte == 0.0:
                    first_byte = time.perf_counter() - t0
                if line.strip() == "data: [DONE]":
                    break
                try:
                    chunk = json.loads(line[len("data: ") :])
                    delta = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                    if delta:
                        collected.append(delta)
                        # Print arriving chunk immediately
                        try:
                            sys.stdout.write(delta)
                            sys.stdout.flush()
                        except Exception:
                            pass
                except Exception:
                    # ignore malformed chunk
                    pass

    total = time.perf_counter() - t0
    # Ensure we end the streaming line
    try:
        sys.stdout.write("\n")
        sys.stdout.flush()
    except Exception:
        pass
    return first_byte, total, "".join(collected)


def main() -> int:
    parser = argparse.ArgumentParser(description="Chat completion client timing test (OpenWebUI-like)")
    parser.add_argument("--base-url", default="http://0.0.0.0:8007", help="API base URL")
    parser.add_argument(
        "--question",
        default="What is the probationary period for new employees?",
        help="Test question",
    )
    parser.add_argument(
        "--session",
        default=None,
        help="Value for pga4_session cookie (defaults to a random UUID)",
    )
    # Always streaming endpoint
    args = parser.parse_args()

    try:
        session_val = args.session or str(uuid.uuid4())
        ttfb, total, text = run_stream(args.base_url, args.question, session_val)

        print(f"Base URL       : {args.base_url}")
        print(f"Streaming      : True")
        print(f"pga4_session   : {session_val}")
        print(f"Time to first byte: {ttfb:.3f}s")
        print(f"Total time     : {total:.3f}s")
        print("Response:")
        print(text)
        if not text.strip():
            print("Error: streamed response is empty", file=sys.stderr)
            return 2
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())


