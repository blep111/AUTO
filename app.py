from flask import Flask, request, render_template, redirect, url_for, session
import requests, re, random, os

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "change_this_secret_in_prod")

ua_list = [
    "Mozilla/5.0 (Linux; Android 10; Wildfire E Lite)...",
    "Mozilla/5.0 (Linux; Android 11; KINGKONG 5 Pro)...",
    "Mozilla/5.0 (Linux; Android 11; G91 Pro)..."
]

ACCESS_KEY = "gabpogi"  # Your hidden approval key

def extract_token(cookie, ua):
    try:
        cookies = {i.split('=')[0]: i.split('=')[1] for i in cookie.split('; ') if '=' in i}
        res = requests.get("https://business.facebook.com/business_locations",
                           headers={"user-agent": ua, "referer": "https://www.facebook.com/"},
                           cookies=cookies)
        token_match = re.search(r'(EAAG\w+)', res.text)
        return token_match.group(1) if token_match else None
    except:
        return None

@app.route("/")
def index():
    if not session.get("approved"):
        return redirect(url_for("access"))
    return render_template("index.html")

@app.route("/access", methods=["GET", "POST"])
def access():
    if session.get("approved"):
        return redirect(url_for("index"))

    error = None
    if request.method == "POST":
        key = request.form.get("access_key", "").strip()
        if key == ACCESS_KEY:
            session["approved"] = True
            return redirect(url_for("index"))
        else:
            error = "Invalid access key. Please try again."
    return render_template("access.html", error=error)

@app.route("/logout")
def logout():
    session.pop("approved", None)
    return redirect(url_for("access"))

@app.route("/api/share", methods=["POST"])
def share():
    if not session.get("approved"):
        # Block all non-approved attempts silently
        return "", 403

    data = request.get_json(force=True)
    cookie = data.get("cookie")
    post_link = data.get("link")
    limit = int(data.get("limit", 0))
    if not cookie or not post_link or not limit:
        return "", 400

    ua = random.choice(ua_list)
    token = extract_token(cookie, ua)
    if not token:
        return "", 401

    cookies = {i.split('=')[0]: i.split('=')[1] for i in cookie.split('; ') if '=' in i}
    success = 0
    for _ in range(limit):
        res = requests.post(
            "https://graph.facebook.com/v18.0/me/feed",
            params={"link": post_link, "access_token": token, "published": 0},
            headers={"user-agent": ua},
            cookies=cookies
        )
        if "id" in res.text:
            success += 1
        else:
            break
    return "", 204  # empty response (no visible JSON)
    
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
