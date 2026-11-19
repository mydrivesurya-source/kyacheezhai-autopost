"""Build the Kya Cheez Hai shop site into docs/ (served by GitHub Pages).
Lists every reel product whose post time (IST) has passed, newest first."""
import json, glob, os, datetime, html, re
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAG="kyacheezhai-21"
now=(datetime.datetime.utcnow()+datetime.timedelta(hours=5,minutes=30)).strftime("%Y-%m-%d-%H%M")
items=[]
for f in sorted(glob.glob(os.path.join(ROOT,"specs","*.json"))):
    stem=os.path.basename(f)[:-5]
    if stem[:15]>now: continue
    d=json.load(open(f,encoding="utf-8"))
    if d.get("kind")!="reel" or not d.get("asin"): continue
    name=(d.get("brand","")+" "+" ".join(d.get("name",[]))).strip()
    items.append(dict(id=stem[16:],date=stem[:10],name=name,cat=d.get("category","Finds"),img=d["images"][0],
        story=d.get("problem",""),feat=d.get("feat",[])[:3],rating=d.get("rating",""),reviews=d.get("reviews",""),
        bought=d.get("bought",""),url=f"https://www.amazon.in/dp/{d['asin']}?tag={TAG}"))
items.sort(key=lambda x:x["date"],reverse=True)
cats=sorted({i["cat"] for i in items})
e=html.escape
cards="\n".join(f'''<article class="card" data-cat="{e(i['cat'])}" id="{e(i['id'])}">
 <div class="ph"><img loading="lazy" src="{e(i['img'])}" alt="{e(i['name'])}"></div>
 <div class="bd"><span class="cat">{e(i['cat'])}</span><h2>{e(i['name'])}</h2>
 <p class="story">{e(i['story'])}</p>
 <ul>{"".join(f"<li>{e(x)}</li>" for x in i['feat'])}</ul>
 <p class="proof">&#9733; {e(i['rating'])}/5 &middot; {e(i['reviews'])} ratings{(" &middot; "+e(i['bought'])+" bought last month") if i['bought'] else ""}</p>
 <a class="btn" href="{e(i['url'])}" target="_blank" rel="nofollow sponsored noopener">Check price on Amazon</a></div></article>''' for i in items)
chips='<button class="chip on" data-c="all">All</button>'+"".join(f'<button class="chip" data-c="{e(c)}">{e(c)}</button>' for c in cats)
page=f'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Kya Cheez Hai – daily finds worth buying</title>
<meta name="description" content="Handpicked, well-rated Amazon India finds from @kyacheezhai.in – watches, beauty, bags, travel, home and more.">
<meta property="og:title" content="Kya Cheez Hai – daily finds"><meta property="og:image" content="{e(items[0]['img']) if items else ''}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Poppins:wght@500;700&display=swap" rel="stylesheet">
<style>
:root{{--ch:#121212;--co:#FF5A4E;--cr:#F8F4EE;--mi:#3DDC97;--mu:#6b655f}}
*{{box-sizing:border-box}}body{{margin:0;font-family:Poppins,system-ui,sans-serif;background:var(--cr);color:var(--ch)}}
header{{background:var(--ch);color:#fff;padding:28px 20px 22px;text-align:center}}
.logo{{display:inline-block;background:var(--co);padding:6px 14px;border-radius:10px;font-weight:700;letter-spacing:.5px}}
header p{{margin:12px 0 0;color:#d8d2ca;font-size:15px}}
.ig{{color:var(--mi);text-decoration:none;font-weight:700}}
.chips{{display:flex;gap:8px;overflow-x:auto;padding:14px 16px;position:sticky;top:0;background:var(--cr);z-index:2}}
.chip{{border:1.5px solid var(--ch);background:#fff;border-radius:999px;padding:7px 14px;font:500 14px Poppins;white-space:nowrap;cursor:pointer}}
.chip.on{{background:var(--ch);color:#fff}}
main{{max-width:1100px;margin:0 auto;padding:0 14px 30px;display:grid;gap:16px;grid-template-columns:repeat(auto-fill,minmax(260px,1fr))}}
.card{{background:#fff;border-radius:18px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,.06);display:flex;flex-direction:column}}
.ph{{aspect-ratio:1/1;display:flex;align-items:center;justify-content:center;background:#fff;padding:14px}}
.ph img{{max-width:100%;max-height:100%;object-fit:contain}}
.bd{{padding:4px 18px 18px;display:flex;flex-direction:column;flex:1}}
.cat{{font-size:12px;font-weight:700;color:var(--co);text-transform:uppercase;letter-spacing:.6px}}
h2{{font-size:18px;margin:4px 0 6px}}.story{{color:var(--mu);margin:0 0 6px;font-size:14px}}
ul{{margin:0 0 8px;padding-left:18px;font-size:14px}}.proof{{font-size:13px;color:var(--mu);margin:0 0 14px}}
.btn{{margin-top:auto;background:var(--co);color:#fff;text-align:center;text-decoration:none;font-weight:700;padding:13px;border-radius:12px}}
footer{{text-align:center;color:var(--mu);font-size:12px;padding:10px 20px 30px;max-width:700px;margin:0 auto}}
</style></head><body>
<header><span class="logo">KYA CHEEZ HAI</span><p>Daily finds worth buying &middot; as seen on <a class="ig" href="https://www.instagram.com/kyacheezhai.in/">@kyacheezhai.in</a></p></header>
<nav class="chips">{chips}</nav>
<main>{cards}</main>
<footer>As an Amazon Associate we earn from qualifying purchases. Prices and availability are shown on Amazon at the time of purchase. Product photos are from the listings; our reel host is AI-generated.</footer>
<script>document.querySelectorAll('.chip').forEach(b=>b.onclick=()=>{{document.querySelectorAll('.chip').forEach(x=>x.classList.remove('on'));b.classList.add('on');
document.querySelectorAll('.card').forEach(c=>c.style.display=(b.dataset.c==='all'||c.dataset.cat===b.dataset.c)?'':'none')}});
if(location.hash){{const el=document.querySelector(location.hash);if(el)el.scrollIntoView()}}</script>
</body></html>'''
os.makedirs(os.path.join(ROOT,"docs"),exist_ok=True)
open(os.path.join(ROOT,"docs","index.html"),"w",encoding="utf-8").write(page)
open(os.path.join(ROOT,"docs",".nojekyll"),"w").write("")
print("site:",len(items),"products")
