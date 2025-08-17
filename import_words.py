# import_words.py
import os
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String
from sqlalchemy.exc import IntegrityError

def normalize_db_url(url: str) -> str:
    return url.replace("postgres://", "postgresql://", 1) if url and url.startswith("postgres://") else url

DB_URL = normalize_db_url(os.getenv("SQLALCHEMY_DATABASE_URI", "sqlite:///padagalu.db"))
PADAGALU_PATH = os.getenv("PADAGALU_PATH", "padagalu.txt")

engine = create_engine(DB_URL, future=True)
metadata = MetaData()

# Table name matches your app's model: __tablename__ = "word"
word = Table(
    "word",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("text", String(100), unique=True, nullable=False),
)

def create_schema():
    metadata.create_all(engine)

def load_words(path=PADAGALU_PATH):
    if not os.path.exists(path):
        print(f"[warn] {path} not found; nothing to import.")
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [w.strip() for w in f if w.strip()]

def insert_words(words):
    inserted = 0
    with engine.begin() as conn:
        for w in words:
            try:
                conn.execute(word.insert().values(text=w))
                inserted += 1
            except IntegrityError:
                # duplicate; skip
                conn.rollback()  # safe to call in begin(); resets failed SAVEPOINT
            except Exception as e:
                print(f"[skip] '{w}': {e}")
    print(f"[done] attempted inserts: {len(words)}, new rows: {inserted}")

if __name__ == "__main__":
    print(f"[info] DB = {DB_URL}")
    create_schema()
    ws = load_words()
    print(f"[info] found {len(ws)} words in padagalu.txt")
    insert_words(ws)