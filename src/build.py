# -*- coding: utf-8 -*-
# Winter travel book: compile the itinerary and editorial assets into a static page.
import sys, html, re, urllib.parse, math, os, json
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from booklet_data import CITIES, DAYS, GUIDES, TRAINS, LINKS, STAYS, BOOKINGS, CLOSED, BACKUPS, SOUVENIRS, CHAPTERS, DAY_PHOTOS, DISH_PHOTOS, PHOTO_TEXT

def esc(t): return html.escape(t, quote=True)
def q(t): return "https://www.google.com/maps/search/?api=1&query=" + urllib.parse.quote_plus(t)
def route_url(o, d, w):
    u = "https://www.google.com/maps/dir/?api=1&origin=" + urllib.parse.quote_plus(o) + "&destination=" + urllib.parse.quote_plus(d)
    if w: u += "&waypoints=" + urllib.parse.quote("|".join(w), safe="")
    return u + "&travelmode=walking"
def _lnk(m):
    name = html.unescape(m.group(1))
    if name in LINKS:
        return f'<a class="plink" href="{esc(q(LINKS[name]))}" target="_blank" rel="noopener"><b>{m.group(1)}</b></a>'
    return f"<b>{m.group(1)}</b>"
def rich(t): return re.sub(r"\*\*(.+?)\*\*", _lnk, esc(t))
def nb(t, seps="、，"):
    parts = re.split("([" + seps + "])", t)
    out, buf = [], ""
    for p in parts:
        if p in seps and p: buf += p; out.append(buf); buf = ""
        else: buf += p
    if buf: out.append(buf)
    return "".join(f'<span class="nb">{esc(x)}</span>' for x in out)

KIND = {"go":"交通","see":"景點","eat":"吃喝","book":"已訂","todo":"待訂","rest":"休息","run":"運動"}
SUN = {"ams":("08:42","16:28"),"haa":("08:43","16:27"),"utr":("08:40","16:28"),"dh":("08:42","16:30"),"lei":("08:42","16:29"),
       "rtm":("08:40","16:31"),"bru":("08:36","16:38"),"bxl":("08:33","16:39"),"kol":("08:20","16:28"),"dus":("08:21","16:26")}
def pos(hm):
    h, m = map(int, hm.split(":")); return max(0, min(100, (h + m/60 - 6) / 18 * 100))

# ---------- route map ----------
LAT0, LAT1, LON0, LON1 = 50.55, 52.6, 2.95, 7.2
S = 196; KX = math.cos(math.radians(51.6))
W = (LON1-LON0)*KX*S; H = (LAT1-LAT0)*S
def xy(lat, lon): return ((lon-LON0)*KX*S, (LAT1-lat)*S)
def pt(k): c = CITIES[k]; return xy(c["lat"], c["lon"])
LABEL = {"ams":("e","阿姆斯特丹","12/5–8"),"haa":("w","哈倫","12/18",-8),"utr":("e","烏特勒支",""),"dh":("w","海牙","12/9–10"),
         "lei":("w","萊登","",-6),"rtm":("e","鹿特丹","12/11–12"),"bru":("e","布魯日","12/13–14"),"bxl":("e","布魯塞爾","12/15"),
         "kol":("w","科隆","12/15–17"),"dus":("w","杜塞道夫","")}
def route_svg():
    main = ["ams","dh","rtm","bru","bxl","kol","haa","ams"]
    spurs = [("ams","utr"),("dh","lei"),("kol","dus")]
    d = "M" + " L".join(f"{pt(k)[0]:.1f},{pt(k)[1]:.1f}" for k in main)
    out = [f'<svg class="routemap" viewBox="-20 -14 {W+70:.0f} {H+30:.0f}" role="img" aria-label="路線圖：阿姆斯特丹、海牙、鹿特丹、布魯日、布魯塞爾、科隆，經哈倫回阿姆斯特丹">']
    for lab, lat, lon in [("NEDERLAND",52.55,5.75),("BELGIË",50.62,3.2),("DEUTSCHLAND",51.78,6.0)]:
        x, y = xy(lat, lon); out.append(f'<text class="country" x="{x:.0f}" y="{y:.0f}">{lab}</text>')
    out.append(f'<path class="leg" d="{d}"/>')
    for a, b in spurs:
        (x1,y1),(x2,y2) = pt(a), pt(b); out.append(f'<line class="spur" x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}"/>')
    for k,v in LABEL.items():
        side,name,dates = v[:3]; dy = v[3] if len(v)>3 else 0
        x, y = pt(k); stay = bool(dates); y0 = y; y = y + dy
        out.append(f'<circle class="{"stay" if stay else "trip"}" cx="{x:.1f}" cy="{y0:.1f}" r="{5.5 if stay else 3.5}"/>')
        if side == "n":
            out.append(f'<text class="city" x="{x:.1f}" y="{y-10:.1f}" text-anchor="middle">{name}</text>'); continue
        dx = 10 if side=="e" else -10; anchor = "start" if side=="e" else "end"
        out.append(f'<text class="city" x="{x+dx:.1f}" y="{y+4:.1f}" text-anchor="{anchor}">{name}</text>')
        if dates: out.append(f'<text class="cdate" x="{x+dx:.1f}" y="{y+18:.1f}" text-anchor="{anchor}">{dates}</text>')
    out.append("</svg>")
    return "".join(out)

def cover_strips():
    rows = []
    for d in DAYS:
        sr, ss = SUN[d["city"]]
        rows.append(f'<i style="--sr:{pos(sr):.1f}%;--ss:{pos(ss):.1f}%"></i>')
    return f'<div class="strips" aria-hidden="true">{"".join(rows)}</div>'

# ---------- sections ----------
def overview():
    rows, prev = [], None
    for d in DAYS:
        c = CITIES[d["city"]]
        change = " is-change" if d["hotel"] != prev else ""; prev = d["hotel"]
        rows.append(f'''<a class="ov" href="#d{d["id"]}" data-day="{d["id"]}" style="--c: var(--c-{c["color"]})">
  <span class="ov-date"><b>{d["date"]}</b><i>{d["wd"]}</i></span>
  <span class="ov-main"><span class="ov-city">{c["name"]}</span><span class="ov-title">{esc(d["title"])}</span></span>
  <span class="ov-hotel{change}">{esc(d["hotel"])}</span>
</a>''')
    return "\n".join(rows)

def daychips():
    return "".join(f'<a class="dchip" href="#d{d["id"]}" data-day="{d["id"]}" style="--c: var(--c-{CITIES[d["city"]]["color"]})"><b>{d["date"].split("/")[1]}</b><i>{d["wd"]}</i></a>' for d in DAYS)

def daylight(d):
    sr, ss = SUN[d["city"]]
    ticks = "".join(f'<i style="left:{pos(t):.1f}%"></i>' for t, _, _ in d["items"])
    return (f'<div class="daylight" style="--sr:{pos(sr):.1f}%;--ss:{pos(ss):.1f}%" role="img" aria-label="日出約 {sr}，日落約 {ss}">'
            f'{ticks}<span class="sr">{sr}</span><span class="ss">{ss}</span></div>')

ROOT = Path(__file__).resolve().parents[1]
PHOTOS = json.loads((ROOT / 'assets/img/photos.json').read_text(encoding='utf-8'))

def photo(key, cls='', sizes='(min-width: 1100px) 450px, (min-width: 761px) 40vw, 95vw', priority=False):
    p = PHOTOS[key]
    alt, caption = PHOTO_TEXT[key]
    if p.get('format') == 'food-portrait':
        cls += ' photo-portrait'
    base = f'assets/img/{p["folder"]}/{p["slug"]}'
    variants = ', '.join(f'{base}-{w}.webp {w}w' for w in (640, 1280, 1920))
    loading = 'fetchpriority="high"' if priority else 'loading="lazy" decoding="async"'
    return (f'<figure class="photo {cls}" style="--focus:{esc(p["focus"])}">'
            f'<img src="{base}-640.webp" srcset="{variants}" sizes="{sizes}" '
            f'width="{p["width"]}" height="{p["height"]}" alt="{esc(alt)}" {loading}>'
            f'<figcaption>{esc(caption)}</figcaption></figure>')

