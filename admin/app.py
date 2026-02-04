from flask import request, redirect, url_for

@app.route("/admin", methods=["GET", "POST"])
def admin():
    with open("services.json", encoding="utf-8") as f:
        services = json.load(f)

    if request.method == "POST":
        services.append({
            "name": request.form["name"],
            "description": request.form["description"],
            "url": request.form["url"],
            "group": request.form["group"]
        })

        with open("services.json", "w", encoding="utf-8") as f:
            json.dump(services, f, ensure_ascii=False, indent=2)

        return redirect(url_for("admin"))

    return render_template("admin.html", services=services)