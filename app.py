from flask import Flask, render_template
from config import SECRET_KEY
from routes.auth import auth_bp
from routes.patient import patient_bp

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY

app.register_blueprint(auth_bp)
app.register_blueprint(patient_bp)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/emergency")
def emergency():
    # No login, no database, no AI. Emergency guidance must always load.
    return render_template("emergency.html")


if __name__ == "__main__":
    app.run(debug=True)