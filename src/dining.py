"""Render the city-by-city pocket dining guide."""
from collections import defaultdict
from food_map_data import AREA_POINTS
from booklet_data import (CITIES, FOOD_DIRECTORY, FOOD_CHAPTER_EXTRAS, FOOD_EXTRA_COPY,
                          FOOD_FIELD_GUIDE, FOOD_AREA_GUIDE, GUIDES)

KINDS = ('正餐', '點心', '咖啡', '喝一杯', '市集')
DISH_GUIDES = {'ams', 'dh', 'rtm', 'bru', 'bxl', 'kol', 'dus'}
MARKET = '大教堂前＋Heinzels 聖誕市集'

def entries():
    rows = list(FOOD_DIRECTORY)
    for guide in GUIDES:
        for badge, name, order, _rating, feature, query, _date in guide['places']:
            if name in FOOD_CHAPTER_EXTRAS:
                city, area, kind = FOOD_CHAPTER_EXTRAS[name]
                rows.append((city, area, kind, name, badge == '首選', order,
                             FOOD_EXTRA_COPY.get(name, feature), '', query))
    return rows

def card(place, esc, maps):
    kind, name, pick, order, feature, note, query = place
    tip = f'<p class="food-tip"><b>到店前</b> {esc(note)}</p>' if note else ''
    meta = '<span class="food-pick">首選</span>' if pick else ''
    links = ([('大教堂前', 'Weihnachtsmarkt am Kölner Dom'), ('Heinzels', query)]
             if name == MARKET else [('地圖', query)])
    links = ''.join(f'<a href="{esc(maps(q))}" target="_blank" rel="noopener" aria-label="{esc(name)}：{esc(t)} Google Maps">{esc(t)} <span aria-hidden="true">↗</span></a>' for t,q in links)
    return f'''<li class="food-place" data-kind="{esc(kind)}">
  <div class="food-meta">{esc(kind)} {meta}</div>
  <div class="food-card-head"><h4>{esc(name)}</h4><div class="food-maps">{links}</div></div>
  <p class="food-order"><span>可以點</span> <b>{esc(order)}</b></p>
  <p class="food-feature">{esc(feature)}</p>
  {tip}
</li>'''

def city_spread(key, areas, guides, esc, maps, photo):
    city = CITIES[key]
    title, intro, ideas = FOOD_FIELD_GUIDE[key]
    label = esc(city['name'])
    image = photo(key, 'food-city-photo', '(max-width: 620px) 31vw, 420px')
    shortcuts = ''.join(f'<button type="button" data-food-idea="{esc(idea)}">{esc(idea)}</button>' for idea in ideas)
    if set(areas) != FOOD_AREA_GUIDE[key].keys():
        raise ValueError(f'Food map labels and dining groups differ for {key}')
    groups = []
    for i, (area, (short, description)) in enumerate(FOOD_AREA_GUIDE[key].items(), 1):
        places = areas[area]
        lat, lon = AREA_POINTS[(key, area)]
        cards = ''.join(card(p, esc, maps) for p in sorted(places, key=lambda p: not p[2]))
        groups.append(f'''<section class="food-area" data-area="{esc(area)}" data-short="{esc(short)}" data-point="{lat},{lon}">
  <div class="food-area-head"><h3 tabindex="-1"><span class="food-folio" aria-label="街區 {i}">{i:02}</span>{esc(area)}</h3><button type="button" data-back-to-map hidden>回地圖 ↑</button></div>
  <p class="food-area-intro">{esc(description)}</p><ul>{cards}</ul>
</section>''')
    dishes = guides[key]['dishes'] if key in DISH_GUIDES else []
    dish_list = ''.join(f'<li><b>{esc(name)}</b> <i>{esc(original)}</i> — {esc(note)}</li>' for name,original,note in dishes)
    details = (f'''<details class="food-special"><summary>認識當地菜色</summary><ul>{dish_list}</ul>
<a href="index.html#g-{key}">看旅行手冊裡的菜色照片 ↗</a></details>''' if dishes else '')
    return f'''<section class="food-city" id="city-{key}" data-panel="{key}">
  <header class="food-city-lead">
    <div class="food-city-copy">
      <p class="food-local">{esc(city['local'])}</p>
      <h2>{label}</h2>
      <p class="food-lead-line">{esc(title)}</p>
      <p class="food-lead-intro">{esc(intro)}</p>
      <div class="food-ideas" hidden><span>想吃</span>{shortcuts}</div>
    </div>
    {image}
  </header>
  <div class="food-filter-slot"></div>
  <div class="food-spread">
    <aside class="food-map-slot" aria-label="街區導覽" hidden></aside>
    <div class="food-results">
      <header class="food-results-head"><b>店家清單</b><span data-results-context>{label}</span></header>
      <p class="food-empty" hidden>這裡沒有符合的選擇，試試換個街區、餐別或關鍵字。</p>
      {''.join(groups)}
      {details}
    </div>
  </div>
</section>'''

