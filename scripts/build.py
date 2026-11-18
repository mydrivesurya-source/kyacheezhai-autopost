"""Build Instagram media for @kyacheezhai.in from a spec in specs/.
Spec (specs/YYYY-MM-DD-HHMM-<slug>.json):
{
  "kind": "reel" | "carousel",
  "brand": "Titan", "name": ["Karishma", "Analog Watch"],
  "feat": ["Gold-tone dial", "", "Water resistant", "", "4.3 stars | 12,000+", "ratings on Amazon"],
  "images": ["https://m.media-amazon.com/...jpg", "..."],   # real product photos only
  "host": "auto" | "<file in media/hosts>",                 # reel only
  "slides": [ {"title": "...", "lines": ["..."], "image": 0} ],  # carousel only (image = index in images)
  "caption": "..."
}
Writes media/<stem>.mp4 (reel) or media/<stem>-N.jpg (carousel) and queue/<stem>.json.
"""
import json, os, pathlib, subprocess, sys, urllib.request, datetime
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
FONT = str(ROOT / "scripts/Poppins-Bold.ttf")
CH=(18,18,18); CORAL=(255,90,78); CREAM=(245,239,230); MINT=(61,220,151); GREY=(200,195,188)
UA = {"User-Agent": "Mozilla/5.0"}

def fetch(url, out):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        pathlib.Path(out).write_bytes(r.read())
    return out

def F(n): return ImageFont.truetype(FONT, n)

