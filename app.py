from flask import Flask, render_template, request, redirect, url_for
import os
import threading
import requests
import time
import socket
import ssl
import json
import urllib3
import smtplib
from urllib.parse import urlparse
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from datetime import datetime, UTC
from email.mime.text import MIMEText
from flask import flash
from flask_httpauth import HTTPBasicAuth
from concurrent.futures import ThreadPoolExecutor

from models import db, Group, Service, AlertRule, NotificationChannel
from werkzeug.security import generate_password_hash, check_password_hash

# --------------------
# app & db
# --------------------
app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////data/servicehub.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config["SECRET_KEY"] = "servicehub_secret_key"

auth = HTTPBasicAuth()

db.init_app(app)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

users = {
    os.getenv("ADMIN_USER", "admin"):
    generate_password_hash(os.getenv("ADMIN_PASSWORD", "servicehub123"))
}
@auth.verify_password
def verify_password(username, password):

    if username in users and check_password_hash(users.get(username), password):
        return username
# --------------------
# utils
# --------------------
def check_service(url, timeout=3):
    start = time.time()
    try:
        r = requests.head(
            url,
            timeout=timeout,
            verify=False,
            allow_redirects=True
        )
        elapsed = time.time() - start

        if r.status_code < 400:
            return "warning" if elapsed > 1.5 else "ok"
        return "down"

    except Exception as e:
        print(f"[ServiceHub] {url} DOWN: {e}")
        return "down"

def process_service(s):

    new_status = check_service(s.url)

    if s.status != new_status:

        message = (
            f"⚠ <b>{s.name}</b>\n"
            f"Статус изменился:\n"
            f"{s.status or 'unknown'} → <b>{new_status}</b>\n"
            f"{s.url}"
        )

        rules = AlertRule.query.filter_by(
            service_id=s.id,
            type="status_change",
            enabled=True
        ).all()

        for rule in rules:
            if rule.channel and rule.channel.enabled:
                send_notification(rule.channel, message)

    s.status = new_status
    s.checked_at = datetime.now(UTC)

    # SSL проверка
    if s.url.startswith("https://"):

        try:

            need_check = (
                not s.ssl_expiry_date or
                not s.checked_at or
                (datetime.now(UTC) - s.checked_at).total_seconds() > 3600
            )

            if need_check:

                parsed = urlparse(s.url)
                host = parsed.hostname

                ssl_info = check_ssl_expiry(host)

                s.ssl_days_left = ssl_info["days_left"]
                s.ssl_expiry_date = ssl_info["expiry_date"]

        except Exception as e:

            print(f"[SSL ERROR] {s.url}: {e}")

            s.ssl_days_left = -1        

def update_statuses():

    services = Service.query.all()

    with ThreadPoolExecutor(max_workers=20) as executor:
        executor.map(process_service, services)

    db.session.commit()

def check_ssl_expiry(hostname, port=443):
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    with socket.create_connection((hostname, port), timeout=5) as sock:
        with context.wrap_socket(sock, server_hostname=hostname) as ssock:
            der_cert = ssock.getpeercert(binary_form=True)

    cert = x509.load_der_x509_certificate(der_cert, default_backend())

    # ВАЖНО: используем timezone-aware дату
    expiry_date = cert.not_valid_after_utc

    days_left = (expiry_date - datetime.now(UTC)).days

    return {
        "expiry_date": expiry_date,
        "days_left": days_left
    }
# --------------------
# routes: dashboard
# --------------------
@app.route("/")
def index():
   
    groups = Group.query.order_by(Group.name).all()

    # добавляем SSL-информацию
    """ for group in groups:
        for s in group.services:

            s.ssl_days_left = None
            s.ssl_expiry_date = None

            if s.url.startswith("https://"):
                try:
                    parsed = urlparse(s.url)
                    host = parsed.hostname

                    ssl_info = check_ssl_expiry(host)

                    s.ssl_days_left = ssl_info["days_left"]
                    s.ssl_expiry_date = ssl_info["expiry_date"]

                except Exception as e:
                    print(f"[SSL ERROR] {s.url}: {type(e).__name__} - {e}")
                    s.ssl_days_left = -1 """

    return render_template(
        "index.html",
        groups=groups,
        year=datetime.now().year
    )

@app.route("/api/status")
def api_status():

    services = Service.query.all()

    data = []

    for s in services:

        data.append({
            "id": s.id,
            "status": s.status,
            "ssl_days_left": s.ssl_days_left
        })

    return {"services": data}

# --------------------
# admin: services
# --------------------
@app.route("/admin", methods=["GET", "POST"])
@auth.login_required
def admin():
    groups = Group.query.order_by(Group.name).all()

    if request.method == "POST":
        service = Service(
            name=request.form["name"],
            description=request.form.get("description"),
            url=request.form["url"],
            group_id=int(request.form["group_id"])
        )
        db.session.add(service)
        db.session.commit()
        return redirect(url_for("admin"))

    services = Service.query.order_by(Service.name).all()
    return render_template(
        "admin.html",
        services=services,
        groups=groups
    )

# --------------------
# admin: edit service
# --------------------
@app.route("/admin/edit/<int:service_id>", methods=["GET", "POST"])
@auth.login_required
def edit_service(service_id):
    service = Service.query.get_or_404(service_id)
    groups = Group.query.order_by(Group.name).all()

    if request.method == "POST":
        service.name = request.form["name"]
        service.description = request.form.get("description")
        service.url = request.form["url"]
        service.group_id = int(request.form["group_id"])

        db.session.commit()
        return redirect(url_for("admin"))

    return render_template(
        "admin_edit.html",
        service=service,
        groups=groups
    )

