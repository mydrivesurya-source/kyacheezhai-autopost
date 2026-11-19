"""Build the Kya Cheez Hai shop site into docs/ (GitHub Pages).
Lists every reel product whose post time (IST) has passed, newest first.

CLICK TRACKING (Meta pixel "KYA CHEEZ HAI", dataset 1508832264448418) — never remove:
- Main page fires PageView; a visit arriving with ?q= (ManyChat DM link) also fires DMVisit.
- Every shop button links to go/<spec-slug>/?src=<dm|instagram|direct>. That page fires
  ShopClick + ViewContent (content_ids=[slug], content_category, store, source) and then
  forwards to the store with the affiliate tag. Shop clicks per product = hits on /go/<slug>/."""
import json, glob, os, datetime, html, shutil, urllib.parse
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAG="kyacheezhai-21"; IG="https://www.instagram.com/kyacheezhai.in/"
PIXEL="1508832264448418"
def pixel_head(extra=""):
    return (f"<script>!function(f,b,e,v,n,t,s){{if(f.fbq)return;n=f.fbq=function(){{n.callMethod?"
            f"n.callMethod.apply(n,arguments):n.queue.push(arguments)}};if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;"
            f"n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;t.src=v;s=b.getElementsByTagName(e)[0];"
            f"s.parentNode.insertBefore(t,s)}}(window,document,'script','https://connect.facebook.net/en_US/fbevents.js');"
            f"fbq('init','{PIXEL}');fbq('track','PageView');{extra}</script>"
            f'<noscript><img height="1" width="1" style="display:none" alt="" src="https://www.facebook.com/tr?id={PIXEL}&ev=PageView&noscript=1"></noscript>')
now=(datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(hours=5,minutes=30)).strftime("%Y-%m-%d-%H%M")
items=[]
shown=set()  # product images already featured in a posted carousel -> list those products now
for f in sorted(glob.glob(os.path.join(ROOT,"specs","*.json"))):
    if os.path.basename(f)[:15]>now: continue
    d=json.load(open(f,encoding="utf-8"))
    if d.get("kind")=="carousel": shown.update(d.get("images",[]))
for f in sorted(glob.glob(os.path.join(ROOT,"specs","*.json"))):
    stem=os.path.basename(f)[:-5]
    d=json.load(open(f,encoding="utf-8"))
    if stem[:15]>now and not (d.get("images") and d["images"][0] in shown): continue
    if d.get("kind")!="reel" or not (d.get("asin") or d.get("url")): continue
    store=d.get("store","Amazon")
    url=d.get("url") or f"https://www.amazon.in/dp/{d['asin']}?tag={TAG}"
    kw=(d.get("cta_comment","").replace("Comment","").replace("for the link","").strip().lower())
    nm=" ".join(d.get("name",[])).lower()
    if any(w in nm for w in ("parfum","edp","fragrance","deo")): kw+=" perfume"
    items.append(dict(id=stem[16:],when=min(stem[:15],now),kw=kw,name=(d.get("brand","")+" "+" ".join(d.get("name",[]))).strip(),
        brand=d.get("brand",""),cat=d.get("category","Finds"),img=d["images"][0],story=d.get("problem",""),
        hook=d.get("hook",""),feat=[x for x in d.get("feat",[]) if x][:3],rating=d.get("rating",""),
        reviews=d.get("reviews",""),bought=d.get("bought",""),url=url,store=store,go=f"go/{stem[16:]}/"))
items.sort(key=lambda x:x["when"],reverse=True)
e=html.escape
cats=sorted({i["cat"] for i in items})
def stars(r):
    try: v=float(r)
    except: return ""
    pct=max(0,min(100,v/5*100))
    return f'<span class="stars" style="--p:{pct:.0f}%" aria-label="{v} out of 5"></span>'
