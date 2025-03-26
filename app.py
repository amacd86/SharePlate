from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Simulated current user
CURRENT_USER = "gus"

# Available groups
GROUPS = ["Aldrich Group", "Lincoln Group", "Cabot Group"]

# In-memory list of shared plates
shared_plates = []

@app.route("/", methods=["GET", "POST"])
def index():
    selected_group = request.args.get("group", "Aldrich Group")

    if request.method == "POST":
        group_selected_from_form = request.form["group"]
        plate = {
            "user": CURRENT_USER,
            "group": group_selected_from_form,
            "description": request.form["description"],
            "available_until": request.form.get("available_until", "")
        }
        shared_plates.append(plate)
        return redirect(url_for("index", group=group_selected_from_form))

    # Show only plates from the selected group
    group_feed = [plate for plate in shared_plates if plate["group"] == selected_group]

    return render_template("index.html", plates=group_feed, group_name=selected_group, groups=GROUPS)

if __name__ == "__main__":
    app.run(debug=True)
