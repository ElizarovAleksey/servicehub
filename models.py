from flask_sqlalchemy import SQLAlchemy
import json

db = SQLAlchemy()

class Group(db.Model):
    __tablename__ = "groups" 

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    services = db.relationship(
        "Service",
        backref="group",
        cascade="all, delete",
        lazy=True
    )

class Service(db.Model):
    __tablename__ = "services"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    url = db.Column(db.String(255), nullable=False)
    is_critical = db.Column(db.Boolean, default=False)

    status = db.Column(db.String(10), default="unknown")
    checked_at = db.Column(db.DateTime)
    

    ssl_days_left = db.Column(db.Integer)
    ssl_expiry_date = db.Column(db.DateTime)
    ssl_checked_at = db.Column(db.DateTime)
    ssl_cert_path = db.Column(db.String(255))
    ssl_mode = db.Column(db.String(10), default="auto")
    
    group_id = db.Column(
        db.Integer,
        db.ForeignKey("groups.id"),
        nullable=False
    )

class AlertRule(db.Model):
    __tablename__ = "alert_rules"

    id = db.Column(db.Integer, primary_key=True)

    service_id = db.Column(db.Integer, db.ForeignKey("services.id"))
    service = db.relationship("Service")

    channel_id = db.Column(db.Integer, db.ForeignKey("notification_channels.id"))
    channel = db.relationship("NotificationChannel")

    type = db.Column(db.String(50))

    days_before = db.Column(db.Integer)

    enabled = db.Column(db.Boolean, default=True)

class NotificationChannel(db.Model):
    __tablename__ = "notification_channels"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(50))  # Telegram / Email
    type = db.Column(db.String(20))  # telegram / email

    config = db.Column(db.Text)  # JSON с настройками

    enabled = db.Column(db.Boolean, default=True)
