"""Run an end-to-end UI click check against a Chrome DevTools instance."""

import argparse
import json
import time
from itertools import count
from typing import Any, cast
from urllib.parse import quote
from urllib.request import Request, urlopen

from websockets.sync.client import connect


def create_tab(debug_port: int, page_url: str) -> str:
    endpoint = f"http://127.0.0.1:{debug_port}/json/new?{quote(page_url, safe=':/')}"
    request = Request(endpoint, method="PUT")
    with urlopen(request, timeout=5) as response:  # noqa: S310 - local DevTools only
        payload = json.load(response)
    return str(payload["webSocketDebuggerUrl"])


def run_check(debug_port: int, page_url: str) -> dict[str, Any]:
    command_ids = count(1)
    errors: list[str] = []

    with connect(create_tab(debug_port, page_url)) as socket:
        def command(method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
            command_id = next(command_ids)
            socket.send(json.dumps({"id": command_id, "method": method, "params": params or {}}))
            while True:
                message = json.loads(socket.recv())
                if message.get("method") == "Runtime.exceptionThrown":
                    errors.append(json.dumps(message["params"], ensure_ascii=False))
                if message.get("id") == command_id:
                    if "error" in message:
                        raise RuntimeError(message["error"])
                    return cast(dict[str, Any], message.get("result", {}))

        command("Runtime.enable")
        command("Page.enable")
        command("Page.navigate", {"url": page_url})
        time.sleep(0.5)
        command(
            "Runtime.evaluate",
            {"expression": "document.querySelector('#start-button').click()"},
        )
        time.sleep(1)
        result = command(
            "Runtime.evaluate",
            {
                "expression": (
                    "JSON.stringify({"
                    "ready:document.querySelector('#connection-label').dataset.uiReady,"
                    "state:document.querySelector('#state-value').textContent,"
                    "transcript:document.querySelectorAll('.transcript-line').length,"
                    "error:document.querySelector('#toast').textContent"
                    "})"
                ),
                "returnByValue": True,
            },
        )

    if errors:
        raise RuntimeError("Browser JavaScript error: " + "\n".join(errors))
    value = result["result"]["value"]
    return dict(json.loads(value))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug-port", type=int, default=9223)
    parser.add_argument("--url", default="http://127.0.0.1:8010/internal/")
    args = parser.parse_args()

    result = run_check(args.debug_port, args.url)
    assert result["ready"] == "true", result
    assert result["state"] == "AWAITING_IDENTITY", result
    assert result["transcript"] >= 1, result
    assert not result["error"], result
    print("Browser UI smoke check: OK", json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
