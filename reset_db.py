"""Delete the database and recreate it with fresh demo data:  python reset_db.py"""
import os
from app.config import Config

cfg = Config()
for suffix in ("", "-wal", "-shm"):
    p = cfg.DATABASE + suffix
    if os.path.exists(p):
        os.remove(p)
from app import create_app
create_app()
print("Database recreated with demo data at", cfg.DATABASE)
