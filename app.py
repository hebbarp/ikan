import os
from flask import Flask, render_template, request, session
from flask_sqlalchemy import SQLAlchemy

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

# ensure table exists under gunicorn too
with app.app_context():
    db.create_all()

@app.route("/", methods=["GET", "POST"])
def index():
    message = ""
    not_found_word = None

    if request.method == "POST":
        # main input (may be empty if user presses Add after a failed lookup)
        word = request.form.get("word", "").strip()

        # if user clicked Add with empty input, reuse the last missing word
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
                # not found on a normal check → remember for one-click add
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
