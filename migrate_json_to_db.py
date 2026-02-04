import json
from app import app
from models import db, Group, Service

with app.app_context():
    db.create_all()

    with open("services.json", encoding="utf-8") as f:
        data = json.load(f)

    for item in data:
        group = Group.query.filter_by(name=item["group"]).first()
        if not group:
            group = Group(name=item["group"])
            db.session.add(group)
            db.session.commit()

        service = Service(
            name=item["name"],
            description=item.get("description"),
            url=item["url"],
            group_id=group.id
        )
        db.session.add(service)

    db.session.commit()

    print("✅ Migration from services.json completed")