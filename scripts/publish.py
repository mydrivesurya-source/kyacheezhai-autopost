"""Publish today's queued Instagram posts for @kyacheezhai.in via the Instagram Graph API.
Queue files: queue/YYYY-MM-DD-HHMM-<slug>.json  (IST date + earliest IST post time). Fields:
  type: "image" | "carousel" | "reel" | "story"
  caption: str
  media: [url, ...]   (public URLs; for files in this repo use media/<name>)
Posted files are moved to queue/done/.
"""
import json, os, pathlib, time, urllib.parse, urllib.request, datetime, shutil, sys, subprocess

G = "https://graph.facebook.com/v21.0"
TOKEN = os.environ["IG_TOKEN"]; IG = os.environ["IG_USER_ID"]
REPO = os.environ.get("GITHUB_REPOSITORY", "")
RAW = f"https://raw.githubusercontent.com/{REPO}/main/"

def call(path, params, method="POST"):
    params = {**params, "access_token": TOKEN}
    data = urllib.parse.urlencode(params).encode()
    if method == "GET":
        req = urllib.request.Request(f"{G}/{path}?{data.decode()}")
    else:
        req = urllib.request.Request(f"{G}/{path}", data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise SystemExit(f"API error {e.code}: {e.read().decode()}")

def url(u): return u if u.startswith("http") else RAW + u.lstrip("/")

def wait_ready(cid, tries=60):
    for _ in range(tries):
        s = call(cid, {"fields": "status_code"}, "GET").get("status_code")
        if s == "FINISHED": return
        if s == "ERROR": raise SystemExit(f"container {cid} failed")
        time.sleep(10)
    raise SystemExit(f"container {cid} timed out")

def publish(post):
    t, cap, media = post["type"], post.get("caption", ""), [url(m) for m in post["media"]]
    if t == "image":
        cid = call(f"{IG}/media", {"image_url": media[0], "caption": cap})["id"]
    elif t == "reel":
        cid = call(f"{IG}/media", {"media_type": "REELS", "video_url": media[0], "caption": cap, "share_to_feed": "true"})["id"]
    elif t == "story":
        m = media[0]
        p = {"media_type": "STORIES"}
        p.update({"video_url": m} if m.lower().endswith(".mp4") else {"image_url": m})
        cid = call(f"{IG}/media", p)["id"]
    elif t == "carousel":
        kids = []
        for m in media[:10]:
            p = {"is_carousel_item": "true"}
            p.update({"media_type": "VIDEO", "video_url": m} if m.lower().endswith(".mp4") else {"image_url": m})
            k = call(f"{IG}/media", p)["id"]; wait_ready(k); kids.append(k)
        cid = call(f"{IG}/media", {"media_type": "CAROUSEL", "children": ",".join(kids), "caption": cap})["id"]
    else:
        raise SystemExit(f"unknown type {t}")
    wait_ready(cid)
    return call(f"{IG}/media_publish", {"creation_id": cid})["id"]

def git(*a): return subprocess.run(["git", *a], capture_output=True, text=True)

def sync_push(msg):
    """Commit staged changes and push, rebasing on conflicts. True only if the push landed."""
    if git("commit", "-qm", msg).returncode != 0: return False
    for i in range(6):
        if git("pull", "-q", "--rebase", "origin", "main").returncode == 0 and git("push", "-q").returncode == 0: return True
        time.sleep(5 * (i + 1))
    return False

def claim(f, done):
    """At-most-once: move the item to queue/done and push BEFORE publishing. If the claim can't be pushed, don't publish."""
    if not os.environ.get("GITHUB_ACTIONS"): shutil.move(str(f), done / f.name); return True
    git("mv", str(f), str(done / f.name))
    if sync_push(f"Claim {f.name}"): return True
    git("reset", "-q", "--hard", "origin/main"); return False

def main():
    now = (datetime.datetime.utcnow() + datetime.timedelta(hours=5, minutes=30)).strftime("%Y-%m-%d-%H%M")
    only = sys.argv[1] if len(sys.argv) > 1 else None
    if os.environ.get("GITHUB_ACTIONS"): git("pull", "-q", "--rebase", "origin", "main")   # see items other runs already claimed
    q = pathlib.Path("queue"); done = q / "done"; done.mkdir(exist_ok=True)
    # due = slot time already passed (catches missed slots too); at most 2 per run to stay natural
    files = sorted(f for f in q.glob("*.json") if (f.name.startswith(only) if only else f.name[:15] <= now))[:3]
    if not files: print("nothing due at", now); return
    # Guard against double posts (e.g. a run that published but failed to push "Mark posted"):
    # skip any feed post whose caption already appears on the account's recent posts.
    try:
        recent = {(m.get("caption") or "").strip() for m in call(f"{IG}/media", {"fields": "caption", "limit": "25"}, "GET").get("data", [])}
    except SystemExit as e:
        print("could not read recent media:", e); recent = set()
    for f in files:
        post = json.loads(f.read_text())
        cap = (post.get("caption") or "").strip()
        if post.get("type") != "story" and cap and cap in recent:
            print("already on Instagram, skipping", f.name); shutil.move(str(f), done / f.name); continue
        if not f.exists(): print("already claimed", f.name); continue
        if not claim(f, done): print("could not claim, skipping", f.name); continue
        try:
            mid = publish(post)
        except SystemExit as e:
            print("API error on", f.name, e)
            if os.environ.get("GITHUB_ACTIONS"):
                git("mv", str(done / f.name), str(f)); sync_push(f"Unclaim {f.name} (publish failed)")
            continue
        print("published", f.name, "->", mid)

if __name__ == "__main__":
    main()
