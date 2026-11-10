(() => {
  const tabs = [...document.querySelectorAll('[data-city]')];
  const panels = [...document.querySelectorAll('[data-panel]')];
  const filters = document.querySelector('.food-filters');
  const mapPanel = document.querySelector('.food-map');
  const area = document.getElementById('food-area');
  const kind = document.getElementById('food-kind');
  const search = document.getElementById('food-search');
  const count = document.getElementById('food-count');
  let active, groups;
  function showResults() {
    const first = groups.find(group => !group.el.hidden)?.el.querySelector('h3') ||
      active.querySelector('.food-empty');
    first.tabIndex = -1;
    first.focus({preventScroll:true});
    first.scrollIntoView({block:'start'});
  }
  const drawMap = window.createFoodMap?.(mapPanel, name => {
    area.value = name;
    update();
  }, showResults);
  const normalize = s => s.normalize('NFD').replace(/\p{M}/gu, '').toLowerCase().replace(/[’']/g, '');
  function update() {
    const terms = normalize(search.value.trim()).split(/\s+/).filter(Boolean);
    let n = 0;
    groups.forEach(group => {
      let visible = 0;
      group.count = 0;
      group.cards.forEach(card => {
        const matchesFood = (!kind.value || card.el.dataset.kind === kind.value) &&
          terms.every(term => card.text.includes(term));
        if (matchesFood) group.count++;
        const match = matchesFood && (!area.value || group.name === area.value);
        card.el.hidden = !match;
        if (match) visible++;
      });
      group.el.hidden = !visible;
      n += visible;
    });
    const label = active.querySelector('h2').textContent;
    const context = groups.find(group => group.name === area.value)?.short || label;
    count.textContent = `${context} · ${n} 個選擇`;
    active.querySelector('[data-results-context]').textContent = `${context} · ${n}`;
    active.querySelector('.food-empty').hidden = n !== 0;
    drawMap?.({city:active.dataset.panel, label, groups, selected:area.value});
  }
  function select(scroll = false) {
    const panel = panels.find(el => '#' + el.id === location.hash) || panels[0];
    if (active === panel) return;
    active = panel;
    panels.forEach(el => { el.hidden = el !== panel; });
    panel.querySelector('.food-filter-slot').append(filters);
    const mapSlot = panel.querySelector('.food-map-slot');
    mapSlot.append(mapPanel);
    mapSlot.hidden = !drawMap;
    panel.querySelectorAll('[data-back-to-map]').forEach(button => { button.hidden = !drawMap; });
    panel.querySelector('.food-ideas').hidden = false;
    tabs.forEach(tab => {
      if (tab.dataset.city === panel.dataset.panel) {
        tab.setAttribute('aria-current', 'true');
        const rail = tab.parentElement;
        const left = tab.offsetLeft - rail.offsetLeft;
        if (left < rail.scrollLeft || left + tab.offsetWidth > rail.scrollLeft + rail.clientWidth)
          rail.scrollLeft = Math.max(0, left - 22);
      } else tab.removeAttribute('aria-current');
    });
    groups = [...panel.querySelectorAll('[data-area]')].map((el, index) => ({
      el, name:el.dataset.area, short:el.dataset.short, number:String(index + 1).padStart(2,'0'),
      hint:el.querySelector('.food-area-intro').textContent,
      point:el.dataset.point.split(',').map(Number),
      cards:[...el.querySelectorAll('.food-place')].map(card => ({
        el:card, text:normalize(el.dataset.area + ' ' + card.textContent)
      }))
    }));
    area.replaceChildren(new Option('所有街區', ''), ...groups.map(g => new Option(g.short, g.name)));
    search.value = '';
    kind.value = '';
    update();
    if (scroll) panel.scrollIntoView({block:'start', behavior:'instant'});
  }
  filters.hidden = false;
  select();
  if (panels.some(panel => '#' + panel.id === location.hash)) {
    window.addEventListener('load', () => requestAnimationFrame(() => {
      window.scrollTo({top:0, behavior:'instant'});
    }), {once:true});
  }
  tabs.forEach(tab => tab.addEventListener('click', event => {
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    if (tab.hash !== location.hash) history.pushState(null, '', tab.hash);
    select(true);
  }));
  document.querySelectorAll('[data-food-idea]').forEach(button => button.addEventListener('click', () => {
    search.value = button.dataset.foodIdea;
    area.value = '';
    kind.value = '';
    update();
    filters.scrollIntoView({block:'start',behavior:'instant'});
  }));
  document.querySelectorAll('[data-back-to-map]').forEach(button => button.addEventListener('click', () => {
    mapPanel.querySelector('[data-map-toggle]').focus({preventScroll:true});
    mapPanel.scrollIntoView({block:'start'});
  }));
  document.querySelector('[data-food-results]').addEventListener('click', showResults);
  window.addEventListener('popstate', () => select(true));
  window.addEventListener('hashchange', () => select(true));
  search.addEventListener('input', update);
  area.addEventListener('change', update);
  kind.addEventListener('change', update);
})();