# --------------------
# admin: delete service
# --------------------
@app.route("/admin/delete/<int:service_id>", methods=["POST"])
@auth.login_required
def delete_service(service_id):
    service = Service.query.get_or_404(service_id)
    db.session.delete(service)
    db.session.commit()
    return redirect(url_for("admin"))

# --------------------
# admin: groups
# --------------------
@app.route("/admin/groups", methods=["GET", "POST"])
@auth.login_required
def admin_groups():
    if request.method == "POST":
        name = request.form["name"].strip()
        if name:
            db.session.add(Group(name=name))
            db.session.commit()
        return redirect(url_for("admin_groups"))

    groups = Group.query.order_by(Group.name).all()
    return render_template("groups.html", groups=groups)

# --------------------
# admin: delete group
# --------------------
@app.route("/admin/groups/delete/<int:group_id>", methods=["POST"])
@auth.login_required
def delete_group(group_id):
    group = Group.query.get_or_404(group_id)
    db.session.delete(group)
    db.session.commit()
    return redirect(url_for("admin_groups"))

# --------------------
# admin: alerts
# --------------------
@app.route("/admin/alerts", methods=["GET", "POST"])
@auth.login_required
def admin_alerts():

    services = Service.query.order_by(Service.name).all()
    channels = NotificationChannel.query.filter_by(enabled=True).all()

    if request.method == "POST":

        rule = AlertRule(
            service_id=int(request.form["service_id"]),
            channel_id=int(request.form["channel_id"]),
            type=request.form["type"],
            days_before=request.form.get("days_before") or None,
            enabled=True
        )

        db.session.add(rule)
        db.session.commit()

        return redirect(url_for("admin_alerts"))

    alerts = AlertRule.query.all()

    return render_template(
        "alerts.html",
        alerts=alerts,
        services=services,
        channels=channels
    )


@app.route("/admin/alerts/delete/<int:alert_id>", methods=["POST"])
@auth.login_required
def delete_alert(alert_id):

    alert = AlertRule.query.get_or_404(alert_id)

    db.session.delete(alert)
    db.session.commit()

    return redirect(url_for("admin_alerts"))

@app.route("/admin/alerts/toggle/<int:alert_id>")
@auth.login_required
def toggle_alert(alert_id):

    alert = AlertRule.query.get_or_404(alert_id)

    alert.enabled = not alert.enabled

    db.session.commit()

    return redirect(url_for("admin_alerts"))

def send_telegram(channel, message):

    config = json.loads(channel.config)

    url = f"https://api.telegram.org/bot{config['token']}/sendMessage"

    r = requests.post(
        url,
        json={
            "chat_id": config["chat_id"],
            "text": message,
            "parse_mode": "HTML"
        },
        timeout=5
    )

    data = r.json()

    if not data.get("ok"):
        raise Exception(data)

def send_email(channel, message):

    config = json.loads(channel.config)

    msg = MIMEText(message)
    msg["Subject"] = "ServiceHub Alert"
    msg["From"] = config["from"]
    msg["To"] = config["to"]

    with smtplib.SMTP_SSL(config["smtp"], int(config["port"])) as server:

        server.login(config["user"], config["password"])
        server.send_message(msg)

    return True

def send_notification(channel, message):

    if channel.type == "telegram":
        send_telegram(channel, message)

    elif channel.type == "email":
        send_email(channel, message)

@app.route("/admin/notifications", methods=["GET", "POST"])
@auth.login_required
def admin_notifications():

    if request.method == "POST":

        name = request.form["name"]
        type = request.form["type"]

        if type == "telegram":

            config = {
                "token": request.form["token"],
                "chat_id": request.form["chat_id"]
            }

        elif type == "email":

            config = {
                "smtp": request.form["smtp"],
                "port": request.form["port"],
                "user": request.form["user"],
                "password": request.form["password"],
                "from": request.form["from"],
                "to": request.form["to"]
            }

        channel = NotificationChannel(
            name=name,
            type=type,
            config=json.dumps(config)
        )

        db.session.add(channel)
        db.session.commit()

        return redirect(url_for("admin_notifications"))

    channels = NotificationChannel.query.all()

    return render_template(
        "notifications.html",
        channels=channels
    )

@app.route("/admin/notifications/delete/<int:channel_id>", methods=["POST"])
@auth.login_required
def delete_notification(channel_id):

    channel = NotificationChannel.query.get_or_404(channel_id)

    db.session.delete(channel)
    db.session.commit()

    flash("Канал уведомлений удалён", "success")

    return redirect(url_for("admin_notifications"))

@app.route("/admin/notifications/test/<int:channel_id>")
@auth.login_required
def test_notification(channel_id):

    channel = NotificationChannel.query.get_or_404(channel_id)

    try:

        send_notification(
            channel,
            "🧪 ServiceHub test notification\nКанал работает корректно."
        )

        flash("Тестовое уведомление отправлено", "success")

    except Exception as e:

        print(e)

        flash("Ошибка отправки уведомления", "error")

    return redirect(url_for("admin_notifications"))

# --------------------
# init
# --------------------

def start_status_worker():

    def loop():

        while True:

            with app.app_context():

                print("[ServiceHub] checking services...")

                update_statuses()

            time.sleep(60)

    t = threading.Thread(target=loop)
    t.daemon = True
    t.start()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        start_status_worker()

    app.run(host="0.0.0.0", port=5000)