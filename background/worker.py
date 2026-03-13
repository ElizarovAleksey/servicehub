import time
from app import app, update_statuses


def start_worker():

    def loop():

        with app.app_context():

            while True:

                print("[ServiceHub] checking services...")

                update_statuses()

                time.sleep(45)

    import threading

    t = threading.Thread(target=loop)
    t.daemon = True
    t.start()