def day_cards(ids):
    out = []
    for d in DAYS:
        if d['id'] not in ids:
            continue
        c = CITIES[d["city"]]
        lis = []
        for t, txt, k in d["items"]:
            chip = f'<span class="chip k-{k}">{KIND[k]}</span>' if k in ("book","todo") else ""
            lis.append(f'<li class="k-{k}"><span class="t">{t}</span><span class="mark" title="{KIND[k]}"></span><span class="x">{rich(txt)}{chip}</span></li>')
        rlink = (f'<a class="pin pin-strong" href="{esc(route_url(*d["route"]))}" target="_blank" rel="noopener">今日路線</a>') if d["route"] else ""
        fact = f'<p class="fact"><span>你知道嗎</span>{esc(d["fact"])}</p>' if d.get("fact") else ""
        mm, dd = d["date"].split("/")
        key = DAY_PHOTOS.get(d['id'])
        scene = photo(key, 'day-photo') if key else ''
        out.append(f'''<details class="day" id="d{d["id"]}" open style="--c: var(--c-{c["color"]})">
  <summary class="day-head">
    <div class="day-num"><span class="m">{mm}</span><span class="slash">/</span><span class="d">{dd}</span><span class="wd">週{d["wd"]}</span></div>
    <div class="day-meta">
      <div class="day-city">{c["name"]} <span class="local">{c["local"]}</span></div>
      <h3>{nb(d["title"])}</h3>
      <p class="mood">{esc(d["mood"])}</p>
      <p class="stay"><span>今晚住</span>{esc(d["hotel"])}</p>
      {daylight(d)}
    </div>
    <span class="caret" aria-hidden="true"></span>
  </summary>
  <div class="day-body{' has-scene' if scene else ''}">
    <div class="day-plan">
    <ol class="tl">{"".join(lis)}</ol>
    {fact}
    <div class="day-act">{rlink}</div>
    </div>
    {scene}
  </div>
</details>''')
    return "\n".join(out)

TOP = ("首選",)
BADGE = {"首選":"b-top","備選":"b-alt","點心":"b-alt","酒吧":"b-alt","咖啡":"b-alt"}
def place_li(p):
    badge,name,dish,rating,why,query,when = p
    r = f'<span class="star">★ {rating}</span>' if rating else ""
    return f'''<li class="pl">
  <div class="pl-top"><span class="badge {BADGE.get(badge,"b-alt")}">{badge}</span>{f'<span class="when">{when}</span>' if when else ""}</div>
  <div class="pl-name">{esc(name)}</div>
  <div class="pl-dish">{esc(dish)}{r}</div>
  <div class="pl-why">{esc(why)}</div>
  <a class="pin" href="{esc(q(query))}" target="_blank" rel="noopener" aria-label="{esc(name)} 地圖"></a>
</li>'''
def chapter_index():
    rows = []
    for i, (key, name, local, date, *_rest) in enumerate(CHAPTERS, 1):
        rows.append(f"""<li><a href="#c-{key}">
          <span class="folio">{i:02}</span><span class="contents-name">{esc(name)}
          <i>{esc(local)}</i></span><span class="contents-date">{date}</span></a></li>""")
    return ''.join(rows)

def food_index():
    return ''.join(f'<li><a href="#g-{g["key"]}">{esc(g["cities"])}<span>{esc(g["dates"])}</span></a></li>' for g in GUIDES)

def guide_story(g):
    facts = "".join(f"<dt>{esc(a)}</dt><dd>{esc(b)}</dd>" for a,b in g["facts"])
    return f'<div class="g-story"><p>{esc(g["story"])}</p>{f"<dl class=g-facts>{facts}</dl>" if facts else ""}</div>'

def guide(g):
    dishes = []
    for name, original, note in g['dishes']:
        key = DISH_PHOTOS.get(name) or DISH_PHOTOS.get(original)
        pic = photo(key, 'dish-photo', '(min-width: 1100px) 345px, (min-width: 761px) 31vw, 46vw') if key in PHOTOS else ''
        dishes.append(f'<li{" class=has-dish" if pic else ""}>{pic}<b>{esc(name)}</b><i>{esc(original)}</i><span>{esc(note)}</span></li>')
    top = [p for p in g["places"] if p[0] in TOP]
    rest = [p for p in g["places"] if p[0] not in TOP]
    more = (f'<details class="more"><summary>再 {len(rest)} 間：備選、點心、酒吧、咖啡</summary><ul class="places">{"".join(place_li(p) for p in rest)}</ul></details>') if rest else ""
    return f'''<section class="guide" id="g-{g["key"]}">
  <header class="g-head"><div><div class="kicker">At the table · 吃喝</div><h3>{nb(g["cities"], "・")}</h3></div><span class="g-dates">{g["dates"]}</span></header>
  <div class="g-eat"><div class="label">必吃必喝</div><ul class="dishes" data-count="{len(dishes)}">{"".join(dishes)}</ul></div>
  <div class="label">推薦的店 · ★ 為 Google 評分</div>
  <ul class="places">{"".join(place_li(p) for p in top)}</ul>
  {more}
</section>'''

def chapters():
    guides = {g['key']: g for g in GUIDES}
    out = []
    for i, (key, name, local, date, intro, image, ids, food) in enumerate(CHAPTERS, 1):
        stories = ''.join(guide_story(guides[k]) for k in food)
        menus = ''.join(guide(guides[k]) for k in food)
        links = ''.join(f'<a href="#d{d["id"]}">{d["date"]} <small>週{d["wd"]}</small></a>' for d in DAYS if d['id'] in ids)
        out.append(f'''<article class="chapter" id="c-{key}" data-first="{ids[0]}" style="--c:var(--c-{CITIES[key]["color"]})">
  <header class="opener bleed">
    {photo(image, 'opener-photo', '(min-width: 1440px) 1440px, 100vw')}
    <div class="opener-copy">
      <div class="opener-index"><span>CHAPTER {i:02} / 07</span><span>{date}</span></div>
      <div class="opener-title"><p>{esc(local)}</p><h2>{nb(name, "・")}</h2><div class="opener-intro">{esc(intro)}</div></div>
    </div>
  </header>
  <div class="chapter-links"><span class="kicker">翻到當天</span>{links}</div>
  {f'<div class="chapter-notes">{stories}</div>' if stories else ''}
  <div class="days">{day_cards(ids)}</div>
  {menus}
</article>''')
    return ''.join(out)

def credits():
    lines = []
    for k, p in PHOTOS.items():
        _, caption = PHOTO_TEXT[k]
        lines.append(f'<li><span>{esc(caption)}</span> — <a href="{esc(p["source"])}">{esc(p["author"])}</a> · <a href="{esc(p["license_url"])}">{esc(p["license"])}</a></li>')
    return ''.join(lines)

def stays():
    out = []
    for dates,n,name,addr,note,query,status in STAYS:
        st = "s-ok" if status=="已訂" else "s-todo"
        out.append(f'''<li class="stayc">
  <div class="stay-top"><span class="mono">{dates}</span><span class="nights">{n}</span><span class="sbadge {st}">{status}</span></div>
  <div class="stay-name">{esc(name)}</div>
  <div class="stay-addr">{esc(addr)}</div>
  <div class="stay-note">{esc(note)}</div>
  <a class="pin" href="{esc(q(query))}" target="_blank" rel="noopener" aria-label="{esc(name)} 地圖"></a>
</li>''')
    return "\n".join(out)

