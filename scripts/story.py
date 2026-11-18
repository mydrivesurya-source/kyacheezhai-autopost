"""Story-edit reel renderer: 6 scenes, kinetic text, transitions, Tara + real product photos, original music bed.
Spec fields used: brand, name[], hook, problem, feat[] (3-4), rating ("4.3"), reviews ("12K+"), bought ("5K+"),
images[] (real product photo URLs), host, cta_comment (optional)."""
import math, subprocess, wave, numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
CH=(18,18,18); CORAL=(255,90,78); CREAM=(248,244,238); MINT=(61,220,151); GOLD=(255,196,61); WHITE=(255,255,255)

def ease(t): t=max(0,min(1,t)); return 1-(1-t)**3
def pop(t): t=max(0,min(1,t)); return 1+0.25*math.sin(t*math.pi)*(1-t) if t<1 else 1

class R:
    def __init__(s, font): s.font=font; s.cache={}
    def F(s,n):
        if n not in s.cache: s.cache[n]=ImageFont.truetype(s.font,n)
        return s.cache[n]

def wrap(d, text, font, width):
    out=[]; cur=""
    for w in text.split():
        t=(cur+" "+w).strip()
        if d.textlength(t,font=font)<=width: cur=t
        else:
            if cur: out.append(cur)
            cur=w
    if cur: out.append(cur)
    return out

def read_frames(path, w, h):
    raw=subprocess.run(["ffmpeg","-loglevel","error","-i",path,"-vf",f"scale={w}:{h},fps={FPS}","-f","rawvideo","-pix_fmt","rgb24","-"],capture_output=True,check=True).stdout
    n=len(raw)//(w*h*3); a=np.frombuffer(raw,np.uint8)[:n*w*h*3].reshape(n,h,w,3)
    return [Image.fromarray(f) for f in a]

def star(d, cx, cy, r, fill):
    pts=[]
    for i in range(10):
        ang=-math.pi/2+i*math.pi/5; rr=r if i%2==0 else r*0.45
        pts.append((cx+rr*math.cos(ang), cy+rr*math.sin(ang)))
    d.polygon(pts, fill=fill)

def music(dur, sr=44100):
    """Original lo-fi bed: 96 bpm kick/hat + soft chord pad (Am-F-C-G)."""
    n=int(dur*sr); t=np.arange(n)/sr; out=np.zeros(n)
    beat=60/96
    chords=[[220,261.6,329.6],[174.6,220,261.6],[261.6,329.6,392],[196,246.9,293.7]]
    for i,b in enumerate(np.arange(0,dur,beat)):
        s=int(b*sr); L=int(0.35*sr); e=min(n,s+L); k=np.arange(e-s)/sr
        out[s:e]+=0.55*np.sin(2*np.pi*(55+90*np.exp(-k*25))*k)*np.exp(-k*9)          # kick
        hs=int((b+beat/2)*sr); he=min(n,hs+int(0.05*sr))
        if hs<n: out[hs:he]+=0.06*np.random.randn(he-hs)*np.exp(-np.arange(he-hs)/sr*80)  # hat
    bar=beat*4
    for i,b in enumerate(np.arange(0,dur,bar)):
        s=int(b*sr); e=min(n,int((b+bar)*sr)); k=np.arange(e-s)/sr
        env=np.minimum(1,k*3)*np.minimum(1,(bar-k)*3)
        for f in chords[i%4]: out[s:e]+=0.05*np.sin(2*np.pi*f*k)*env
    return out/ max(1e-6,np.abs(out).max())

