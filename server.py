from flask import Flask, render_template_string, request, redirect, session
import requests, base64, hashlib
import os

app = Flask(__name__)
app.secret_key = "secret123"
app.config['SESSION_TYPE'] = 'filesystem'

# ===== SETTINGS =====
import json
DB_FILE = "database.json"

# load db
def load_db():
    if not os.path.exists(DB_FILE):
        return []
    return json.load(open(DB_FILE))

# save db
def save_db(data):
    json.dump(data, open(DB_FILE, "w"), indent=4)

# ===== LOGIN =====
USERNAME = "admin"
PASSWORD = "1234"

# ===== LICENSE =====
def generate_license(user_id, hwid):
    raw = user_id + hwid + "ARS_SECRET"
    return hashlib.sha256(raw.encode()).hexdigest()[:16].upper()


# ===== LOGIN PAGE =====
@app.route("/", methods=["GET","POST"])
def login():
    if session.get("login"):
        return redirect("/dashboard")

    if request.method == "POST":
        if request.form["user"] == USERNAME and request.form["pass"] == PASSWORD:
            session["login"] = True
            return redirect("/dashboard")

    return """
    <style>
    body{background:#111;color:white;text-align:center;font-family:sans-serif}
    input,button{padding:10px;margin:10px;border-radius:5px}
    </style>
    <h2>Admin Login</h2>
    <form method="post">
    <input name="user" placeholder="Username"><br>
    <input name="pass" type="password" placeholder="Password"><br>
    <button>Login</button>
    </form>
    """
# ===== DASHBOARD =====
@app.route("/dashboard", methods=["GET","POST"])
def dashboard():
    if not session.get("login"):
        return redirect("/")

    db = load_db()

    # stats
    active = sum(1 for u in db if u["status"] == "ACTIVE")
    disabled = sum(1 for u in db if u["status"] == "DISABLED")

    if request.method == "POST":
        user = request.form.get("user")
        hwid = request.form.get("hwid")
        action = request.form.get("action")

        if action == "generate":
            lic = generate_license(user, hwid)

            db.append({
                "license": lic,
                "user": user,
                "hwid": hwid,
                "status": "ACTIVE"
            })

        elif action in ["disable", "enable"]:
            for u in db:
                if u["user"] == user:
                    u["status"] = "ACTIVE" if action == "enable" else "DISABLED"

        save_db(db)
        return redirect("/dashboard")   # ✅ sirf POST ke andar

    return render_template_string("""
    <style>
    body{background:#0f172a;color:white;font-family:sans-serif}
    .box{background:#1e293b;padding:15px;margin:10px;border-radius:10px}
    input,button{padding:8px;margin:5px;border-radius:5px;border:none}
    button{background:#2563eb;color:white;cursor:pointer}
    table{border-collapse:collapse}
    td,th{padding:8px;border-bottom:1px solid #333}
    </style>

    <h2>🔥 Admin Dashboard</h2>

    <div class="box">
    Total Users: {{users|length}} |
    Active: {{active}} |
    Disabled: {{disabled}}
    </div>

    <div class="box">
    <form method="post">
    <input name="user" placeholder="User ID">
    <input name="hwid" placeholder="HWID"><br>
    <button name="action" value="generate">Generate</button>
    </form>
    </div>

    <div class="box">
    <input id="search" placeholder="Search user..." onkeyup="filter()">
    <table id="table" width="100%">
    <tr>
        <th>License</th>
        <th>User</th>
        <th>HWID</th>
        <th>Status</th>
        <th>Action</th>
    </tr>

    {% for u in users %}
    <tr>
        <td>{{u.license}}</td>
        <td>{{u.user}}</td>
        <td>{{u.hwid}}</td>
        <td>{{u.status}}</td>
        <td>
            <form method="post">
                <input type="hidden" name="user" value="{{u.user}}">
                <button name="action" value="enable">Enable</button>
                <button name="action" value="disable">Disable</button>
            </form>
        </td>
    </tr>
    {% endfor %}
    </table>
    </div>

    <script>
    function filter(){
        let input=document.getElementById("search").value.toLowerCase();
        let rows=document.querySelectorAll("#table tr");
        rows.forEach((r,i)=>{
            if(i==0)return;
            r.style.display=r.innerText.toLowerCase().includes(input)?"":"none";
        });
    }
    </script>
    """, users=db, active=active, disabled=disabled)

@app.route("/api/check")
def api_check():
    user = request.args.get("user")
    hwid = request.args.get("hwid")

    db = load_db()

    for u in db:
        if u["user"] == user and u["hwid"] == hwid:
            return {
                "status": u["status"],
                "license": u["license"]
            }

    return {"status": "INVALID"}
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
