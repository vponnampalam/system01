"""Send a message to the system01 webserver's HTTP API."""

import argparse
import json
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_URL = "https://system01-287338587474.europe-west1.run.app/messages"


def post_message(url: str, message: str) -> dict:
    """POST a JSON message and return the decoded JSON response."""
    payload = json.dumps({"message": message}).encode("utf-8")
    request = Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Post a message to system01.")
    parser.add_argument("message", help="Text of the message to send")
    parser.add_argument(
        "--url",
        default=DEFAULT_URL,
        help=f"Message API URL (default: {DEFAULT_URL})",
    )
    args = parser.parse_args()

    try:
        result = post_message(args.url, args.message)
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        print(f"HTTP {error.code}: {detail}", file=sys.stderr)
        return 1
    except (URLError, TimeoutError, ValueError) as error:
        print(f"Request failed: {error}", file=sys.stderr)
        return 1

    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
