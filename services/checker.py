import requests
import socket
import ssl
from datetime import datetime

from services.cache import update
from config import REQUEST_TIMEOUT, VERIFY_SSL


def check_service(service):

    url = service["url"]
    name = service["name"]

    status = "down"
    cert_expiry = None

    try:
        r = requests.get(
            url,
            timeout=REQUEST_TIMEOUT,
            verify=VERIFY_SSL
        )

        if r.status_code < 500:
            status = "ok"

        if url.startswith("https"):

            hostname = url.split("//")[1].split("/")[0]

            context = ssl.create_default_context()
            with socket.create_connection((hostname, 443), timeout=3) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:

                    cert = ssock.getpeercert()

                    expiry = cert["notAfter"]

                    cert_expiry = datetime.strptime(
                        expiry,
                        "%b %d %H:%M:%S %Y %Z"
                    )

    except Exception:
        status = "down"

    update(name, {
        "status": status,
        "cert_expiry": cert_expiry
    })