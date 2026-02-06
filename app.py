from flask import Flask, render_template, request, redirect, url_for
import threading
from datetime import datetime
import requests
import time



from models import db, Group, Service

# --------------------
# app & db
# --------------------
app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////data/servicehub.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

# --------------------
# utils
# --------------------
def check_service(url, timeout=3):
    start = time.time()
    try:
        r = requests.get(
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

def update_statuses():
    with app.app_context():
        services = Service.query.all()
        for s in services:
            s.status = check_service(s.url)
            s.checked_at = datetime.utcnow()
        db.session.commit()

# --------------------
# routes: dashboard
# --------------------
@app.route("/")
def index():
    # запускаем обновление в фоне
    threading.Thread(target=update_statuses, daemon=True).start()

    groups = Group.query.order_by(Group.name).all()
    return render_template(
        "index.html",
        groups=groups,
        year=datetime.now().year
    )

# --------------------
# admin: services
# --------------------
@app.route("/admin", methods=["GET", "POST"])
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
def delete_service(service_id):
    service = Service.query.get_or_404(service_id)
    db.session.delete(service)
    db.session.commit()
    return redirect(url_for("admin"))

# --------------------
# admin: groups
# --------------------
@app.route("/admin/groups", methods=["GET", "POST"])
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
def delete_group(group_id):
    group = Group.query.get_or_404(group_id)
    db.session.delete(group)
    db.session.commit()
    return redirect(url_for("admin_groups"))

# --------------------
# init
# --------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(host="0.0.0.0", port=5000)