def bookings():
    out = []; i = 0
    for st in ["待訂","待確認","已訂","當天買"]:
        lis = []
        for status,date,item,note in BOOKINGS:
            if status != st: continue
            nt = f"<small>{esc(note)}</small>" if note else ""
            if st in ("待訂","待確認"):
                i += 1
                lis.append(f'<li><label><input type="checkbox" id="todo-{i}" data-todo="{i}"><span class="box"></span><span class="tdate">{date}</span><span class="titem">{esc(item)}{nt}</span></label></li>')
            else:
                lis.append(f'<li class="static"><span class="sicon">{"已訂" if st=="已訂" else "現場"}</span><span class="tdate">{date}</span><span class="titem">{esc(item)}{nt}</span></li>')
        if st in ("已訂","當天買"):
            out.append(f'<details class="tgroup fold"><summary class="label">{st}（{len(lis)}）</summary><ul>{"".join(lis)}</ul></details>')
        else:
            out.append(f'<div class="tgroup"><div class="label">{st}</div><ul>{"".join(lis)}</ul></div>')
    return "\n".join(out), i

def trains(): return "".join(f"<tr><td class='mono'>{a}</td><td>{esc(b)}</td><td class='mono'>{esc(c)}</td><td>{esc(d)}</td></tr>" for a,b,c,d in TRAINS)
def closed(): return "".join(f"<tr><td>{esc(a)}</td><td>{esc(b)}</td><td>{esc(c)}</td></tr>" for a,b,c in CLOSED)
def lis(rows): return "".join(f"<li><b>{esc(a)}</b>：{esc(b)}</li>" for a,b in rows)