def page(esc, maps, photo):
    cities = {key: defaultdict(list) for key in CITIES}
    for city, area, *rest in entries():
        cities[city][area].append(rest)
    guides = {g['key']: g for g in GUIDES}
    tabs = ''.join(f'<a href="#city-{k}" data-city="{k}">{esc(c["name"])}</a>' for k,c in CITIES.items())
    sections = ''.join(city_spread(k,a,guides,esc,maps,photo) for k,a in cities.items())
    kinds = ''.join(f'<option>{kind}</option>' for kind in KINDS)
    return f'''
<a class="skip-link" href="#food-main">跳到吃喝指南</a>
<header class="food-mast"><div class="wrap">
  <a href="index.html#overview">← 回旅行手冊</a><span>WINTER RAIL JOURNAL</span>
</div></header>
<main class="wrap food-main" id="food-main" tabindex="-1">
  <header class="food-intro"><p class="kicker">Pocket guide / 吃喝</p><h1>這附近吃什麼？</h1>
  <p>從一個街區、一口當地味道開始。</p></header>
  <nav class="food-cities" aria-label="選擇城市">{tabs}</nav>
  <div class="food-filters" hidden>
    <label>找店或菜名<input type="search" placeholder="例如：淡菜、蘋果派" id="food-search" autocomplete="off"></label>
    <label>街區<select id="food-area"><option value="">所有街區</option></select></label>
    <label>餐別<select id="food-kind"><option value="">所有餐別</option>{kinds}</select></label>
    <div class="food-filter-foot"><p id="food-count" role="status"></p><button type="button" data-food-results>直接看清單 ↓</button></div>
  </div>
  <div class="food-map" data-tiles="https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png" hidden>
    <div class="food-map-head"><b>街區地圖</b><button type="button" data-map-toggle aria-expanded="true" aria-controls="food-map-body">收起底圖</button></div>
    <p class="food-map-key">圖上編號對應街區索引；索引右側是符合條件的店家數。</p>
    <div id="food-map-body">
      <div class="food-map-canvas" role="region" aria-label="吃喝街區地圖"></div>
      <p class="food-map-status" role="status"></p>
      <div class="food-map-tools" hidden>
        <button type="button" data-map-reset>回到全城</button>
        <button type="button" data-map-drag aria-pressed="false">移動地圖</button>
      </div>
    </div>
    <div class="food-area-key">
      <div class="food-area-key-head"><b>街區索引</b><button type="button" data-clear-area hidden>看全部街區</button></div>
      <ul class="food-legend" aria-label="從街區選店"></ul>
    </div>
  </div>
  {sections}
</main>
<footer class="wrap food-footer">整理自旅伴的美食清單與手冊選店。菜單、營業時間和訂位方式以店家公告為準。<a href="index.html#photo-credits">照片來源與授權</a></footer>
<script src="src/food-map.js?v=field-guide" defer></script>
<script src="src/food.js?v=field-guide" defer></script>'''
