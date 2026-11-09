(() => {
  const tabs = [...document.querySelectorAll('[data-city]')];
  const panels = [...document.querySelectorAll('[data-panel]')];
  const filters = document.querySelector('.food-filters');
  const area = document.getElementById('food-area');
  const kind = document.getElementById('food-kind');
  const search = document.getElementById('food-search');
  const count = document.getElementById('food-count');
  const empty = document.querySelector('.food-empty');
  let active, groups;
  const drawMap = window.createFoodMap?.(document.querySelector('.food-map'), name => {
    area.value = name;
    update();
  }, () => {
    const first = groups.find(group => !group.el.hidden)?.el.querySelector('h3');
    if (first) {
      first.focus({preventScroll:true});
      first.scrollIntoView({block:'start'});
    }
  });
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
    count.textContent = `顯示 ${n} 個選擇`;
    empty.hidden = n !== 0;
    drawMap?.({city:active.dataset.panel, label:active.querySelector('h2').textContent,
      groups, selected:area.value});
  }
  function select(scroll = false) {
    const panel = panels.find(el => '#' + el.id === location.hash) || panels[0];
    if (active === panel) return;
    active = panel;
    panels.forEach(el => { el.hidden = el !== panel; });
    tabs.forEach(tab => {
      if (tab.dataset.city === panel.dataset.panel) {
        tab.setAttribute('aria-current', 'true');
        const rail = tab.parentElement;
        const left = tab.offsetLeft - rail.offsetLeft;
        if (left < rail.scrollLeft || left + tab.offsetWidth > rail.scrollLeft + rail.clientWidth)
          rail.scrollLeft = left - 16;
      } else tab.removeAttribute('aria-current');
    });
    groups = [...panel.querySelectorAll('[data-area]')].map(el => ({
      el, name: el.dataset.area,
      point: el.dataset.point?.split(',').map(Number),
      cards: [...el.querySelectorAll('.food-place')].map(card => ({
        el: card, text: normalize(el.dataset.area + ' ' + card.textContent)
      }))
    }));
    area.replaceChildren(new Option('所有街區', ''), ...groups.map(g => new Option(g.name, g.name)));
    search.value = '';
    kind.value = '';
    update();
    if (scroll && window.scrollY > filters.offsetTop)
      filters.scrollIntoView({block: 'start', behavior: 'instant'});
  }
  filters.hidden = false;
  select();
  if (panels.some(panel => '#' + panel.id === location.hash)) {
    window.addEventListener('load', () => requestAnimationFrame(() => {
      window.scrollTo({top: 0, behavior: 'instant'});
    }), {once: true});
  }
  // Keep city links shareable and native when JavaScript is unavailable.
  tabs.forEach(tab => tab.addEventListener('click', event => {
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    if (tab.hash !== location.hash) history.pushState(null, '', tab.hash);
    select(true);
  }));
  window.addEventListener('popstate', () => select(true));
  window.addEventListener('hashchange', () => select(true));
  search.addEventListener('input', update);
  area.addEventListener('change', update);
  kind.addEventListener('change', update);
})();
