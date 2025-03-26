from flask import Flask, render_template, request, redirect, url_for, session
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "supersecretkey"

UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

USERS = {
    "Gus": "Aldrich Group",
    "Tessa": "Aldrich Group",
    "Rachel": "Aldrich Group",
    "Ollie": "Lincoln Group",
    "Gel": "Lincoln Group",
    "Izzy": "Lincoln Group",
    "Dylan": "Lincoln Group",
    "Jackson": "Cabot Group",
    "Kristen": "Cabot Group",
    "Mark": "Cabot Group",
    "Abby": "Cabot Group"
}

shared_plates = []

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        if username in USERS:
            session["user"] = username
            session["group"] = USERS[username]
            return redirect(url_for("index"))
    return render_template("login.html", users=USERS.keys())

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/", methods=["GET", "POST"])
def index():
    if "user" not in session:
        return redirect(url_for("login"))

    current_user = session["user"]
    group_name = session["group"]

    if request.method == "POST":
        description = request.form["description"]
        available_until = request.form.get("available_until", "")
        image_file = request.files.get("image")
        image_path = None

        if image_file and allowed_file(image_file.filename):
            filename = secure_filename(image_file.filename)
            save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            image_file.save(save_path)
            image_path = f"uploads/{filename}"

        plate = {
            "user": current_user,
            "group": group_name,
            "description": description,
            "available_until": available_until,
            "image": image_path
        }
        shared_plates.append(plate)
        return redirect(url_for("index"))

    group_feed = [p for p in shared_plates if p["group"] == group_name]
    return render_template("index.html", plates=group_feed, group_name=group_name, user=current_user)

if __name__ == "__main__":
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)
