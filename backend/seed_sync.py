"""
Seed script sincrono - cria usuario admin.
Uso: python seed_sync.py
"""
import os
import sys
import sqlite3
import uuid

sys.path.insert(0, os.path.dirname(__file__))

from app.services.auth import hash_password

os.makedirs("data", exist_ok=True)

db_path = os.path.join("data", "correcao.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        hashed_password TEXT NOT NULL,
        full_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS corrections (
        id TEXT PRIMARY KEY,
        teacher_id TEXT NOT NULL,
        student_name TEXT NOT NULL,
        student_id TEXT NOT NULL,
        class_name TEXT NOT NULL,
        discipline TEXT DEFAULT '',
        original_filename TEXT NOT NULL,
        original_path TEXT NOT NULL,
        processed_path TEXT,
        status TEXT DEFAULT 'pending',
        confidence REAL,
        result_json TEXT,
        error_message TEXT,
        image_width INTEGER,
        image_height INTEGER,
        file_size_bytes INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

cursor.execute("SELECT id FROM users WHERE username = ?", ("admin",))
if cursor.fetchone():
    print("Usuario admin ja existe.")
else:
    hashed = hash_password("admin123")
    cursor.execute(
        "INSERT INTO users (id, username, hashed_password, full_name, email, is_active) VALUES (?, ?, ?, ?, ?, 1)",
        (str(uuid.uuid4()), "admin", hashed, "Administrador", "admin@faculdade.edu"),
    )
    conn.commit()
    print("Usuario admin criado: admin / admin123")

conn.close()