def card(i,n):
    feats="".join(f"<li>{e(x)}</li>" for x in i["feat"])
    bought=f'<span class="pill">{e(i["bought"])} bought last month</span>' if i["bought"] else ""
    return f'''<article class="card reveal" data-cat="{e(i['cat'])}" data-q="{e((i['name']+' '+i['cat']+' '+i['kw']).lower())}" id="{e(i['id'])}">
  <a class="media shop" href="{e(i['go'])}" target="_blank" rel="nofollow sponsored noopener"><img loading="lazy" src="{e(i['img'])}" alt="{e(i['name'])}"><span class="num">{n:02d}</span></a>
  <div class="body"><div class="meta"><span class="cat">{e(i['cat'])}</span>{bought}</div>
  <h3>{e(i['name'])}</h3><p class="why">{e(i['story'])}</p><ul>{feats}</ul>
  <div class="foot"><div class="rate">{stars(i['rating'])}<span>{e(i['rating'])} · {e(i['reviews'])}</span></div>
  <a class="btn shop" href="{e(i['go'])}" target="_blank" rel="nofollow sponsored noopener">View on {e(i['store'])} <span aria-hidden="true">&rarr;</span></a></div></div></article>'''
feat=items[0] if items else None
featured=f'''<section class="feature reveal" id="today"><div class="fimg"><img src="{e(feat['img'])}" alt="{e(feat['name'])}"></div>
  <div class="ftext"><span class="eyebrow">Today's find</span><h2>{e(feat['name'])}</h2><p class="lede">{e(feat['story'])}</p>
  <ul class="ticks">{''.join(f'<li>{e(x)}</li>' for x in feat['feat'])}</ul>
  <div class="rate big">{stars(feat['rating'])}<span>{e(feat['rating'])}/5 from {e(feat['reviews'])} ratings</span></div>
  <a class="btn lg shop" href="{e(feat['go'])}" target="_blank" rel="nofollow sponsored noopener">Check price on {e(feat['store'])} <span aria-hidden="true">&rarr;</span></a></div></section>''' if feat else ""
