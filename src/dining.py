"""Render the standalone pocket dining directory from the public booklet data."""
from collections import defaultdict
from food_map_data import AREA_POINTS
from booklet_data import CITIES, FOOD_DIRECTORY, FOOD_CHAPTER_EXTRAS, FOOD_CITY_NOTES, GUIDES

KINDS = ('正餐', '點心', '咖啡', '喝一杯', '市集')
DISH_GUIDES = {'ams':'ams', 'dh':'dh', 'rtm':'rtm', 'bru':'bru', 'bxl':'bxl', 'kol':'kol', 'dus':'dus'}
GUIDE_ANCHORS = {'utr':'ams','lei':'dh',**DISH_GUIDES}
MARKET = '大教堂前＋Heinzels 聖誕市集'

def entries():
    rows = list(FOOD_DIRECTORY)
    for guide in GUIDES:
        for badge, name, order, _rating, feature, query, _date in guide['places']:
            if name not in FOOD_CHAPTER_EXTRAS:
                continue
            city, area, kind = FOOD_CHAPTER_EXTRAS[name]
            rows.append((city, area, kind, name, badge == '首選', order, feature, '', query))
    return rows

def page(esc, maps):
    cities = {key: defaultdict(list) for key in CITIES}
    for city, area, *rest in entries():
        cities[city][area].append(rest)
    guides = {g['key']: g for g in GUIDES}
    tabs, sections = [], []
    for key, areas in cities.items():
        city = CITIES[key]
        label = esc(city['name'])
        tabs.append(f'<a href="#city-{key}" data-city="{key}">{label}</a>')
        groups = []
        for area, places in areas.items():
            cards = []
            for kind, name, pick, order, feature, note, query in sorted(places, key=lambda p: not p[2]):
                tip = f'<p class="food-tip">{esc(note)}</p>' if note else ''
                meta = f'<span class="food-pick">首選</span>' if pick else ''
                if name == MARKET:
                    links = [('大教堂前地圖', 'Weihnachtsmarkt am Kölner Dom'), ('Heinzels 地圖', query)]
                else:
                    links = [('地圖', query)]
                links = ''.join(f'<a href="{esc(maps(q))}" target="_blank" rel="noopener" aria-label="{esc(name)}：{esc(t)}">{esc(t)} <span aria-hidden="true">↗</span></a>' for t,q in links)
                cards.append(f'''<li class="food-place" data-kind="{esc(kind)}">
  <div class="food-meta">{esc(kind)} {meta}</div><h4>{esc(name)}</h4>
  <p class="food-order"><span>該點</span> {esc(order)}</p>
  <p>{esc(feature)}</p>{tip}<div class="food-maps">{links}</div>
</li>''')
            lat, lon = AREA_POINTS[(key, area)]
            coords = f' data-point="{lat},{lon}"'
            groups.append(f'''<section class="food-area" data-area="{esc(area)}"{coords}><h3 tabindex="-1">{esc(area)}</h3><ul>{''.join(cards)}</ul></section>''')
        dishes = guides.get(DISH_GUIDES.get(key), {}).get('dishes', [])
        chapter = GUIDE_ANCHORS.get(key)
        dish_list = ''.join(f'<li><b>{esc(name)}</b> <i>{esc(original)}</i> — {esc(note)}</li>' for name,original,note in dishes)
        details = (f'''<details class="food-special"><summary>先認識當地吃什麼</summary><ul>{dish_list}</ul>
<a href="index.html#g-{chapter}">回旅行書看菜色照片 ↗</a></details>''' if dishes else '')
        sections.append(f'''<section class="food-city" id="city-{key}" data-panel="{key}">
  <header><p>{esc(city['local'])}</p><h2>{label}</h2><p>{esc(FOOD_CITY_NOTES[key])}</p></header>
  {details}
  {''.join(groups)}
</section>''')
    kinds = ''.join(f'<option>{kind}</option>' for kind in KINDS)
    return f'''
<a class="skip-link" href="#food-main">跳到吃喝清單</a>
<header class="food-mast"><div class="wrap">
  <a href="index.html#overview">← 回旅行手冊</a><span>WINTER RAIL JOURNAL</span>
</div></header>
<main class="wrap food-main" id="food-main" tabindex="-1">
  <header class="food-intro"><p class="kicker">Pocket guide · 01 / 吃喝</p><h1>這附近吃什麼？</h1>
  <p>先選你在哪座城，點地圖看街區，或搜尋想吃的菜。每家都列出該點什麼、特色和地圖。</p></header>
  <nav class="food-cities" aria-label="選擇城市">{''.join(tabs)}</nav>
  <div class="food-filters" hidden>
    <label>找店或菜名<input type="search" placeholder="例如：淡菜、蘋果派" id="food-search" autocomplete="off"></label>
    <label>街區<select id="food-area"><option value="">所有街區</option></select></label>
    <label>餐別<select id="food-kind"><option value="">所有餐別</option>{kinds}</select></label>
    <p id="food-count" role="status"></p>
  </div>
  <details class="food-map" data-tiles="https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png" hidden open>
    <summary><span class="food-map-title">街區地圖 <small data-map-city></small></span><span class="food-map-toggle" aria-hidden="true"></span></summary>
    <div class="food-map-canvas" role="region" aria-label="吃喝街區地圖"></div>
    <p class="food-map-status" role="status"></p>
    <div class="food-map-foot">
      <p>數字是這區符合菜名與餐別的選擇。點一下篩選；店家地址以各店的 Google Maps 連結為準。</p>
      <div class="food-map-tools" hidden>
        <button type="button" data-map-reset>回到全城</button>
        <button type="button" data-map-drag aria-pressed="false">移動地圖</button>
        <button type="button" data-clear-area hidden>清除街區篩選</button>
      </div>
    </div>
  </details>
  <p class="food-empty" hidden>這個條件沒有結果。可以換街區、餐別或關鍵字。</p>
  {''.join(sections)}
</main>
<footer class="wrap food-footer">整理自旅伴的美食清單與手冊選店。菜單、營業時間和訂位方式以店家公告為準。</footer>
<script src="src/food-map.js" defer></script>
<script src="src/food.js" defer></script>'''