def card(img, size):
    c = Image.new("RGB", (size, size), (255,255,255))
    p = Image.open(img).convert("RGB"); p.thumbnail((size-20, size-20))
    c.paste(p, ((size-p.width)//2, (size-p.height)//2))
    m = Image.new("L", c.size, 0); ImageDraw.Draw(m).rounded_rectangle([0,0,size-1,size-1], 36, fill=255)
    return c, m

def panel(spec, img, out):
    W,H=1080,900; im=Image.new("RGB",(W,H),CH); d=ImageDraw.Draw(im)
    c,m=card(img,560); im.paste(c,(60,80),m)
    d.rounded_rectangle([60,26,300,66],20,fill=MINT); d.text((78,28),spec.get("badge","NEW FIND"),font=F(28),fill=CH)
    x=650; d.text((x,90),spec["brand"],font=F(40),fill=CREAM); y=140
    for t in spec["name"]: d.text((x,y),t,font=F(46),fill=CREAM); y+=56
    y+=20
    for line in spec["feat"]:
        if line: d.text((x,y),line,font=F(28),fill=GREY)
        y+=38
    d.rounded_rectangle([60,690,1020,795],52,fill=CORAL)
    t=spec.get("cta","Tap link in bio to shop"); w=d.textlength(t,font=F(44)); d.text(((W-w)/2,713),t,font=F(44),fill=(255,255,255))
    d.text((60,828),"#ad  Affiliate link. Real product photos.",font=F(24),fill=(140,135,128))
    im.save(out)

def dur(f):
    return float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",f]).decode().strip())

def pick_host(spec, stem):
    hosts = sorted(p.name for p in (ROOT/"media/hosts").glob("*.mp4"))
    h = spec.get("host","auto")
    if h == "auto":
        day = datetime.date.fromisoformat(stem[:10]).toordinal()
        h = hosts[day % len(hosts)]
    return str(ROOT/"media/hosts"/h)

def build_reel(spec, stem, tmp):
    imgs=[fetch(u, f"{tmp}/p{i}.jpg") for i,u in enumerate(spec["images"][:2])]
    if len(imgs)==1: imgs.append(imgs[0])
    panel(spec, imgs[0], f"{tmp}/a.png"); panel(spec, imgs[1], f"{tmp}/b.png")
    host=pick_host(spec, stem); D=dur(host); O=max(D/2-0.25,0.5)
    out=ROOT/f"media/{stem}.mp4"
    fc=(f"[0:v]scale=1080:1920,crop=1080:1020:0:0,setsar=1,fps=30[top];"
        f"[1:v]scale=1080:900,fps=30,setsar=1[a];[2:v]scale=1080:900,fps=30,setsar=1[b];"
        f"[a][b]xfade=transition=slideleft:duration=0.5:offset={O:.2f},trim=duration={D:.2f}[bot];[top][bot]vstack[v];"
        f"[v]drawbox=x=820:y=30:w=230:h=50:color=0xFF5A4E@0.95:t=fill,"
        f"drawtext=fontfile={FONT}:text='KYA CHEEZ HAI':x=840:y=39:fontsize=26:fontcolor=white,"
        f"drawtext=fontfile={FONT}:text='AI host':x=34:y=36:fontsize=22:fontcolor=white@0.75:box=1:boxcolor=black@0.35:boxborderw=8[out]")
    subprocess.run(["ffmpeg","-y","-loglevel","error","-i",host,"-loop","1","-t",f"{D:.2f}","-i",f"{tmp}/a.png",
        "-loop","1","-t",f"{D:.2f}","-i",f"{tmp}/b.png","-filter_complex",fc,"-map","[out]","-map","0:a?",
        "-c:v","libx264","-preset","veryfast","-crf","21","-pix_fmt","yuv420p","-c:a","aac","-shortest",
        "-movflags","+faststart",str(out)],check=True)
    return [f"media/{stem}.mp4"]

def wrap(d, text, font, width):
    words=text.split(); lines=[]; cur=""
    for w in words:
        t=(cur+" "+w).strip()
        if d.textlength(t,font=font)<=width: cur=t
        else: lines.append(cur); cur=w
    if cur: lines.append(cur)
    return lines

def build_carousel(spec, stem, tmp):
    imgs=[fetch(u, f"{tmp}/p{i}.jpg") for i,u in enumerate(spec["images"])]
    outs=[]
    for n,s in enumerate(spec["slides"],1):
        W,H=1080,1350; im=Image.new("RGB",(W,H),CH); d=ImageDraw.Draw(im)
        d.rounded_rectangle([60,50,330,96],22,fill=MINT); d.text((80,54),spec.get("badge","KYA CHEEZ HAI"),font=F(28),fill=CH)
        d.text((W-160,56),f"{n}/{len(spec['slides'])}",font=F(30),fill=GREY)
        y=130
        for line in wrap(d,s["title"],F(58),960): d.text((60,y),line,font=F(58),fill=CREAM); y+=72
        if s.get("image") is not None:
            c,m=card(imgs[s["image"]],640); im.paste(c,((W-640)//2,y+20),m); y+=690
        else: y+=30
        for line in s.get("lines",[]):
            for l in wrap(d,line,F(36),960): d.text((60,y),l,font=F(36),fill=GREY); y+=50
            y+=8
        if n==len(spec["slides"]):
            d.rounded_rectangle([60,H-230,W-60,H-130],50,fill=CORAL)
            t=spec.get("cta","Link in bio to shop"); w=d.textlength(t,font=F(44)); d.text(((W-w)/2,H-208),t,font=F(44),fill=(255,255,255))
        d.text((60,H-80),"#ad  Affiliate links. Real product photos.",font=F(24),fill=(140,135,128))
        p=f"media/{stem}-{n}.jpg"; im.save(ROOT/p,quality=92); outs.append(p)
    return outs

def main():
    specs = sorted((ROOT/"specs").glob("*.json"))
    built = {p.stem for p in (ROOT/"queue").rglob("*.json")}
    for sp in specs:
        stem=sp.stem
        if stem in built: continue
        spec=json.loads(sp.read_text()); tmp=f"/tmp/{stem}"; os.makedirs(tmp,exist_ok=True)
        media = build_reel(spec,stem,tmp) if spec["kind"]=="reel" else build_carousel(spec,stem,tmp)
        q={"type":"reel" if spec["kind"]=="reel" else "carousel","caption":spec["caption"],"media":media}
        (ROOT/"queue"/f"{stem}.json").write_text(json.dumps(q,ensure_ascii=False,indent=1))
        print("built",stem,media)

if __name__=="__main__":
    main()
