import os
from flask import Flask, render_template, request, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from prosody import maatra_count
from generator import generate_dwipadi

def normalize_db_url(url: str) -> str:
    return url.replace("postgres://", "postgresql://", 1) if url and url.startswith("postgres://") else url

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret")

DATABASE_URL = normalize_db_url(os.getenv("SQLALCHEMY_DATABASE_URI", "sqlite:///padagalu.db"))
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class Word(db.Model):
    __tablename__ = "word"
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(100), unique=True, nullable=False)

class Dwipadi(db.Model):
    __tablename__ = "dwipadi"
    id = db.Column(db.Integer, primary_key=True)
    line1 = db.Column(db.Text, nullable=False)
    line2 = db.Column(db.Text, nullable=False)
    score = db.Column(db.Float)

# Ensure tables exist under gunicorn too
with app.app_context():
    db.create_all()

@app.route("/", methods=["GET", "POST"])
def index():
    message = ""
    not_found_word = None

    if request.method == "POST":
        word = request.form.get("word", "").strip()
        if "add" in request.form and not word:
            word = (session.get("last_not_found") or "").strip()

        if word:
            existing = Word.query.filter_by(text=word).first()
            if existing and "add" not in request.form:
                message = f"✅ ಸೂಪರ್! ಪದ '{word}' ಪದಕೋಶದಲ್ಲಿ ಇದೆ."
            elif "add" in request.form:
                if existing:
                    message = f"ℹ️ ಪದ '{word}' ಈಗಾಗಲೇ ಇದೆ."
                else:
                    db.session.add(Word(text=word))
                    db.session.commit()
                    message = f"✨ ಪದ '{word}' ಸೇರಿಸಲ್ಪಟ್ಟಿದೆ."
                    session.pop("last_not_found", None)
            else:
                session["last_not_found"] = word
                not_found_word = word
                message = f"❌ ಪದ '{word}' ಪದಕೋಶದಲ್ಲಿಲ್ಲ. ಸೇರಿಸಬೇಕೇ?"
        else:
            message = "⚠️ ಪದ ಖಾಲಿ ಇದೆ."

    words_count = Word.query.count()
    return render_template(
        "index.html",
        message=message,
        count=words_count,
        not_found_word=session.get("last_not_found")
    )

@app.route("/dwipadi", methods=["GET", "POST"])
def dwipadi():
    results = []
    saved_msg = ""
    # read from querystring on GET, but from form on POST
    target = 12
    from flask import request
    if request.method == "GET":
        try:
            target = int(request.args.get("target", target))
        except Exception:
            target = 12
    else:
        try:
            target = int(request.form.get("target", target) or target)
        except Exception:
            target = 12

    if request.method == "POST":
        if "generate" in request.form:
            # pull words from DB
            from sqlalchemy import text
            rows = db.session.execute(text("SELECT text FROM word")).fetchall()
            words = [r[0] for r in rows]
            # Vary the seed each request for fresh results
            from time import time_ns
            results = generate_dwipadi(words, target=target, k=5, seed=(time_ns() & 0xFFFF))
        elif "save" in request.form:
            l1 = request.form.get("l1","").strip()
            l2 = request.form.get("l2","").strip()
            score = float(request.form.get("score","0") or 0)
            if l1 and l2:
                db.session.add(Dwipadi(line1=l1, line2=l2, score=score))
                db.session.commit()
                saved_msg = "💾 ಉಳಿಸಲಾಗಿದೆ!"

    # show last 10 saved for inspiration
    recent = Dwipadi.query.order_by(Dwipadi.id.desc()).limit(10).all()
    return render_template("dwipadi.html",
                           target=target,
                           results=results,
                           recent=recent,
                           saved_msg=saved_msg)
@app.get("/health")
def health():
    db.session.execute(text("SELECT 1"))
    return "ok", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
