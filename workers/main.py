"""Continuously POST a message to the system01 webserver."""

import argparse
import json
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_URL = "https://system01-287338587474.europe-west1.run.app/messages"
DEFAULT_INTERVAL = 10


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


def positive_seconds(value: str) -> float:
    """Parse a positive number of seconds for the repeat interval."""
    try:
        seconds = float(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("interval must be a number") from error
    if seconds <= 0:
        raise argparse.ArgumentTypeError("interval must be greater than zero")
    return seconds


def main() -> int:
    parser = argparse.ArgumentParser(
        description="POST a message repeatedly, waiting between requests."
    )
    parser.add_argument("message", help="Text of the message to send each time")
    parser.add_argument(
        "--url",
        default=DEFAULT_URL,
        help=f"Message API URL (default: {DEFAULT_URL})",
    )
    parser.add_argument(
        "--interval",
        type=positive_seconds,
        default=DEFAULT_INTERVAL,
        help=f"Seconds to wait after each attempt (default: {DEFAULT_INTERVAL})",
    )
    args = parser.parse_args()

    print(f"Posting to {args.url} every {args.interval:g} seconds. Press Ctrl+C to stop.")
    try:
        while True:
            try:
                result = post_message(args.url, args.message)
                print(f"POST succeeded: {json.dumps(result)}", flush=True)
            except HTTPError as error:
                detail = error.read().decode("utf-8", errors="replace")
                print(f"HTTP {error.code}: {detail}", file=sys.stderr, flush=True)
            except (URLError, TimeoutError, ValueError) as error:
                print(f"Request failed: {error}", file=sys.stderr, flush=True)

            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nWorker stopped.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
