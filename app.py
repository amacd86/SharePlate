from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
import os
from werkzeug.utils import secure_filename
from datetime import datetime
from models import db, User, Plate
from werkzeug.security import check_password_hash, generate_password_hash  # Ensure this is imported
import time  # Add this import for timestamping filenames
app = Flask(__name__)
app.secret_key = "supersecretkey"
app.secret_key = "supersecretkey"
app.config["UPLOAD_FOLDER"] = "static/uploads"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///shareplate.db"
db.init_app(app)

if not os.path.exists(app.config["UPLOAD_FOLDER"]):
    os.makedirs(app.config["UPLOAD_FOLDER"])

VALID_INVITE_CODES = {
    "ALDRICH123": "Aldrich Group",
    "LINCOLN456": "Lincoln Group",
    "CABOT789": "Cabot Group"
}

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        invite_code = request.form["invite_code"]

        valid_invites = {
            "ALD123": "Aldrich Group",
            "CAB456": "Cabot Group",
            "LNC789": "Lincoln Group"
        }

        if invite_code not in valid_invites:
            return "Invalid invite code."

        group = valid_invites[invite_code]

        if User.query.filter_by(email=email).first():
            return "Email already registered."

        new_user = User(name=name, email=email, group=group)
        new_user.set_password(password)  # Hash the password
        db.session.add(new_user)
        db.session.commit()

        session["user_id"] = new_user.id
        return redirect(url_for("home"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            return redirect(url_for("home"))
        else:
            return "Invalid email or password"

    return render_template("login.html")  # No `users=` passed here

@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect(url_for("login"))
    user = User.query.get(session["user_id"])
    return render_template("profile.html", user=user)

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

@app.template_filter("datetimeformat")
def datetimeformat(value):
    try:
        dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%-I:%M %p")  # 7:30 PM
    except Exception:
        return value

@app.route("/upload_avatar", methods=["POST"])
def upload_avatar():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    file = request.files["avatar"]
    if file and file.filename:
        filename = f"{int(time.time())}_{secure_filename(file.filename)}"  # Append timestamp to filename
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        user = User.query.get(session["user_id"])
        user.avatar = filename  # Save filename in the database
        db.session.commit()
        return redirect(url_for("profile"))

    return "No file selected"

@app.route("/change_password", methods=["GET", "POST"])
def change_password():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])

    if request.method == "POST":
        current_password = request.form["current_password"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        if not check_password_hash(user.password, current_password):
            return "❌ Current password is incorrect"

        if new_password != confirm_password:
            return "❌ New passwords do not match"

        user.password = generate_password_hash(new_password)
        db.session.commit()
        return redirect(url_for("settings"))

    return render_template("change_password.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/settings", methods=["GET", "POST"])
def settings():
    print("🛠️ Entered settings route")
    user = User.query.get(session["user_id"])
    print("🔍 Loaded user:", user.name)

    if request.method == "POST":
        # Feed visibility
        visibility = request.form.get("feed_visibility")
        if visibility:
            user.feed_visibility = visibility

        # Group joining
        invite_code = request.form.get("invite_code")
        group = VALID_INVITE_CODES.get(invite_code)
        if group:
            user.group = group
        elif invite_code:
            return "Invalid invite code", 400

        # Password change
        new_password = request.form.get("new_password")
        if new_password:
            user.password = generate_password_hash(new_password)

        # Avatar upload
        avatar_file = request.files.get("avatar")
        if avatar_file and avatar_file.filename:
            filename = secure_filename(avatar_file.filename)
            avatar_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            avatar_file.save(avatar_path)
            user.avatar = filename

        db.session.commit()
        return redirect(url_for("home"))

    return render_template("settings.html", user=user)

@app.route("/")
def home():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])

    # If user hasn't completed settings, show them a soft reminder screen
    if not user.group or not user.feed_visibility:
        return render_template("index.html", user_name=user.name, show_settings_link=True)

    group_name = user.group

    plates = (
        Plate.query
        .join(User)
        .filter(User.group == group_name)  # Filter plates by group
        .order_by(Plate.timestamp.desc())
        .all()
    )

    # Debugging: Log plates in the group feed
    print("📦 Plates in group feed:")
    for p in plates:
        print(f"➡️ {p.title}, {p.image}")
        if p.image:
            print("🧪 Would generate image URL:", url_for('static', filename='uploads/' + p.image))

    return render_template("index.html", plates=plates, group_name=group_name, user_name=user.name)

# Temporary route to debug all plates in the database
@app.route("/debug_plates")
def debug_plates():
    plates = Plate.query.all()
    return "<br>".join([f"{p.title} — {p.image}" for p in plates])

@app.route("/debug_feed")
def debug_feed():
    plates = Plate.query.all()
    output = []

    for plate in plates:
        output.append(
            f"<strong>{plate.title}</strong><br>"
            f"Description: {plate.description}<br>"
            f"Image: {plate.image}<br>"
            f"User ID: {plate.user_id}<br>"
            f"Timestamp: {plate.timestamp}<br>"
            f"<hr>"
        )

    return "<h1>All Plates in DB</h1>" + "<br>".join(output)

@app.route("/reserve/<int:plate_id>")
def reserve_plate(plate_id):
    plate = Plate.query.get_or_404(plate_id)
    plate.interested += 1
    db.session.commit()
    return redirect(url_for("home"))

@app.route("/share", methods=["POST"])
def share():
    if "user" not in session:
        return redirect(url_for("login"))

    description = request.form.get("description")
    date_part = request.form.get("available_date")
    time_part = request.form.get("available_time")
    file = request.files.get("image")

    filename = None
    if file and file.filename:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

    available_until = None
    if date_part and time_part:
        try:
            available_until_dt = datetime.strptime(f"{date_part} {time_part}", "%Y-%m-%d %H:%M")
            available_until = available_until_dt.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            print("⚠️ Invalid date/time format")

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
    if "user_id" not in session:
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])
    group_name = user.group
    group_members = [u.name for u in User.query.filter_by(group=group_name).all()]
    return render_template("group.html", group_name=group_name, user=user, group_members=group_members)

@app.route("/messages")
def messages():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])
    user_name = user.name
    user_messages = MESSAGES.get(user_name, {})
    return render_template("messages.html", user=user_name, messages=user_messages, USERS=USERS)

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        user = User.query.get(session["user_id"])
        title = request.form.get("title")
        description = request.form.get("description")
        file = request.files.get("image")

        filename = None
        if file and file.filename:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(file_path)
            print("📸 Uploaded image filename:", filename)  # Debugging print
            print("📂 Saved to:", file_path)  # Debugging print

        new_plate = Plate(
            user_id=user.id,
            title=title,
            description=description,
            image=filename,  # ✅ Save the filename to the database
            timestamp=datetime.now(),
            interested=0
        )

        db.session.add(new_plate)
        db.session.commit()

        return redirect(url_for("home"))

    return render_template("upload.html")

# Ensure this is the only message_user function
@app.route("/message/<recipient>", methods=["GET", "POST"])
def message_user(recipient):
    if "user" not in session:
        return redirect(url_for("login"))

    current_user = session["user"]

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

@app.route("/debug_uploads")
def debug_uploads():
    try:
        folder = app.config["UPLOAD_FOLDER"]
        files = os.listdir(folder)
        return "<h2>Files in static/uploads:</h2><ul>" + "".join(f"<li>{f}</li>" for f in files) + "</ul>"
    except FileNotFoundError:
        return "<h1>Uploads folder not found</h1>"

if __name__ == "__main__":
    app.run(debug=True)
