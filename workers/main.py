"""Continuously POST a message to the system01 webserver."""

import argparse
import json
import logging
import random
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_URL = "https://system01-287338587474.europe-west1.run.app/messages"
DEFAULT_INTERVAL = 10
TEMP_MIN = 67
TEMP_MAX = 98

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


def create_message() -> str:
    """Create the message to send."""
    temp_val = random.uniform(TEMP_MIN, TEMP_MAX)
    return json.dumps({"temp": temp_val})


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
        description="Create and POST a message repeatedly, waiting between requests."
    )
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

    logger.info(
        "Starting POST loop: url=%s interval=%g seconds",
        args.url,
        args.interval,
    )
    try:
        while True:
            logger.info("Posting message to %s", args.url)
            try:
                result = post_message(args.url, create_message())
                logger.info("POST succeeded: %s", json.dumps(result))
            except HTTPError as error:
                detail = error.read().decode("utf-8", errors="replace")
                logger.error("POST failed with HTTP %s: %s", error.code, detail)
            except (URLError, TimeoutError, ValueError) as error:
                logger.error("POST request failed: %s", error)

            time.sleep(args.interval)
    except KeyboardInterrupt:
        logger.info("Worker stopped.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
