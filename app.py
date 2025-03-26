from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
import os
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"
app.config["UPLOAD_FOLDER"] = "static/uploads"

if not os.path.exists(app.config["UPLOAD_FOLDER"]):
    os.makedirs(app.config["UPLOAD_FOLDER"])

# Mock user data
USERS = {
    "Gus": {"group": "Aldrich Group", "avatar": "gus.jpg"},
    "Tessa": {"group": "Aldrich Group", "avatar": "tessa.jpg"},
    "Rachel": {"group": "Aldrich Group", "avatar": "default.jpg"},
    "Ollie": {"group": "Lincoln Group", "avatar": "ollie.jpg"},
    "Gel": {"group": "Lincoln Group", "avatar": "gel.jpg"},
    "Izzy": {"group": "Lincoln Group", "avatar": "default.jpg"},
    "Dylan": {"group": "Lincoln Group", "avatar": "dylan.jpg"},
    "Jackson": {"group": "Cabot Group", "avatar": "jackson.jpg"},
    "Kristen": {"group": "Cabot Group", "avatar": "kristen.jpg"},
    "Mark": {"group": "Cabot Group", "avatar": "default.jpg"},
    "Abby": {"group": "Cabot Group", "avatar": "abby.jpg"}
}

# In-memory data store
FEED = []
MESSAGES = {}

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        group = request.form["group"]
        if username not in USERS:
            USERS[username] = {"group": group, "avatar": "default.jpg"}
            session["user"] = username
            session["group"] = group
            return redirect(url_for("index"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        if username in USERS:
            session["user"] = username
            session["group"] = USERS[username]["group"]
            return redirect(url_for("index"))
        else:
            return redirect(url_for("register"))
    return render_template("login.html", users=USERS.keys())

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/")
def index():
    if "user" not in session:
        return redirect(url_for("login"))

    current_user = session["user"]
    group_name = session["group"]
    now = datetime.now()
    group_feed = [plate for plate in FEED if plate["group"] == group_name and (not plate['available_until'] or datetime.strptime(plate['available_until'], '%Y-%m-%d %H:%M:%S') > now)]
    return render_template("index.html", plates=group_feed, group_name=group_name, user=current_user, USERS=USERS)

@app.route("/share", methods=["POST"])
def share():
    if "user" not in session:
        return redirect(url_for("login"))

    description = request.form.get("description")
    available_until = request.form.get("available_until")
    file = request.files.get("image")

    filename = None
    if file and file.filename:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

    FEED.append({
        "user": session["user"],
        "group": session["group"],
        "description": description,
        "available_until": available_until,
        "timestamp": datetime.now(),
        "image": filename
    })
    return redirect(url_for("index"))

@app.route("/group")
def group():
    if "user" not in session:
        return redirect(url_for("login"))

    current_user = session["user"]
    group_name = session["group"]
    group_members = [user for user, data in USERS.items() if data["group"] == group_name]
    return render_template("group.html", group_name=group_name, user=current_user, group_members=group_members, USERS=USERS)

@app.route("/messages")
def messages():
    if "user" not in session:
        return redirect(url_for("login"))

    current_user = session["user"]
    user_messages = MESSAGES.get(current_user, {})
    return render_template("messages.html", user=current_user, messages=user_messages, USERS=USERS)

@app.route("/message/<recipient>", methods=["GET", "POST"])
def message_user(recipient):
    if "user" not in session:
        return redirect(url_for("login"))

    current_user = session["user"]

    # Ensure message structure exists for both sender and recipient
    if current_user not in MESSAGES:
        MESSAGES[current_user] = {}
    if recipient not in MESSAGES:
        MESSAGES[recipient] = {}
    if recipient not in MESSAGES[current_user]:
        MESSAGES[current_user][recipient] = []
    if current_user not in MESSAGES[recipient]:
        MESSAGES[recipient][current_user] = []

    if request.method == "POST":
        msg = request.form.get("message")
        timestamp = datetime.now()
        message_data = {
            "from": current_user,
            "to": recipient,
            "text": msg,
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M")
        }
        MESSAGES[current_user][recipient].append(message_data)
        MESSAGES[recipient][current_user].append(message_data)
        return redirect(url_for("message_user", recipient=recipient))

    conversation = MESSAGES[current_user].get(recipient, [])
    conversation.sort(key=lambda x: x["timestamp"])
    return render_template("message_user.html", user=current_user, recipient=recipient, conversation=conversation, USERS=USERS)

if __name__ == "__main__":
    app.run(debug=True)
