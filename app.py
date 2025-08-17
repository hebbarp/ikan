import os
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy

def normalize_db_url(url: str) -> str:
    # Render often supplies postgres://; SQLAlchemy expects postgresql://
    return url.replace("postgres://", "postgresql://", 1) if url and url.startswith("postgres://") else url

app = Flask(__name__)
DATABASE_URL = normalize_db_url(os.getenv("SQLALCHEMY_DATABASE_URI", "sqlite:///padagalu.db"))
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class Word(db.Model):
    __tablename__ = "words"
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(100), unique=True, nullable=False)

# ✅ Ensure tables exist even under Gunicorn (not just python app.py)
with app.app_context():
    db.create_all()

@app.route("/", methods=["GET", "POST"])
def index():
    message = ""
    if request.method == "POST":
        word = request.form["word"].strip()
        if word.lower() == "ಸಾಕು":
            message = "🙏 ಧನ್ಯವಾದಗಳು. ಪದಕೋಶದಿಂದ ಹೊರಬರುತ್ತಿದ್ದೇವೆ."
        else:
            existing = Word.query.filter_by(text=word).first()
            if existing:
                message = f"✅ ಸೂಪರ್! ಪದ '{word}' ಪದಕೋಶದಲ್ಲಿ ಇದೆ."
            else:
                if "add" in request.form:
                    new_word = Word(text=word)
                    db.session.add(new_word)
                    db.session.commit()
                    message = f"✨ ಪದ '{word}' ಸೇರಿಸಲ್ಪಟ್ಟಿದೆ."
                else:
                    message = f"❌ ಪದ '{word}' ಪದಕೋಶದಲ್ಲಿ ಇಲ್ಲ. ಸೇರಿಸಬೇಕೇ?"

    words_count = Word.query.count()
    return render_template("index.html", message=message, count=words_count)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))