CSS = r"""
/* Layout: winter light × railway timetable. Night-blue cover with a to-scale route map and 15 daylight strips;
   below it, editorial rules instead of boxes: overview timetable → day pages with a daylight bar → food → stays → before you go → notes. */
:root{
 --paper:#F1F3F4; --surface:#FFFFFF; --sunk:#E7EBED; --ink:#121C28; --ink-2:#34404D; --muted:#5D6975;
 --rule:#D5DBE0; --rule-strong:#121C28;
 --delft:#1E3F8C; --delft-wash:#E3E9F4; --lamp:#B47A00; --lamp-wash:#F6EBD3;
 --ok:#2E6A4E; --ok-wash:#DEEEE5; --warn:#C23B22; --warn-wash:#F8E1DB;
 --night:#0F1F45; --night-ink:#F3F5FA; --night-muted:#A8B6D6; --sun:#F2C14E;
 --day-band:#F4D98B; --night-band:#D9DEE6;
 --c-ams:#D0612A; --c-dh:#7A4E9A; --c-rtm:#2C7A8C; --c-bru:#3F7A5A; --c-bxl:#A8800F; --c-kol:#5A6475; --c-dus:#3367A6;
 --f-display:"Noto Serif TC","Songti TC",serif; --f-num:"Source Serif 4","Noto Serif TC",serif;
 --f-body:"Noto Sans TC","PingFang TC","Microsoft JhengHei",system-ui,sans-serif; --f-mono:"Source Code Pro","Noto Sans TC",ui-monospace,Menlo,monospace;
 --s1:4px;--s2:8px;--s3:12px;--s4:16px;--s5:24px;--s6:32px;--s7:48px;--s8:72px;
 --r:4px; --tap:44px; --gutter:16px; --nav-h:48px; --chips-h:56px;
}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){
 --paper:#0B0F15; --surface:#121820; --sunk:#19212B; --ink:#E9EDF2; --ink-2:#C4CCD6; --muted:#93A0AE;
 --rule:#25303C; --rule-strong:#E9EDF2; --delft:#93B2F2; --delft-wash:#16233D; --lamp:#F2C14E; --lamp-wash:#2E2614;
 --ok:#7CCBA2; --ok-wash:#132A20; --warn:#F28B74; --warn-wash:#33190F;
 --night:#070C18; --night-ink:#EEF2F8; --night-muted:#8E9CC0; --sun:#F2C14E; --day-band:#8A7230; --night-band:#1E2834;
 --c-ams:#F09A66; --c-dh:#C3A3DD; --c-rtm:#86C2DE; --c-bru:#8CC7A8; --c-bxl:#E0BC5E; --c-kol:#AEB6C4; --c-dus:#8DB6E6;
 color-scheme:dark;}}
:root[data-theme="dark"]{
 --paper:#0B0F15; --surface:#121820; --sunk:#19212B; --ink:#E9EDF2; --ink-2:#C4CCD6; --muted:#93A0AE;
 --rule:#25303C; --rule-strong:#E9EDF2; --delft:#93B2F2; --delft-wash:#16233D; --lamp:#F2C14E; --lamp-wash:#2E2614;
 --ok:#7CCBA2; --ok-wash:#132A20; --warn:#F28B74; --warn-wash:#33190F;
 --night:#070C18; --night-ink:#EEF2F8; --night-muted:#8E9CC0; --sun:#F2C14E; --day-band:#8A7230; --night-band:#1E2834;
 --c-ams:#F09A66; --c-dh:#C3A3DD; --c-rtm:#86C2DE; --c-bru:#8CC7A8; --c-bxl:#E0BC5E; --c-kol:#AEB6C4; --c-dus:#8DB6E6;
 color-scheme:dark;}

*{box-sizing:border-box}
html{scroll-behavior:smooth}
@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}*{transition:none!important}}
body{margin:0;background:var(--paper);color:var(--ink);font:400 16px/1.7 var(--f-body)}
body::before{content:"";position:fixed;inset:0 0 auto;height:env(safe-area-inset-top,0px);z-index:30;background:var(--paper)}
a{color:inherit}
a:focus-visible,summary:focus-visible,input:focus-visible+.box{outline:2px solid var(--delft);outline-offset:2px}
h1,h2,h3{margin:0;text-wrap:balance} p{margin:0}
.wrap{max-width:1040px;margin:0 auto;padding-left:max(var(--gutter),env(safe-area-inset-left,0px));padding-right:max(var(--gutter),env(safe-area-inset-right,0px))}
@media(min-width:761px){:root{--gutter:24px}}
.nb{white-space:nowrap}
.label{font:500 12px/1.4 var(--f-body);letter-spacing:.04em;color:var(--muted)}
.kicker{font:500 11.5px/1.4 var(--f-mono);letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}
.mono{font-family:var(--f-mono);font-variant-numeric:tabular-nums}
section.block{padding-block:var(--s8) 0;scroll-margin-top:var(--nav-h)}
.block-head{display:grid;gap:var(--s2);margin-bottom:var(--s5)}
.block-head h2{font:700 clamp(30px,7vw,44px)/1.2 var(--f-display)}
.block-head p{color:var(--ink-2);font-size:15px;max-width:38em}

/* cover */
.cover{background:var(--night);color:var(--night-ink)}
.cover .wrap{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.05fr);gap:var(--s7);align-items:center;padding-block:var(--s8) var(--s7)}
.eyebrow{font:500 11.5px/1 var(--f-mono);letter-spacing:.16em;color:var(--night-muted)}
.cover h1{font:900 clamp(44px,9vw,76px)/1.04 var(--f-display);margin-top:var(--s5);letter-spacing:.01em}
.cover .sub{font:500 17px/1.5 var(--f-display);color:var(--night-muted);margin-top:var(--s3)}
.cover .stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));margin-top:var(--s6);border-top:1px solid color-mix(in srgb,var(--night-ink) 22%,transparent)}
.stat{display:grid;padding:var(--s3) var(--s3) 0}.stat:first-child{padding-left:0}
.stat+.stat{border-left:1px solid color-mix(in srgb,var(--night-ink) 22%,transparent)}
.stat b{font:400 40px/1 var(--f-num)}.stat span{font-size:12px;color:var(--night-muted);margin-top:4px}
.countdown{margin-top:var(--s5);color:var(--night-muted);font-size:14px}
.countdown b{font:600 24px var(--f-num);color:var(--sun)}
.routemap{width:100%;height:auto;max-width:100%;display:block}
.routemap .country{fill:var(--night-muted);opacity:.45;font:500 10px var(--f-mono);letter-spacing:.2em}
.routemap .leg{fill:none;stroke:var(--night-ink);stroke-width:1.8;stroke-linejoin:round;stroke-linecap:round}
.routemap .spur{stroke:var(--night-ink);stroke-width:1.3;stroke-dasharray:2 5;opacity:.7}
.routemap .stay{fill:var(--sun);stroke:var(--night);stroke-width:2}
.routemap .trip{fill:var(--night-ink)}
.routemap .city{fill:var(--night-ink);font:600 13px var(--f-body)}
.routemap .cdate{fill:var(--night-muted);font:400 10.5px var(--f-mono)}
.routemap .city,.routemap .cdate{paint-order:stroke;stroke:var(--night);stroke-width:3px;stroke-linejoin:round}
.maplegend{display:flex;gap:var(--s4);font:500 11px var(--f-mono);letter-spacing:.06em;color:var(--night-muted);margin-top:var(--s2);flex-wrap:wrap}
.maplegend i{display:inline-block;width:9px;height:9px;border-radius:50%;background:var(--sun);margin-right:6px}
.maplegend em{display:inline-block;width:18px;border-top:1.5px dashed var(--night-ink);margin-right:6px;vertical-align:3px}
.strips{display:grid;gap:3px;margin-top:var(--s5)}
.strips i{display:block;height:4px;background:linear-gradient(90deg,color-mix(in srgb,var(--night-ink) 14%,transparent) var(--sr),var(--sun) var(--sr) var(--ss),color-mix(in srgb,var(--night-ink) 14%,transparent) var(--ss))}
.strips-cap{font:500 10.5px var(--f-mono);letter-spacing:.08em;color:var(--night-muted);margin-top:var(--s2)}

/* nav */
.nav{position:sticky;top:0;z-index:20;background:color-mix(in srgb,var(--paper) 88%,transparent);backdrop-filter:saturate(1.4) blur(12px);-webkit-backdrop-filter:saturate(1.4) blur(12px);border-bottom:1px solid var(--rule)}
.nav .wrap{display:flex;align-items:center;gap:var(--s2)}
.nav ul{list-style:none;margin:0;padding:0;display:flex;flex:1;min-width:0;overflow-x:auto;scrollbar-width:none}
.nav a{height:var(--nav-h);display:flex;align-items:center;padding:0 var(--s3);font:500 14px var(--f-body);color:var(--muted);text-decoration:none;white-space:nowrap}
.nav a:hover{color:var(--ink)}
.nav a[aria-current="true"]{color:var(--ink);box-shadow:inset 0 -2px var(--ink)}
.today{flex:none;border-radius:var(--r);background:var(--ink);color:var(--paper);font:600 14px var(--f-body);height:32px;display:flex;align-items:center;padding:0 var(--s4);text-decoration:none}

/* overview */
.ovlist{border-top:2px solid var(--rule-strong)}
@media(min-width:761px){.ovlist{columns:2;column-gap:var(--s7)}}
.ov{display:grid;grid-template-columns:64px minmax(0,1fr);gap:2px var(--s3);align-items:baseline;min-height:56px;padding:var(--s3) 0;border-bottom:1px solid var(--rule);text-decoration:none;break-inside:avoid}
.ov-date{grid-row:span 2;display:flex;gap:6px;align-items:baseline}
.ov-date b{font:400 20px/1 var(--f-num);color:var(--c)}.ov-date i{font:500 11px var(--f-mono);font-style:normal;color:var(--muted)}
.ov-main{display:grid}.ov-city{font:600 12px var(--f-body);letter-spacing:.04em;color:var(--c)}
.ov-title{font:500 15.5px/1.45 var(--f-body)}.ov:hover .ov-title{text-decoration:underline}
.ov-hotel{font-size:12.5px;color:var(--muted)}
.ov.is-today .ov-title{font-weight:700}
@media(max-width:760px){.ov-hotel:not(.is-change){display:none}}

/* date chips + legend */
.dchips{position:sticky;top:var(--nav-h);z-index:15;display:flex;overflow-x:auto;scrollbar-width:none;padding:0 var(--gutter);margin:0 calc(-1*var(--gutter)) var(--s5);border-bottom:1px solid var(--rule);background:var(--paper);scroll-snap-type:x proximity}
.dchip{position:relative;flex:none;display:grid;justify-items:center;align-content:center;min-width:48px;height:var(--chips-h);text-decoration:none;scroll-snap-align:start}
.dchip::after{content:"";position:absolute;left:10px;right:10px;bottom:6px;height:3px;background:var(--c)}
.dchip b{font:400 21px/1 var(--f-num)}.dchip i{font:500 10.5px var(--f-mono);font-style:normal;color:var(--muted)}
.dchip[aria-current="true"]{background:var(--sunk)}
.dchip.is-today{background:var(--ink);color:var(--paper)}.dchip.is-today i{color:inherit}
.legend{display:flex;flex-wrap:wrap;gap:var(--s2) var(--s4);font:500 12px var(--f-body);color:var(--muted);margin-bottom:var(--s5)}
.legend span{display:inline-flex;align-items:center;gap:6px}
.legend .mark{margin:0}

/* day */
.days{display:grid;gap:var(--s6)}
.day{border-top:2px solid var(--rule-strong);scroll-margin-top:calc(var(--nav-h) + var(--chips-h) + 8px)}
.day>summary{list-style:none;cursor:pointer}
.day>summary::-webkit-details-marker{display:none}
.day-head{display:grid;padding:var(--s4) 0;gap:0 var(--s4);grid-template-columns:auto minmax(0,1fr) var(--tap);
 grid-template-areas:"num city caret" "num title caret" "num mood mood" "num stay stay" "num light light"}
.day-meta{display:contents}
.day-num{grid-area:num;display:flex;align-items:baseline;gap:2px;color:var(--c)}
.day-num .m,.day-num .slash{font:400 18px var(--f-num);color:var(--muted)}
.day-num .d{font:400 56px/.9 var(--f-num)}
.day-num .wd{font:500 11px var(--f-mono);color:var(--muted);margin-left:6px}
.day-city{grid-area:city;font:600 12px var(--f-body);letter-spacing:.04em;color:var(--c);align-self:center}
.day-city .local{font:italic 400 15px var(--f-num);color:var(--muted);margin-left:4px}
.day h3{grid-area:title;font:700 clamp(22px,5.6vw,28px)/1.3 var(--f-display);margin-top:var(--s1)}
.mood{grid-area:mood;font-size:15px;color:var(--ink-2);margin-top:var(--s2)}
.stay{grid-area:stay;font-size:13px;color:var(--muted);margin-top:var(--s3);display:flex;gap:var(--s2);align-items:center;flex-wrap:wrap}
.stay span{border:1px solid var(--rule);border-radius:3px;font:500 11px var(--f-mono);padding:1px 5px}
.caret{grid-area:caret;justify-self:end;width:var(--tap);height:var(--tap);display:grid;place-items:center}
.caret::before{content:"";width:9px;height:9px;border-right:1.5px solid var(--muted);border-bottom:1.5px solid var(--muted);transform:rotate(45deg) translateY(-2px);transition:transform .2s}
details[open] .caret::before{transform:rotate(-135deg)}
.daylight{grid-area:light;position:relative;height:6px;margin:var(--s4) 0 var(--s5);border-radius:1px;
 background:linear-gradient(90deg,var(--night-band) var(--sr),var(--day-band) var(--sr) var(--ss),var(--night-band) var(--ss))}
.daylight i{position:absolute;top:-4px;width:1.5px;height:14px;background:var(--ink);transform:translateX(-50%)}
.daylight i.now{background:var(--warn);width:2px;height:18px;top:-6px}
.daylight .sr,.daylight .ss{position:absolute;top:12px;background:var(--paper);padding:0 3px;font:500 10px var(--f-mono);color:var(--muted);transform:translateX(-50%)}
.daylight .sr{left:var(--sr)}.daylight .ss{left:var(--ss)}
.day-body{display:grid}
.tl{list-style:none;margin:0;padding:var(--s2) 0 var(--s4)}
.tl li{display:grid;grid-template-columns:48px 20px minmax(0,1fr);gap:0 var(--s3);padding-block:10px;position:relative}
.tl li::before{content:"";position:absolute;left:calc(48px + var(--s3) + 9.5px);top:0;bottom:0;width:1px;background:var(--rule)}
.tl li:first-child::before{top:18px}.tl li:last-child::before{bottom:auto;height:18px}
.tl .t{font:400 13px/1.6 var(--f-mono);color:var(--muted);font-variant-numeric:tabular-nums}
.tl .x{font-size:15.5px;line-height:1.65;min-width:0}.tl .x b{color:var(--ink)}
.mark{position:relative;z-index:1;justify-self:center;width:11px;height:11px;margin-top:7px;border-radius:50%;background:var(--paper);border:1.5px solid var(--muted)}
.k-go .mark{border-radius:1px}
.k-see .mark{background:var(--delft);border-color:var(--delft)}
.k-eat .mark{background:var(--lamp);border-color:var(--lamp)}
.k-book .mark{background:var(--ok);border-color:var(--ok)}
.k-todo .mark{background:var(--warn-wash);border:2.5px solid var(--warn)}
.k-rest .mark{width:10px;height:2px;border:0;border-radius:0;background:var(--muted);margin-top:12px}
.k-run .mark{border-color:var(--delft)}
.plink{color:var(--ink);text-decoration:underline 1.5px var(--delft);text-underline-offset:3px;padding-block:4px}
.plink b{color:inherit}.plink::after{content:"↗";font:500 .78em var(--f-mono);color:var(--delft);margin-left:2px}
.chip{display:inline-block;font:500 11px/1 var(--f-mono);letter-spacing:.06em;padding:3px 6px;border-radius:3px;border:1px solid currentColor;margin-left:6px;vertical-align:2px}
.chip.k-book{color:var(--ok)}.chip.k-todo{color:var(--paper);background:var(--warn);border-color:var(--warn)}
.fact{margin:0 0 var(--s5) calc(48px + 20px + 2*var(--s3));padding:0 0 0 var(--s4);border-left:2px solid var(--delft);font:400 15px/1.75 var(--f-display);color:var(--ink-2);display:grid;gap:2px}
.fact span{font:500 11px var(--f-mono);letter-spacing:.14em;color:var(--delft)}
.day-act{padding:0 0 var(--s5)}
@media(min-width:761px){.tl,.fact{max-width:720px}}
.pl .pin::before,.stayc .pin::before{width:11px;height:11px}
.pin{display:inline-flex;align-items:center;justify-content:center;gap:var(--s2);min-height:var(--tap);min-width:var(--tap);border-radius:var(--r);border:1px solid var(--rule);color:var(--ink);font:500 13.5px var(--f-body);text-decoration:none;padding:0 var(--s4)}
.pin::before{content:"";width:9px;height:9px;border-radius:50% 50% 50% 0;transform:rotate(-45deg);background:var(--delft)}
.pin:hover{border-color:var(--ink)}
.pin-strong{width:100%;min-height:48px;background:var(--ink);color:var(--paper);border:0;font:600 15px var(--f-body)}
.pin-strong::before{background:var(--sun)}
@media(min-width:761px){.pin-strong{width:auto;padding-inline:var(--s5)}}

/* guides */
.guides{display:grid;gap:var(--s7)}
.guide{border-top:2px solid var(--rule-strong);padding-top:var(--s5);display:grid;gap:var(--s5);scroll-margin-top:var(--nav-h)}
.g-head{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:baseline;gap:var(--s1) var(--s4)}
.g-head h3{font:700 clamp(26px,6vw,36px)/1.25 var(--f-display)}
.g-dates{font:500 12px var(--f-mono);color:var(--c)}
.g-body{display:grid;grid-template-columns:minmax(0,1.2fr) minmax(0,1fr);gap:var(--s6)}
.g-story{display:grid;gap:var(--s4);align-content:start}
.g-story p{font:400 17px/1.8 var(--f-display)}
.g-facts{margin:0;display:grid;grid-template-columns:auto minmax(0,1fr);border-top:1px solid var(--rule);padding-top:var(--s3);gap:6px var(--s4);font-size:14px}
.g-facts dt{font:500 11.5px var(--f-mono);letter-spacing:.08em;color:var(--muted);padding-top:3px}.g-facts dd{margin:0}
.dishes{list-style:none;margin:var(--s2) 0 0;padding:0;border-top:1px solid var(--rule)}
.dishes li{display:flex;flex-wrap:wrap;align-items:baseline;column-gap:var(--s2);padding:var(--s3) 0;border-bottom:1px solid var(--rule)}
.dishes b{order:0;font-weight:700}
.dishes li::before{content:"";order:1;flex:1;min-width:24px;border-bottom:1px dotted var(--muted);transform:translateY(-4px)}
.dishes i{order:2;font:italic 400 16px var(--f-num);color:var(--ink-2)}
.dishes span{order:3;flex-basis:100%;font-size:13.5px;color:var(--muted)}
.places{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:1fr;gap:0 var(--s6);border-top:1px solid var(--rule)}
@media(min-width:761px){.places{grid-template-columns:1fr 1fr}}
.pl{display:grid;grid-template-columns:minmax(0,1fr) var(--tap);grid-template-areas:"top pin" "name pin" "dish pin" "why pin";gap:2px var(--s3);border-bottom:1px solid var(--rule);padding:var(--s3) 0;min-width:0}
.pl-top{grid-area:top;display:flex;gap:var(--s2);align-items:center}
.pl-name{grid-area:name;font-weight:700;font-size:16px;line-height:1.4}
.pl-dish{grid-area:dish;color:var(--ink-2);font-size:14px}
.pl-why{grid-area:why;font-size:13.5px;color:var(--muted)}
.pl .pin{grid-area:pin;align-self:center;width:var(--tap);height:var(--tap);padding:0}
.when{font:500 11.5px var(--f-mono);color:var(--muted)}
.badge{font:500 11px var(--f-mono);letter-spacing:.06em;padding:2px 6px;border-radius:3px}
.b-top{background:var(--ink);color:var(--paper)}
.b-alt{color:var(--muted);border:1px solid var(--rule)}
.star{font:500 12px var(--f-mono);color:var(--muted);margin-left:var(--s2)}
.more>summary{min-height:var(--tap);display:flex;align-items:center;font:500 13px var(--f-body);letter-spacing:.02em;color:var(--delft);cursor:pointer;list-style:none}
.more>summary::-webkit-details-marker{display:none}
.more>summary::before{content:"+";margin-right:8px}.more[open]>summary::before{content:"−"}

/* stays */
.stays{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:1fr;gap:0 var(--s6);border-top:2px solid var(--rule-strong)}
@media(min-width:761px){.stays{grid-template-columns:1fr 1fr}}
.stayc{display:grid;grid-template-columns:minmax(0,1fr) var(--tap);grid-template-areas:"top pin" "name pin" "addr pin" "note pin";gap:2px var(--s3);padding:var(--s3) 0;border-bottom:1px solid var(--rule)}
.stay-top{grid-area:top;display:flex;gap:var(--s3);align-items:center;font:500 12px var(--f-mono);color:var(--muted)}
.sbadge{font:500 11px var(--f-mono);padding:2px 6px;border-radius:3px}
.s-ok{color:var(--ok);border:1px solid currentColor}.s-todo{color:var(--paper);background:var(--warn)}
.stay-name{grid-area:name;font-weight:700;font-size:16.5px}
.stay-addr{grid-area:addr;font-size:13.5px;color:var(--ink-2)}.stay-note{grid-area:note;font-size:13px;color:var(--muted)}
.stayc .pin{grid-area:pin;align-self:center;width:var(--tap);height:var(--tap);padding:0}

/* checklist */
.progress{display:flex;align-items:center;gap:var(--s3);font:500 13px var(--f-mono);color:var(--muted);margin-bottom:var(--s5)}
.progress b{color:var(--ink)}
.progress::after{content:"";flex:1;height:2px;background:linear-gradient(90deg,var(--ok) var(--p,0%),var(--rule) 0)}
.alldone{font:400 15px var(--f-display);color:var(--ok);margin:-12px 0 var(--s5)}
.todo-wrap{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,320px),1fr));gap:var(--s6)}
.tgroup>.label{display:block;padding-bottom:var(--s2);border-bottom:2px solid var(--rule-strong);color:var(--ink)}
details.tgroup>summary{list-style:none;cursor:pointer;min-height:var(--tap);display:flex;align-items:flex-end}
details.tgroup>summary::-webkit-details-marker{display:none}
details.tgroup>summary::after{content:"+";margin-left:auto;font-size:14px}
details.tgroup[open]>summary::after{content:"−"}
.tgroup ul{list-style:none;margin:0;padding:0}
.tgroup label,.tgroup li.static{display:grid;grid-template-columns:24px 52px minmax(0,1fr);gap:var(--s3);min-height:52px;padding:var(--s3) 0;border-bottom:1px solid var(--rule);cursor:pointer;align-items:start}
.tgroup li.static{cursor:default;grid-template-columns:40px 52px minmax(0,1fr);color:var(--muted)}
.tgroup label:active{background:var(--sunk)}
.tgroup input{position:absolute;opacity:0;width:1px;height:1px}
.box{width:22px;height:22px;border:1.5px solid var(--ink-2);border-radius:3px;margin-top:1px;display:grid;place-items:center}
.tgroup input:checked+.box{background:var(--ok);border-color:var(--ok)}
.tgroup input:checked+.box::after{content:"";width:5px;height:10px;border:solid var(--paper);border-width:0 2px 2px 0;transform:rotate(45deg) translate(-1px,-1px)}
.tgroup input:checked~.titem{text-decoration:line-through;color:var(--muted)}
.tdate{font:500 12.5px var(--f-mono);color:var(--muted);padding-top:2px}
.titem{display:grid;font-size:15px}.titem small{font-size:12.5px;color:var(--muted)}
.sicon{font:500 11px var(--f-mono);padding-top:3px}
.subhead{margin-top:var(--s7)}

/* info */
.prac{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,290px),1fr));gap:0 var(--s6)}
.card{border-top:2px solid var(--rule-strong);padding:var(--s4) 0 var(--s6);display:grid;gap:var(--s3);align-content:start;min-width:0}
.card.wide{grid-column:1/-1}
.card h3{font:700 20px/1.3 var(--f-display)}
.card ul{list-style:none;margin:0;padding:0;display:grid;gap:6px;font-size:15px}
.card li{position:relative;padding-left:var(--s4)}
.card li::before{content:"";position:absolute;left:0;top:.85em;width:7px;height:1px;background:var(--muted)}
.big{font:400 56px/1 var(--f-num);color:var(--delft)}
table{border-collapse:collapse;width:100%;font-size:14px}
th,td{text-align:left;padding:var(--s2) var(--s3) var(--s2) 0;border-bottom:1px solid var(--rule);vertical-align:top}
th{font:500 11px var(--f-mono);letter-spacing:.1em;color:var(--muted)}
.trains td:nth-child(3){font-family:var(--f-body);font-variant-numeric:tabular-nums;white-space:nowrap;font-size:13px}
footer{padding-block:var(--s7) var(--s8);color:var(--muted);font-size:13px;border-top:1px solid var(--rule);margin-top:var(--s8)}

/* phone */
@media(max-width:760px){
 :root{--nav-h:0px}
 .cover .wrap{grid-template-columns:minmax(0,1fr);gap:var(--s6);padding-block:var(--s7) var(--s6)}
 .nav{position:fixed;top:auto;bottom:0;left:0;right:0;border-bottom:0;border-top:1px solid var(--rule);padding-bottom:env(safe-area-inset-bottom,0px)}
 .nav .wrap{padding:0}
 .nav ul{overflow:visible}
 .nav li{flex:1}
 .nav a{height:56px;justify-content:center;padding:0;font-size:13px}
 .nav a[aria-current="true"]{box-shadow:inset 0 2px var(--ink)}
 .today{position:fixed;right:max(16px,env(safe-area-inset-right,0px));bottom:calc(68px + env(safe-area-inset-bottom,0px));height:var(--tap);box-shadow:0 4px 14px rgb(0 0 0 / .25)}
 body{padding-bottom:calc(56px + env(safe-area-inset-bottom,0px))}
 .dchips{top:env(safe-area-inset-top,0px);border-bottom:0;box-shadow:0 1px 0 var(--rule)}
 .day{scroll-margin-top:calc(var(--chips-h) + 8px)}
 .legend{display:none}
 .day-head{grid-template-areas:"num city caret" "title title title" "mood mood mood" "stay stay stay" "light light light"}
 .day-num .d{font-size:40px}
 .day:not([open]) .mood,.day:not([open]) .stay{display:none}
 .day:not([open]) .daylight{margin-bottom:0}
 .fact{margin-left:0}
 .g-body{grid-template-columns:minmax(0,1fr)}
 .trains,.trains tbody,.closed,.closed tbody{display:block}
 .trains thead,.closed thead{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}
 .trains tr{display:grid;grid-template-columns:48px minmax(0,1fr) auto;gap:2px var(--s3);padding:var(--s3) 0;border-bottom:1px solid var(--rule)}
 .trains td,.closed td{padding:0;border:0}
 .trains td:nth-child(4){grid-column:2/-1;font-size:13px;color:var(--muted)}
 .closed tr{display:grid;padding:var(--s3) 0;border-bottom:1px solid var(--rule)}
 .closed td:first-child{font-weight:700}
 .closed td:nth-child(3){font:500 12.5px var(--f-mono);color:var(--muted)}
}
@media print{.nav,.today,.dchips{display:none}}
"""