grid="\n".join(card(i,n) for n,i in enumerate(items,1))
chips='<button class="chip on" data-c="all">All</button>'+"".join(f'<button class="chip" data-c="{e(c)}">{e(c)}</button>' for c in cats)
ogimg=e(items[0]["img"]) if items else "assets/tara_rooftop.jpg"
CID=os.environ.get("CUELINKS_CID","").strip() or (open(os.path.join(ROOT,"cuelinks_cid.txt")).read().strip() if os.path.exists(os.path.join(ROOT,"cuelinks_cid.txt")) else "")
cue=(f'<script>var cId="{CID}";(function(d,t){{var s=document.createElement("script");s.type="text/javascript";s.async=true;s.src=(document.location.protocol=="https:"?"https://cdn0.cuelinks.com/js/":"http://cdn0.cuelinks.com/js/")+"cuelinksv2.js";document.getElementsByTagName("body")[0].appendChild(s);}}());</script>') if CID else ""
PIX=pixel_head("var P0=new URLSearchParams(location.search).get('q');if(P0)fbq('trackCustom','DMVisit',{keyword:P0.toLowerCase()});")
page=f'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Kya Cheez Hai — Daily finds worth buying</title>
<meta name="description" content="Handpicked, highly rated finds from Amazon India — watches, beauty, bags, travel and home. Curated daily by @kyacheezhai.in.">
<meta property="og:title" content="Kya Cheez Hai — Daily finds worth buying"><meta property="og:description" content="Handpicked, highly rated finds. Curated daily."><meta property="og:image" content="{ogimg}"><meta name="theme-color" content="#14110F">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
{PIX}
<style>
:root{{--ink:#14110F;--paper:#FBF7F1;--card:#FFFFFF;--line:#ECE4D8;--muted:#7A7068;--coral:#FF5A4E;--coral2:#E8473C;--mint:#2FBF85;--gold:#F2B33D;--r:22px}}
*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}
body{{margin:0;background:var(--paper);color:var(--ink);font:400 16px/1.55 Inter,system-ui,sans-serif;-webkit-font-smoothing:antialiased}}
img{{display:block;max-width:100%}}a{{color:inherit}}
.wrap{{max-width:1180px;margin:0 auto;padding:0 22px}}
.top{{position:sticky;top:0;z-index:20;backdrop-filter:saturate(1.4) blur(14px);background:rgba(251,247,241,.82);border-bottom:1px solid transparent;transition:border-color .3s}}
.top.s{{border-color:var(--line)}}
.bar{{display:flex;align-items:center;justify-content:space-between;height:64px}}
.logo{{font:700 21px Fraunces,serif;letter-spacing:-.3px;text-decoration:none}}.logo b{{color:var(--coral)}}
.ig{{display:inline-flex;gap:8px;align-items:center;text-decoration:none;font-weight:600;font-size:14px;padding:9px 16px;border-radius:999px;background:var(--ink);color:#fff}}
.hero{{display:grid;grid-template-columns:1.15fr .85fr;gap:48px;align-items:center;padding:56px 0 40px}}
.eyebrow{{display:inline-block;font:600 12px Inter;letter-spacing:2px;text-transform:uppercase;color:var(--coral)}}
h1{{font:700 clamp(40px,6vw,72px)/1.02 Fraunces,serif;letter-spacing:-1.5px;margin:14px 0 18px}}
h1 em{{font-style:italic;color:var(--coral)}}
.hero p{{font-size:18px;color:var(--muted);max-width:520px;margin:0 0 28px}}
.cta{{display:flex;gap:12px;flex-wrap:wrap}}
.btn{{display:inline-flex;align-items:center;gap:8px;justify-content:center;background:var(--coral);color:#fff;text-decoration:none;font-weight:600;font-size:15px;padding:12px 18px;border-radius:12px;transition:transform .2s,background .2s,box-shadow .2s;box-shadow:0 6px 18px -8px rgba(255,90,78,.7)}}
.btn:hover{{background:var(--coral2);transform:translateY(-1px)}}.btn.lg{{padding:16px 26px;font-size:16px;border-radius:14px}}
.btn.ghost{{background:transparent;color:var(--ink);border:1.5px solid var(--ink);box-shadow:none}}
.portrait{{position:relative}}
.portrait .ph{{border-radius:28px;overflow:hidden;aspect-ratio:4/5;box-shadow:0 30px 60px -30px rgba(20,17,15,.45)}}
.portrait img{{width:100%;height:100%;object-fit:cover;object-position:top}}
.badge{{position:absolute;left:-18px;bottom:28px;background:var(--card);border-radius:16px;padding:12px 16px;box-shadow:0 14px 30px -12px rgba(0,0,0,.25);font-size:13px;line-height:1.3}}
.badge strong{{display:block;font:700 18px Fraunces,serif}}
.trust{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;padding:8px 0 46px}}
.trust div{{border-top:1.5px solid var(--ink);padding-top:14px;font-size:14px;color:var(--muted)}}
.trust b{{display:block;color:var(--ink);font:700 20px Fraunces,serif;margin-bottom:4px}}
.feature{{display:grid;grid-template-columns:1fr 1fr;background:var(--card);border-radius:30px;overflow:hidden;box-shadow:0 20px 50px -30px rgba(20,17,15,.35);margin-bottom:64px}}
.fimg{{background:#fff;position:relative;min-height:420px}}
.fimg img{{position:absolute;top:44px;left:44px;width:calc(100% - 88px);height:calc(100% - 88px);object-fit:contain;transition:transform .6s}}.feature:hover .fimg img{{transform:scale(1.04)}}
.ftext{{padding:48px;background:var(--ink);color:#fff;display:flex;flex-direction:column;justify-content:center}}
.ftext h2{{font:700 clamp(28px,3.2vw,40px)/1.1 Fraunces,serif;margin:12px 0 12px;letter-spacing:-.5px}}
.lede{{color:#cfc6bc;font-size:17px;margin:0 0 18px}}
.ticks{{list-style:none;padding:0;margin:0 0 20px}}.ticks li{{padding-left:28px;position:relative;margin:8px 0}}
.ticks li:before{{content:"";position:absolute;left:0;top:5px;width:16px;height:16px;border-radius:50%;background:var(--mint)}}
.ticks li:after{{content:"";position:absolute;left:5px;top:8px;width:5px;height:8px;border:solid var(--ink);border-width:0 2px 2px 0;transform:rotate(45deg)}}
.rate{{display:flex;align-items:center;gap:8px;font-size:13px;color:var(--muted)}}.rate.big{{color:#cfc6bc;font-size:14px;margin-bottom:24px}}
.stars{{--p:80%;display:inline-block;width:86px;height:15px;background:linear-gradient(90deg,var(--gold) var(--p),#D9D1C6 var(--p));-webkit-mask:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 120 22'%3E%3Cg%3E%3Cpath id='s' d='M11 1l3 6.5 7 .8-5.2 4.8 1.4 7L11 16.6 4.8 20l1.4-7L1 8.3l7-.8z'/%3E%3Cuse href='%23s' x='24.5'/%3E%3Cuse href='%23s' x='49'/%3E%3Cuse href='%23s' x='73.5'/%3E%3Cuse href='%23s' x='98'/%3E%3C/g%3E%3C/svg%3E") center/contain no-repeat;mask:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 120 22'%3E%3Cg%3E%3Cpath id='s' d='M11 1l3 6.5 7 .8-5.2 4.8 1.4 7L11 16.6 4.8 20l1.4-7L1 8.3l7-.8z'/%3E%3Cuse href='%23s' x='24.5'/%3E%3Cuse href='%23s' x='49'/%3E%3Cuse href='%23s' x='73.5'/%3E%3Cuse href='%23s' x='98'/%3E%3C/g%3E%3C/svg%3E") center/contain no-repeat}}
.shophead{{display:flex;align-items:end;justify-content:space-between;gap:20px;flex-wrap:wrap;margin-bottom:18px}}
.shophead h2{{font:700 clamp(30px,4vw,44px)/1.05 Fraunces,serif;margin:6px 0 0;letter-spacing:-.8px}}
.card.hit{{outline:2px solid var(--ink);outline-offset:3px}}
.search{{flex:0 1 320px;position:relative}}.search input{{width:100%;font:500 15px Inter;padding:13px 16px 13px 42px;border-radius:14px;border:1.5px solid var(--line);background:var(--card);outline:none;transition:border-color .2s}}
.search input:focus{{border-color:var(--ink)}}.search svg{{position:absolute;left:14px;top:50%;transform:translateY(-50%);opacity:.5}}
.chips{{display:flex;gap:8px;overflow-x:auto;padding:4px 0 22px;scrollbar-width:none}}.chips::-webkit-scrollbar{{display:none}}
.chip{{border:1.5px solid var(--line);background:var(--card);border-radius:999px;padding:8px 16px;font:500 14px Inter;white-space:nowrap;cursor:pointer;transition:all .2s}}
.chip:hover{{border-color:var(--ink)}}.chip.on{{background:var(--ink);color:#fff;border-color:var(--ink)}}
.grid{{display:grid;gap:22px;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));padding-bottom:70px}}
.card{{background:var(--card);border-radius:var(--r);overflow:hidden;display:flex;flex-direction:column;border:1px solid var(--line);transition:transform .35s cubic-bezier(.2,.8,.2,1),box-shadow .35s}}
.card:hover{{transform:translateY(-6px);box-shadow:0 26px 50px -28px rgba(20,17,15,.4)}}
.media{{position:relative;display:block;aspect-ratio:1/1;background:#fff;overflow:hidden}}
.media img{{position:absolute;top:26px;left:26px;width:calc(100% - 52px);height:calc(100% - 52px);object-fit:contain;transition:transform .5s}}.card:hover .media img{{transform:scale(1.06)}}
.num{{position:absolute;top:14px;left:16px;font:700 13px Fraunces,serif;color:var(--muted)}}
.body{{padding:4px 20px 20px;display:flex;flex-direction:column;flex:1}}
.meta{{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:8px}}
.cat{{font:600 11px Inter;letter-spacing:1.4px;text-transform:uppercase;color:var(--coral)}}
.pill{{font-size:11px;font-weight:600;background:#EAF8F1;color:#1C8A5E;padding:3px 8px;border-radius:999px}}
.card h3{{font:700 20px/1.2 Fraunces,serif;margin:0 0 8px;letter-spacing:-.2px}}
.why{{color:var(--muted);font-size:14px;margin:0 0 10px}}
.card ul{{margin:0 0 16px;padding-left:18px;font-size:14px}}.card li{{margin:3px 0}}
.foot{{margin-top:auto;display:flex;flex-direction:column;gap:12px}}.foot .btn{{width:100%}}
.empty{{display:none;text-align:center;color:var(--muted);padding:30px 0 60px}}
.band{{background:var(--ink);color:#fff;border-radius:30px;padding:46px;display:grid;grid-template-columns:1.2fr .8fr;gap:30px;align-items:center;margin-bottom:60px}}
.band h2{{font:700 clamp(28px,3.4vw,40px)/1.1 Fraunces,serif;margin:10px 0 12px}}.band p{{color:#cfc6bc;margin:0 0 22px}}
.band .ph{{border-radius:22px;overflow:hidden;aspect-ratio:1/1}}.band img{{width:100%;height:100%;object-fit:cover;object-position:top}}
footer{{border-top:1px solid var(--line);padding:26px 0 40px;color:var(--muted);font-size:13px}}
footer .row{{display:flex;justify-content:space-between;gap:18px;flex-wrap:wrap}}
.reveal{{opacity:0;transform:translateY(18px);transition:opacity .7s,transform .7s}}.reveal.in{{opacity:1;transform:none}}
@media (max-width:860px){{.hero{{grid-template-columns:1fr;gap:30px;padding:32px 0 24px}}.portrait{{order:-1;max-width:420px}}.badge{{left:12px}}
.feature,.band{{grid-template-columns:1fr}}.ftext,.band{{padding:30px}}.fimg{{min-height:300px;padding:28px}}.trust{{grid-template-columns:1fr}}}}
@media (prefers-reduced-motion:reduce){{*{{transition:none!important}}.reveal{{opacity:1;transform:none}}}}
</style></head><body>
<header class="top" id="top"><div class="wrap bar"><a class="logo" href="#">Kya Cheez <b>Hai</b></a>
<a class="ig" href="{IG}" target="_blank" rel="noopener"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r="1" fill="currentColor"/></svg>@kyacheezhai.in</a></div></header>
<main class="wrap">
<section class="hero"><div><span class="eyebrow">Curated daily · India</span>
<h1>Things <em>actually</em> worth buying.</h1>
<p>Every day we dig through thousands of listings and keep only the finds people love — top rated, flying off the shelves, and fairly priced.</p>
<div class="cta"><a class="btn lg" href="#today">See today's find <span aria-hidden="true">&rarr;</span></a><a class="btn lg ghost" href="#shop">Browse all</a></div></div>
<div class="portrait"><div class="ph"><img src="assets/tara_rooftop.jpg" alt="Tara, Kya Cheez Hai host"></div>
<div class="badge"><strong>{len(items)} finds</strong>handpicked so far</div></div></section>
<section class="trust"><div><b>4.1★ or better</b>Only products buyers rate highly</div><div><b>Thousands sold</b>Picks that are selling fast right now</div><div><b>Real photos</b>What you see is the actual product</div></section>
{featured}
<section id="shop"><div class="shophead"><div><span class="eyebrow">The shop</span><h2>All finds</h2></div>
<label class="search"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg><input id="q" type="search" placeholder="Search watches, perfume, bags…" aria-label="Search finds"></label></div>
<nav class="chips">{chips}</nav><div class="grid" id="grid">{grid}</div><p class="empty" id="empty">No finds match that yet — try another word.</p></section>
<section class="band reveal"><div><span class="eyebrow">Never miss a find</span><h2>New finds drop twice a day on Instagram.</h2><p>Short, honest reels with the real product — follow along and save what you love.</p>
<a class="btn lg" href="{IG}" target="_blank" rel="noopener">Follow @kyacheezhai.in <span aria-hidden="true">&rarr;</span></a></div><div class="ph"><img loading="lazy" src="assets/tara_party.jpg" alt="Kya Cheez Hai on Instagram"></div></section>
</main>
<footer><div class="wrap row"><span>© {datetime.date.today().year} Kya Cheez Hai</span><span>As an Amazon Associate and affiliate partner of other stores, we earn from qualifying purchases at no extra cost to you. Prices and availability are set by each store. Our host Tara is AI-generated; product photos are from the listings.</span></div></footer>
<script>
const t=document.getElementById('top');addEventListener('scroll',()=>t.classList.toggle('s',scrollY>10),{{passive:true}});
const io=new IntersectionObserver(es=>es.forEach(x=>{{if(x.isIntersecting){{x.target.classList.add('in');io.unobserve(x.target)}}}}),{{threshold:.08}});
document.querySelectorAll('.reveal').forEach(el=>io.observe(el));
let cat='all';const q=document.getElementById('q'),cards=[...document.querySelectorAll('.card')],empty=document.getElementById('empty');
function f(){{const s=q.value.trim().toLowerCase();let n=0;cards.forEach(c=>{{const ok=(cat==='all'||c.dataset.cat===cat)&&(!s||c.dataset.q.includes(s));c.style.display=ok?'':'none';if(ok){{n++;c.classList.add('in')}}}});empty.style.display=n?'none':'block'}}
q.addEventListener('input',f);document.querySelectorAll('.chip').forEach(b=>b.onclick=()=>{{document.querySelectorAll('.chip').forEach(x=>x.classList.remove('on'));b.classList.add('on');cat=b.dataset.c;f()}});
const P=new URLSearchParams(location.search).get('q');if(P){{const w=P.toLowerCase(),g=cards[0]&&cards[0].parentNode;if(g){{cards.filter(c=>c.dataset.q.includes(w)).reverse().forEach(c=>{{g.prepend(c);c.classList.add('in','hit')}});setTimeout(()=>g.scrollIntoView({{behavior:'smooth'}}),300)}}}}
var SRC=(function(){{try{{var u=new URLSearchParams(location.search),r=document.referrer||'',v;
if(u.get('q')||u.get('src')==='dm')v='dm';else if(u.get('src')==='instagram'||u.get('igshid')||u.get('fbclid')||/instagram\\.com|facebook\\.com|l\\.instagram/.test(r))v='instagram';
v=v||sessionStorage.getItem('kch_src')||'direct';sessionStorage.setItem('kch_src',v);return v}}catch(_){{return 'direct'}}}})();
document.querySelectorAll('a.shop').forEach(a=>{{a.href=a.getAttribute('href')+'?src='+SRC}});
if(location.hash){{const el=document.querySelector(location.hash);if(el)setTimeout(()=>el.scrollIntoView({{behavior:'smooth'}}),300)}}
</script>{cue}</body></html>'''
os.makedirs(os.path.join(ROOT,"docs"),exist_ok=True)
open(os.path.join(ROOT,"docs","index.html"),"w",encoding="utf-8").write(page)
open(os.path.join(ROOT,"docs",".nojekyll"),"w").write("")
CUE_WRAP=lambda u,store: (f"https://linksredirect.com/?cid={CID}&source=linkkit&url="+urllib.parse.quote(u,safe="")) if CID and store!="Amazon" else u
gdir=os.path.join(ROOT,"docs","go"); shutil.rmtree(gdir,ignore_errors=True)
for i in items:
    dest=CUE_WRAP(i["url"],i["store"]); js=json.dumps
    ev=("var S=new URLSearchParams(location.search).get('src')||'direct',D={content_ids:["+js(i["id"])+"],content_type:'product',content_name:"+js(i["name"])+
        ",content_category:"+js(i["cat"])+",store:"+js(i["store"])+",source:S};fbq('trackCustom','ShopClick',D);fbq('track','ViewContent',D);")
    g=f'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>Opening {e(i['store'])}…</title>
<noscript><meta http-equiv="refresh" content="0;url={e(dest)}"></noscript>{pixel_head(ev)}
<style>body{{margin:0;min-height:100vh;display:grid;place-items:center;background:#FBF7F1;color:#14110F;font:500 16px Inter,system-ui,sans-serif;text-align:center}}a{{color:#E8473C}}</style></head>
<body><p>Opening {e(i['store'])}…<br><small><a href="{e(dest)}" rel="nofollow sponsored">Tap here if it doesn\'t open</a></small></p>
<script>setTimeout(function(){{location.replace({js(dest)})}},700);</script></body></html>'''
    os.makedirs(os.path.join(gdir,i["id"]),exist_ok=True)
    open(os.path.join(gdir,i["id"],"index.html"),"w",encoding="utf-8").write(g)
print("site:",len(items),"products,",len(items),"go pages")