def render(spec, host, imgs, out, font, tmp):
    r=R(font); F=r.F
    P=[Image.open(p).convert("RGB") for p in imgs]
    nohost = (host is None)
    if nohost:
        # product-only hero: real photo on a soft blurred copy of itself, slow push-in
        base=P[0].copy(); bg=base.resize((W,H)).filter(ImageFilter.GaussianBlur(40))
        bg=Image.blend(bg,Image.new("RGB",(W,H),CH),0.35)
        def hero(i, kind="full"):
            z=1+0.0015*i; im=bg.copy(); ph=base.copy(); ph.thumbnail((int(900*z),int(1100*z)))
            card=Image.new("RGB",(ph.width+40,ph.height+40),WHITE); card.paste(ph,(20,20))
            im.paste(card,((W-card.width)//2,(H-card.height)//2-140))
            return im if kind=="full" else im.crop((0,(H-960)//2-140,W,(H+960)//2-140))
        tara=hero; half_top=lambda i: hero(i,"half")
    else:
        full=read_frames(host,W,H)                       # host is 9:16 -> full screen, uncropped
        half=[f.resize((540,960)) for f in full]
        nT=len(full)
        def tara(i, kind="full"):
            k=i if i<nT else (nT-1-((i-nT)%(nT-1)) if ((i-nT)//(nT-1))%2==0 else (i-nT)%(nT-1))
            return (full if kind=="full" else half)[max(0,min(nT-1,k))]
        import os
        SMILE={"tara_party.mp4":6.5}
        st=SMILE.get(os.path.basename(host),0.05)
        still_full=full[min(nT-1,int(st*FPS))]
        def still(i, zoom=True):
            # smiling still (no lip movement) with a slow push-in
            if not zoom: return still_full
            z=1+0.0009*i; w,h=int(W*z),int(H*z)
            return still_full.resize((w,h)).crop(((w-W)//2,(h-H)//2,(w-W)//2+W,(h-H)//2+H))
        bgcache={}
        def half_top(i):
            f=tara(i,"half"); key=i//6
            if key not in bgcache:
                bgcache.clear(); bgcache[key]=tara(i).crop((0,480,W,1440)).filter(ImageFilter.GaussianBlur(28))
            top=bgcache[key].copy(); top.paste(f,((W-540)//2,0)); return top
    def fitted(img, box_w, box_h, scale=1.0):
        im=img.copy(); im.thumbnail((int(box_w*scale),int(box_h*scale))); return im

    feats=[f for f in spec.get("feat",[]) if f][:4]
    name=(spec.get("brand","")+" "+" ".join(spec.get("name",[]))).strip()
    hook=spec.get("hook","Kya cheez hai yaar!")
    problem=spec.get("problem","Har din ki problem? Ab nahi.")
    rating=float(spec.get("rating","4.3")); reviews=spec.get("reviews","10K+"); bought=spec.get("bought","")
    scenes=[("hook",2.6),("problem",2.4),("reveal",3.0),("features",0.9*len(feats)+0.8),("proof",2.0),("cta",2.2)]
    starts=[];acc=0
    for nm,d in scenes: starts.append((nm,acc,d)); acc+=d
    total=acc; N=int(total*FPS)

    ff=subprocess.Popen(["ffmpeg","-y","-loglevel","error","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-",
        "-c:v","libx264","-preset","veryfast","-crf","20","-pix_fmt","yuv420p",f"{tmp}/v.mp4"],stdin=subprocess.PIPE)
    prev=None
    for i in range(N):
        t=i/FPS
        nm,s0,d=[x for x in starts if x[1]<=t][-1]; lt=t-s0; p=lt/d
        im=Image.new("RGB",(W,H),CREAM); dr=ImageDraw.Draw(im)
        if nm=="hook":
            im.paste(tara(i),(0,0)); dr=ImageDraw.Draw(im)
            sc=pop(lt/0.5); f=F(int(84*sc))
            lines=wrap(dr,hook,F(84),940); y=1300
            for ln in lines:
                w=dr.textlength(ln,font=f); dr.rounded_rectangle([(W-w)/2-24,y-10,(W+w)/2+24,y+int(100*sc)],22,fill=CORAL)
                dr.text(((W-w)/2,y),ln,font=f,fill=WHITE); y+=int(118*sc)
        elif nm=="problem":
            im.paste(half_top(i),(0,0)); dr=ImageDraw.Draw(im)
            dr.rectangle([0,960,W,H],fill=CH)
            dr.text((70,1040),"THE PROBLEM",font=F(34),fill=CORAL)
            words=problem.split(); k=int(len(words)*min(1,lt/1.4))+1
            y=1110
            for ln in wrap(dr," ".join(words[:k]),F(70),940): dr.text((70,y),ln,font=F(70),fill=WHITE); y+=88
        elif nm=="reveal":
            im.paste(half_top(i),(0,0)); dr=ImageDraw.Draw(im)
            dr.rectangle([0,960,W,H],fill=WHITE)
            e=ease(lt/0.6); pim=fitted(P[0],760,640,1+0.05*p)
            im.paste(pim,((W-pim.width)//2,int(990+(1-e)*500)+(640-pim.height)//2))
            dr.rounded_rectangle([60,990,330,1040],25,fill=MINT); dr.text((84,994),"NEW FIND",font=F(32),fill=CH)
            if lt>0.5:
                a=ease((lt-0.5)/0.5); y=1660+int((1-a)*60)
                for ln in wrap(dr,name,F(54),960)[:2]: dr.text((60,y),ln,font=F(54),fill=CH); y+=66
        elif nm=="features":
            pim=P[1%len(P)]; sc=1.0+0.08*p
            bg=pim.copy(); bg.thumbnail((int(1000*sc),int(1150*sc)))
            im.paste(bg,((W-bg.width)//2,170+(1150-bg.height)//2)); dr=ImageDraw.Draw(im)
            dr.rectangle([0,1330,W,H],fill=CH)
            for j,ft in enumerate(feats):
                a=ease((lt-0.3-j*0.9)/0.35)
                if a<=0: continue
                x=70-int((1-a)*80); y=1380+j*125
                dr.ellipse([x,y+4,x+56,y+60],fill=MINT); dr.line([(x+14,y+33),(x+25,y+45),(x+44,y+18)],fill=CH,width=7)
                dr.text((x+84,y),ft,font=F(50),fill=WHITE)
            if not nohost:
              b=still(i,False).resize((300,533)).crop((0,60,300,360)); m=Image.new("L",(300,300),0); ImageDraw.Draw(m).ellipse([0,0,299,299],fill=255)
              dr.ellipse([W-345,95,W-35,405],fill=CORAL); im.paste(b,(W-340,100),m)
        elif nm=="proof":
            pim=fitted(P[0],560,560); im.paste(pim,((W-pim.width)//2,260+(560-pim.height)//2)); dr=ImageDraw.Draw(im)
            dr.text((W/2-dr.textlength("Loved by buyers",font=F(56))/2,900),"Loved by buyers",font=F(56),fill=CH)
            fill=ease(lt/1.0)*rating
            for j in range(5):
                cx=W/2-260+j*130; star(dr,cx,1080,56,(225,220,212))
                if fill>j:
                    s=Image.new("RGBA",(130,130),(0,0,0,0)); star(ImageDraw.Draw(s),65,65,56,GOLD)
                    frac=min(1,fill-j); cut=s.crop((0,0,int(9+112*frac),130)); im.paste(cut,(int(cx-65),1015),cut)
            dr=ImageDraw.Draw(im); txt=f"{rating:.1f} / 5   |   {reviews} ratings"
            dr.text((W/2-dr.textlength(txt,font=F(50))/2,1190),txt,font=F(50),fill=CH)
            if bought: t2=f"{bought} bought last month"; dr.text((W/2-dr.textlength(t2,font=F(44))/2,1270),t2,font=F(44),fill=CORAL)
        else:  # cta
            im.paste(tara(i) if nohost else still(int(lt*FPS)),(0,0)); dr=ImageDraw.Draw(im)
            s=1+0.06*math.sin(lt*2*math.pi*1.6); bw,bh=int(760*s),int(150*s)
            dr.rounded_rectangle([(W-bw)//2,1250,(W+bw)//2,1250+bh],bh//2,fill=CORAL)
            f=F(int(72*s)); tx="Link in bio"; dr.text(((W-dr.textlength(tx,font=f))/2,1250+bh/2-44*s),tx,font=f,fill=WHITE)
            c=spec.get("cta_comment","Comment YES for the link!")
            dr.text(((W-dr.textlength(c,font=F(46)))/2,1450),c,font=F(46),fill=WHITE,stroke_width=4,stroke_fill=CH)
        # global chrome
        dr.rectangle([0,0,int(W*t/total),10],fill=CORAL)
        tag="KYA CHEEZ HAI"; dr.rounded_rectangle([40,36,60+dr.textlength(tag,font=F(30)),86],14,fill=CORAL); dr.text((50,40),tag,font=F(30),fill=WHITE)
        foot="#ad  |  real product photos" if nohost else "#ad  |  AI host  |  real product photos"
        dr.text((40,H-60),foot,font=F(26),fill=(170,165,160) if nm in("reveal","proof") else (230,225,220))
        # whip transition: 5-frame blend at scene starts
        if prev is not None and lt<5/FPS and s0>0: im=Image.blend(prev,im,min(1,(lt*FPS+1)/5))
        prev=im
        ff.stdin.write(im.tobytes())
    ff.stdin.close(); ff.wait()
    # audio: Tara voice for her clip length + music bed ducked under voice
    sr=44100
    raw=b"" if nohost else subprocess.run(["ffmpeg","-loglevel","error","-i",host,"-f","s16le","-ac","1","-ar",str(sr),"-"],capture_output=True).stdout
    voice=np.frombuffer(raw,np.int16).astype(np.float32)/32768 if raw else np.zeros(0)
    n=int(total*sr); mix=np.zeros(n); v=voice[:n]; mix[:len(v)]+=v*0.95
    bed=music(total,sr); duck=np.ones(n)*0.62; duck[:len(v)]=0.16
    mix+=bed*duck; fade=int(0.6*sr); mix[-fade:]*=np.linspace(1,0,fade)
    pcm=(np.clip(mix,-1,1)*32767).astype(np.int16)
    with wave.open(f"{tmp}/a.wav","wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(pcm.tobytes())
    subprocess.run(["ffmpeg","-y","-loglevel","error","-i",f"{tmp}/v.mp4","-i",f"{tmp}/a.wav","-c:v","copy","-c:a","aac","-b:a","160k","-shortest","-movflags","+faststart",out],check=True)
    return total