JS = r"""
<script>
(function(){
  var start=new Date(2026,11,5), end=new Date(2026,11,19);
  var europe=new Intl.DateTimeFormat('en-GB',{timeZone:'Europe/Amsterdam',year:'numeric',month:'numeric',day:'numeric',hour:'numeric',minute:'numeric',hourCycle:'h23'}).formatToParts(new Date());
  var now={}; europe.forEach(function(part){now[part.type]=Number(part.value);});
  var today=new Date(now.year,now.month-1,now.day);
  var cd=document.getElementById('countdown'), btn=document.getElementById('todayBtn'), todayId=null;
  if(today<start){cd.innerHTML='還有 <b>'+Math.round((start-today)/864e5)+'</b> 天出發';}
  else if(today<=end){
    todayId='d12'+String(today.getDate()).padStart(2,'0');
    cd.innerHTML='旅行第 <b>'+(Math.round((today-start)/864e5)+1)+'</b> 天';
    var el=document.getElementById(todayId);
    if(el){btn.href='#'+todayId;btn.hidden=false;
      document.querySelectorAll('[data-day="'+todayId.slice(1)+'"]').forEach(function(e){e.classList.add('is-today');});
      var bar=el.querySelector('.daylight'); if(bar){var p=(now.hour+now.minute/60-6)/18*100;
        if(p>=0&&p<=100){var i=document.createElement('i');i.className='now';i.style.left=p+'%';bar.appendChild(i);}}}
  } else {cd.textContent='旅程結束，歡迎回家。';}
  var mobile=window.matchMedia('(max-width: 760px)').matches;
  var days=document.querySelectorAll('details.day');
  if(mobile){days.forEach(function(d,i){d.open=todayId?d.id===todayId:i===0;});}
  else{document.querySelectorAll('details.tgroup.fold').forEach(function(d){d.open=true;});}
  function openHash(){var h=location.hash.slice(1),el=h&&document.getElementById(h); if(el&&el.tagName==='DETAILS')el.open=true;}
  window.addEventListener('hashchange',openHash); openHash();
  if(location.hash){
    var target=document.getElementById(location.hash.slice(1));
    if(target)requestAnimationFrame(function(){target.scrollIntoView({behavior:'instant'});});
  }
  document.querySelectorAll('a[href^="#d1"]').forEach(function(a){a.addEventListener('click',function(){var el=document.getElementById(a.getAttribute('href').slice(1)); if(el)el.open=true;});});
  // checklist
  var boxes=document.querySelectorAll('input[data-todo]'), out=document.getElementById('todoCount'), prog=document.querySelector('.progress'), done=document.getElementById('allDone');
  function count(){var n=0;boxes.forEach(function(b){if(b.checked)n++;});out.textContent=n;prog.style.setProperty('--p',(boxes.length?n/boxes.length*100:0)+'%');done.hidden=n!==boxes.length;}
  var saved={}; try{saved=JSON.parse(localStorage.getItem('trip-todos-v3')||'{}');}catch(e){}
  boxes.forEach(function(b){ if(saved[b.dataset.todo])b.checked=true;
    b.addEventListener('change',function(){saved[b.dataset.todo]=b.checked;try{localStorage.setItem('trip-todos-v3',JSON.stringify(saved));}catch(e){}count();});});
  count();
  // Track sections and dates from the same reading line just below the sticky bars.
  var navLinks={}, chips={}, queued=false, activeNav=null, activeDate=null;
  document.querySelectorAll('.nav li a').forEach(function(a){navLinks[a.hash.slice(1)]=a;});
  document.querySelectorAll('.dchip').forEach(function(a){chips[a.dataset.day]=a;});
  var sections=Array.from(document.querySelectorAll('.block, #guides, .chapter, .guide'));
  var dates=Array.from(document.querySelectorAll('.chapter, .day, .guide'));
  var row=document.querySelector('.dchips');
  function current(previous,next){
    if(previous!==next){
      if(previous)previous.removeAttribute('aria-current');
      if(next)next.setAttribute('aria-current','true');
    }
    return next;
  }
  function watch(){
    queued=false;
    var line=(mobile?0:48)+row.offsetHeight+28, nav=null, date=null;
    sections.forEach(function(s){
      if(s.getBoundingClientRect().top<=line){
        nav=navLinks[s.id]||navLinks[s.classList.contains('guide')?'guides':'days'];
      }
    });
    if(document.getElementById('days').getBoundingClientRect().bottom>line){
      dates.forEach(function(s){
        if(s.getBoundingClientRect().top<=line)date=chips[s.dataset.first||s.id.slice(1)]||null;
      });
    }
    activeNav=current(activeNav,nav);
    if(activeDate!==date && date){
      var l=date.offsetLeft, r=l+date.offsetWidth;
      if(l<row.scrollLeft||r>row.scrollLeft+row.clientWidth){
        row.scrollTo({left:l-16,behavior:'instant'});
      }
    }
    activeDate=current(activeDate,date);
  }
  function queue(){if(!queued){queued=true;requestAnimationFrame(watch);}}
  window.addEventListener('scroll',queue,{passive:true});
  window.addEventListener('resize',queue);
  document.addEventListener('toggle',queue,true);
  queue();
})();
</script>
"""

