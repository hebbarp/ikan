# import_words.py
import os
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, text

def normalize_db_url(url: str) -> str:
    return url.replace("postgres://", "postgresql://", 1) if url and url.startswith("postgres://") else url

DB_URL = normalize_db_url(os.getenv("SQLALCHEMY_DATABASE_URI", "sqlite:///padagalu.db"))
PADAGALU_PATH = os.getenv("PADAGALU_PATH", "padagalu.txt")

engine = create_engine(DB_URL, future=True)
metadata = MetaData()

# Table name matches app: __tablename__ = "word"
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
    dialect = engine.dialect.name  # 'sqlite', 'postgresql', etc.
    if dialect == "sqlite":
        upsert_sql = text("INSERT OR IGNORE INTO word(text) VALUES (:t)")
    else:  # assume PostgreSQL
        upsert_sql = text("INSERT INTO word(text) VALUES (:t) ON CONFLICT (text) DO NOTHING")

    inserted = 0
    with engine.begin() as conn:
        for w in words:
            try:
                conn.execute(upsert_sql, {"t": w})
                inserted += 1  # counts attempts; duplicates are ignored silently
            except Exception as e:
                # Do NOT call conn.rollback() inside 'begin()' block.
                # Just skip and continue.
                print(f"[skip] '{w}': {e}")
                continue
    # Show total rows
    with engine.connect() as conn:
        total = conn.execute(text("SELECT COUNT(*) FROM word")).scalar_one()
    print(f"[done] attempted: {len(words)}, total rows now: {total}")

if __name__ == "__main__":
    print(f"[info] DB = {DB_URL}")
    create_schema()
    ws = load_words()
    print(f"[info] found {len(ws)} words in {PADAGALU_PATH}")
    insert_words(ws)