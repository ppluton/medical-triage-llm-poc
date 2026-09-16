#!/usr/bin/env python3
"""Print the deployed Modal Server HTTPS origin without exposing credentials."""

from urllib.parse import urlparse

import modal

from triage_poc.modal_deployment import MODAL_APP_NAME, MODAL_SERVER_NAME


def main() -> None:
    url = modal.Server.from_name(MODAL_APP_NAME, MODAL_SERVER_NAME).get_url()
    parsed = urlparse(url)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or parsed.path not in {"", "/"}
    ):
        raise ValueError("Modal returned an unexpected Server URL")
    print(url.rstrip("/"))


if __name__ == "__main__":
    main()