def body():
    todo_html, ntodo = bookings()
    return f'''
<a class="skip-link" href="#main">跳到內容</a>
<header class="cover">
  {photo('cover', 'cover-photo', '100vw', priority=True)}
  <div class="wrap cover-copy">
    <div class="cover-mast"><span>WINTER RAIL JOURNAL</span><span>EUROPE / 2026</span></div>
    <div class="cover-title">
      <div class="eyebrow">PRIVATE ITINERARY · WINTER 2026</div>
      <h1>從低地<br>到萊茵河</h1>
      <p class="sub"><span class="nb">荷蘭・比利時・德國</span><span class="nb">冬日十五天 · 12.5–12.19</span></p>
      <div class="countdown" id="countdown">12 月 5 日出發</div>
    </div>
    <a class="cover-index" href="#overview">翻開目錄 <span aria-hidden="true">↓</span></a>
  </div>
</header>

<nav class="nav" aria-label="章節">
  <div class="wrap">
    <ul>
      <li><a href="#overview">總覽</a></li>
      <li><a href="#days">每日</a></li>
      <li><a href="#guides">吃喝</a></li>
      <li><a href="#stays">住宿</a></li>
      <li><a href="#todo">出發前</a></li>
      <li><a href="#info">須知</a></li>
    </ul>
    <a class="today" id="todayBtn" href="#days" hidden>今天</a>
  </div>
</nav>

<main class="wrap" id="main" tabindex="-1">
  <section class="block" id="overview">
    <div class="block-head"><div class="kicker">Overview</div><h2>十五天，一眼看完</h2><p>點任何一天，就翻到那一天。</p></div>
    <div class="contents-spread">
      <div>
        <div class="kicker">Contents · 目錄</div>
        <ol class="contents">{chapter_index()}</ol>
      </div>
      <aside class="route-panel" aria-label="旅行路線與日照">
        <div class="kicker">The route · 路線</div>
        {route_svg()}
        <div class="maplegend"><span><i></i>過夜城市</span><span><em></em>一日遊</span></div>
        {cover_strips()}
        <div class="strips-cap">十五天的日照：金色是白天，大約 08:30 到 16:30</div>
        <div class="stats">
          <div class="stat"><b>15</b><span>天</span></div>
          <div class="stat"><b>3</b><span>個國家</span></div>
          <div class="stat"><b>10</b><span>座城市</span></div>
          <div class="stat"><b>9</b><span>個聖誕市集</span></div>
        </div>
      </aside>
    </div>
    <details class="index-fold"><summary>十五天行程一覽</summary><div class="ovlist">{overview()}</div></details>
    <section class="food-index" id="guides">
      <div class="block-head"><div class="kicker">Eat &amp; drink</div><h2>每座城市，該吃什麼</h2><p>每家店都對照過 Google 評分、旅遊指南和 Threads 上的心得才放進來。標了日期的，已經排進行程。</p></div>
      <ul>{food_index()}</ul>
    </section>
  </section>

  <section class="block" id="days">
    <div class="dchips" role="navigation" aria-label="選擇日期">{daychips()}</div>
    <div class="block-head days-heading"><div class="kicker">Day by day</div><h2>每日行程</h2><p>金色店名點了就開地圖；「今日路線」會把當天要去的地方一次放進 Google Maps。點日期可以收合。日期下那條細線是當天的日照：金色是白天，刻度是每一站的時間。</p></div>
    <div class="legend">
      <span class="k-go"><span class="mark"></span>交通</span>
      <span class="k-see"><span class="mark"></span>景點</span>
      <span class="k-eat"><span class="mark"></span>吃喝</span>
      <span class="k-book"><span class="mark"></span>已訂</span>
      <span class="k-todo"><span class="mark"></span>待訂</span>
      <span class="k-rest"><span class="mark"></span>休息</span>
      <span class="k-run"><span class="mark"></span>運動</span>
    </div>
    {chapters()}
  </section>

  <section class="block" id="stays">
    <div class="block-head"><div class="kicker">Where you sleep</div><h2>今晚睡哪裡</h2><p>7 間旅館、14 晚。入住和退房時間以訂房確認信為準。</p></div>
    <ul class="stays">{stays()}</ul>
  </section>

  <section class="block" id="todo">
    <div class="block-head"><div class="kicker">Before you go</div><h2>出發前要訂好的事</h2><p>打勾只會存在這支手機上。兩個人一起出發，就讓一個人負責勾，訂好了在群組說一聲。</p></div>
    <div class="progress">已完成 <b id="todoCount">0</b> / {ntodo}</div>
    <p class="alldone" id="allDone" hidden>都訂好了，可以專心期待出發。</p>
    <div class="todo-wrap">{todo_html}</div>
    <div class="card wide subhead">
      <div class="label">營業日</div>
      <h3>營業日都對過了</h3>
      <table class="closed"><thead><tr><th>地方</th><th>要注意</th><th>我們哪天去</th></tr></thead><tbody>{closed()}</tbody></table>
    </div>
  </section>

  <section class="block" id="info">
    <div class="block-head"><div class="kicker">Good to know</div><h2>旅途須知</h2><p>天氣、交通、喝酒的規矩和緊急電話，都收在這裡。</p></div>
    <div class="prac">
      <div class="card">
        <div class="label">12 月天氣</div>
        <div class="big">0–7°C</div>
        <ul><li>常下雨、風大，體感比溫度冷。</li><li>日出約 08:20–08:45，日落約 16:30–16:40，戶外行程排在白天。</li><li>聖誕市集晚上最好看。</li></ul>
      </div>
      <div class="card">
        <div class="label">行李</div>
        <h3>要帶的東西</h3>
        <ul><li>防風防水外套，裡面洋蔥式穿法</li><li>好走的防水鞋，石板路很多</li><li>毛帽、手套、圍巾、摺疊傘</li><li>歐規轉接頭（Type C／F，230V）</li><li>跑步裝備：12/7、12/12、12/14、12/17 有晨跑</li><li>12/9 滑雪：手套、厚襪，雪衣雪鞋現場租</li></ul>
      </div>
      <div class="card">
        <div class="label">錢和 App</div>
        <h3>付款與交通</h3>
        <ul><li>幾乎都能刷卡；少數老啤酒屋只收現金，帶一點歐元。</li><li>荷蘭火車、電車直接刷信用卡進出（OVpay），出站也要刷。</li><li>App：NS（荷蘭）、SNCB（比利時）、DB Navigator（德國）、Google Maps。</li><li>把這頁加到手機主畫面，收訊差時比較好開。</li></ul>
      </div>
      <div class="card wide">
        <div class="label">火車</div>
        <h3>火車一覽</h3>
        <table class="trains"><thead><tr><th>日期</th><th>路段</th><th>車程</th><th>備註</th></tr></thead><tbody>{trains()}</tbody></table>
      </div>
      <div class="card wide">
        <div class="label">備案</div>
        <h3>出狀況怎麼辦</h3>
        <ul>{lis(BACKUPS)}</ul>
      </div>
      <div class="card">
        <div class="label">啤酒規矩</div>
        <h3>三地三種喝法</h3>
        <ul><li><b>比利時</b>：每款酒有專用杯，修道院啤酒常在 8–10% 以上，小心後勁。</li><li><b>科隆 Kölsch</b>：0.2 公升小杯，空了服務生會自動補，把杯墊蓋在杯口才會停。</li><li><b>杜塞道夫 Altbier</b>：深色、每家只賣自己釀的，在這裡別點 Kölsch。</li></ul>
      </div>
      <div class="card">
        <div class="label">伴手禮</div>
        <h3>帶什麼回家</h3>
        <ul>{lis(SOUVENIRS)}</ul>
      </div>
      <div class="card">
        <div class="label">緊急</div>
        <h3>先存起來</h3>
        <ul><li>歐盟緊急電話：<b class="mono">112</b></li><li>外交部旅外急難救助：<span class="mono">+800-0885-0885</span>（全球免付費）</li><li>駐荷蘭（海牙）、駐比利時（布魯塞爾）、駐德國（柏林）都有台北代表處，出發前把地址和電話存進手機。</li></ul>
      </div>
    </div>
  </section>
</main>

<footer class="wrap"><p>營業時間、票價和車次查於 2026 年 11 月，出發前一週請再用 Google Maps 或官網確認一次。★ 評分來自 Google 地圖，推薦參考旅遊指南、評論網站和 Threads。</p>
<details class="photo-credits"><summary>照片來源與授權</summary><p>照片用於介紹地點與料理。料理圖片不一定拍自推薦店家；照片已轉檔及縮放，顯示時可能裁切。改作沿用各照片的原授權。</p><ul>{credits()}</ul></details>
</footer>
{JS}'''

