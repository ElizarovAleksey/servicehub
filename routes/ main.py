from flask import Blueprint, render_template
from services.cache import get_all
from services.loader import load_services

main = Blueprint("main", __name__)


@main.route("/")
def index():

    services = load_services()
    cache = get_all()

    for s in services:

        name = s["name"]

        if name in cache:
            s["status"] = cache[name]["data"]["status"]
            s["cert_expiry"] = cache[name]["data"]["cert_expiry"]
        else:
            s["status"] = "unknown"

    return render_template(
        "index.html",
        services=services
    )