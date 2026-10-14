
import threading
import time
import webview
from app import app

def start_server():
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
        use_reloader=False
    )

if __name__ == "__main__":
    server = threading.Thread(
        target=start_server,
        daemon=True
    )
    server.start()

    time.sleep(1)

    webview.create_window(
        "Advanced ATS Tracker Pro",
        "http://127.0.0.1:5000",
        width=1200,
        height=800,
        min_size=(800, 600)
    )
    webview.start()