HEAD_LINKS = '<link rel="preload" href="assets/fonts/noto-serif-tc.woff2" as="font" type="font/woff2" crossorigin>'
FONTS_CSS = (ROOT / "src/fonts.css").read_text(encoding="utf-8")
BOOK_CSS = (ROOT / "src/book.css").read_text(encoding="utf-8")

def build(artifact_path, site_path):
    b = "\n".join(line.rstrip() for line in body().splitlines())
    artifact = (f'<title>荷比德冬季旅行手冊</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n{HEAD_LINKS}\n<style>{FONTS_CSS}{CSS}{BOOK_CSS}</style>\n{b}\n')
    site = ('<!doctype html>\n<html lang="zh-Hant">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            '<meta name="robots" content="noindex, nofollow">\n<meta name="theme-color" content="#0F1F45">\n<title>荷比德冬季旅行手冊</title>\n'
            f'{HEAD_LINKS}\n<style>[hidden]{{display:none!important}} img{{max-width:100%}} :root{{padding-top:env(safe-area-inset-top,0px)}}{FONTS_CSS}{CSS}{BOOK_CSS}</style>\n</head>\n<body>\n{b}\n</body>\n</html>\n')
    # Public page: private terms are blocked by hash so this public source does not name them.
    import hashlib
    for n, h in [(2, '8f5039a6dfad4305'), (2, '9a155d48a53c7936'), (3, 'ae56c663b674b148'), (3, 'c81ed803e323ad7f')]:
        hits = {site[i:i+n] for i in range(len(site)-n+1)
                if hashlib.sha256(site[i:i+n].encode()).hexdigest()[:16] == h}
        assert not hits, "Privacy check failed (blocked term)"
    flights = re.findall(r"\b(?:CI|EK|BR|KL|LH|SN|TK|JL|NH|CX)\s?\d{2,4}\b", site)
    assert not flights, "Privacy check failed (blocked code)"
    Path(site_path).write_text(site, encoding="utf-8")
    Path(artifact_path).write_text(artifact, encoding="utf-8")
    print("built", len(site))

if __name__ == "__main__":
    # Usage: python3 src/build.py            -> writes index.html (the GitHub Pages site)
    #        python3 src/build.py SITE [ART] -> also writes a fragment for a Claude artifact
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    site = sys.argv[1] if len(sys.argv) > 1 else os.path.join(root, "index.html")
    art = sys.argv[2] if len(sys.argv) > 2 else os.devnull
    build(art, site)
