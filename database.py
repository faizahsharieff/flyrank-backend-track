import os
import psycopg
from dotenv import load_dotenv
import time

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


def get_connection():
    for _ in range(10):
        try:
            return psycopg.connect(DATABASE_URL)
        except psycopg.OperationalError:
            time.sleep(2)

    raise Exception("Could not connect to PostgreSQL")


def init_db():
    conn = get_connection()

    with conn.cursor() as cur:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            done BOOLEAN DEFAULT FALSE
        )
        """)

        cur.execute("SELECT COUNT(*) FROM tasks")
        count = cur.fetchone()[0]

        if count == 0:
            cur.execute("""
            INSERT INTO tasks(title, done)
            VALUES
            ('Learn Docker', FALSE),
            ('Learn Postgres', FALSE),
            ('Finish Assignment', FALSE)
            """)

    conn.commit()
    conn.close()