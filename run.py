"""Start the server:  python run.py   (creates + seeds the database on first run)."""
import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host=os.environ.get("HOST", "127.0.0.1"), port=int(os.environ.get("PORT", "5000")),
            debug=os.environ.get("DEBUG", "0") == "1", threaded=True)
