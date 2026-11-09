/* One map, loaded only when its open panel is near the viewport. */
window.createFoodMap = function (panel, pickArea, showResults) {
  const mapEl = panel.querySelector('.food-map-canvas');
  const status = panel.querySelector('.food-map-status');
  const tools = panel.querySelector('.food-map-tools');
  const clear = panel.querySelector('[data-clear-area]');
  const drag = panel.querySelector('[data-map-drag]');
  const reset = panel.querySelector('[data-map-reset]');
  const tileUrl = panel.dataset.tiles;
  let visible = false, loading, map, markers, mapPopup, openGroup, state, displayedCity, moving = false;
  const mapAssets = 'https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/';
  const integrity = {
    'leaflet.css': 'sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=',
    'leaflet.js': 'sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo='
  };
  function load(name, style) {
    return new Promise((resolve, reject) => {
      const el = document.createElement(style ? 'link' : 'script');
      el.crossOrigin = 'anonymous';
      el.integrity = integrity[name];
      if (style) { el.rel = 'stylesheet'; el.href = mapAssets + name; }
      else el.src = mapAssets + name;
      el.onload = resolve;
      el.onerror = reject;
      document.head.append(el);
    });
  }
  function setDrag(on) {
    moving = on;
    if (on) map.dragging.enable(); else map.dragging.disable();
    drag.setAttribute('aria-pressed', String(on));
    drag.textContent = on ? '完成移動' : '移動地圖';
  }
  function fit() {
    if (!markers.size) return;
    const points = [...markers.values()].map(pin => pin.getLatLng());
    if (points.length === 1) map.setView(points[0], 16, {animate:false});
    else map.fitBounds(points, {maxZoom:16, paddingTopLeft:[58, 34], paddingBottomRight:[24, 34], animate:false});
  }
  function popup(group) {
    const content = document.createElement('div');
    const name = document.createElement('strong');
    name.textContent = group.name;
    const go = document.createElement('button');
    go.type = 'button';
    go.textContent = `看這區 ${group.count} 個選擇 ↓`;
    if (group.count) go.addEventListener('click', () => {
      map.closePopup();
      showResults();
    });
    content.append(name, go);
    if (!group.count) {
      const tip = document.createElement('p');
      tip.textContent = '這區沒有符合的店，可換餐別或關鍵字。';
      content.replaceChild(tip, go);
    }
    return content;
  }
  function draw() {
    if (!map || !visible || !panel.open || !state) return;
    const {city, label, groups, selected} = state;
    const cityChanged = city !== displayedCity;
    if (cityChanged) {
      map.closePopup();
      markers.forEach(pin => pin.remove());
      markers.clear();
      displayedCity = city;
      groups.forEach(group => {
        if (!group.point) return;
        const number = document.createElement('span');
        number.className = 'food-pin-number';
        const icon = L.divIcon({className:'food-pin', html:number, iconSize:[44, 44], iconAnchor:[22, 22]});
        const pin = L.marker(group.point, {icon, title:group.name, keyboard:true, autoPanOnFocus:false});
        pin.addTo(map).on('click', () => {
          pickArea(group.name);
          const current = state.groups.find(item => item.name === group.name);
          mapPopup.setLatLng(pin.getLatLng()).setContent(popup(current)).openOn(map);
          openGroup = {name:current.name, count:current.count};
        });
        markers.set(group.name, pin);
      });
    }
    map.invalidateSize({pan:false});
    if (cityChanged) fit();
    mapEl.setAttribute('aria-label', `${label}的吃喝街區地圖`);
    groups.forEach(group => {
      const pin = markers.get(group.name);
      if (!pin) return;
      const el = pin.getElement();
      el.querySelector('.food-pin-number').textContent = group.count;
      el.classList.toggle('is-selected', group.name === selected);
      el.classList.toggle('is-empty', !group.count);
      el.setAttribute('aria-label', `${group.name}，${group.count} 個選擇`);
      el.setAttribute('aria-pressed', String(group.name === selected));
      pin.setZIndexOffset(group.name === selected ? 1000 : 0);
    });
    if (openGroup && map.hasLayer(mapPopup)) {
      const group = groups.find(item => item.name === openGroup.name);
      if (!group || group.name !== selected) map.closePopup();
      else if (openGroup.count !== group.count) {
        mapPopup.setContent(popup(group));
        openGroup.count = group.count;
      }
    }
  }
  function activate() {
    if (!panel.open || !visible || !state) return;
    if (map) { draw(); return; }
    if (loading) return;
    status.textContent = '正在載入街區地圖…';
    loading = Promise.all([load('leaflet.css', true), load('leaflet.js', false)]).then(() => {
      map = L.map(mapEl, {scrollWheelZoom:false, dragging:false, maxZoom:19, minZoom:10, attributionControl:true});
      markers = new Map();
      mapPopup = L.popup({offset:[0,-13], maxWidth:240});
      map.on('popupclose', () => { openGroup = null; });
      map.attributionControl.setPrefix(false);
      const zoom = map.zoomControl.getContainer();
      zoom.querySelector('.leaflet-control-zoom-in').setAttribute('aria-label', '放大地圖');
      zoom.querySelector('.leaflet-control-zoom-out').setAttribute('aria-label', '縮小地圖');
      const layer = L.tileLayer(tileUrl, {
        maxZoom:19,
        attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      }).addTo(map);
      layer.on('tileerror', () => { status.textContent = '底圖暫時無法載入，仍可點街區或使用清單。'; });
      layer.on('tileload', () => { status.textContent = ''; });
      tools.hidden = false;
      status.textContent = '';
      setDrag(false);
      draw();
    }).catch(error => {
      console.error("Street map initialization failed", error);
      status.textContent = '地圖暫時無法載入，仍可使用街區篩選和店家地圖連結。';
      mapEl.hidden = true;
    });
  }
  panel.addEventListener('toggle', () => {
    if (!panel.open && map) {
      map.closePopup();
      setDrag(false);
    }
    activate();
  });
  reset.addEventListener('click', () => { map.closePopup(); fit(); });
  drag.addEventListener('click', () => setDrag(!moving));
  clear.addEventListener('click', () => {
    pickArea('');
    panel.querySelector('summary').focus({preventScroll:true});
  });
  if ('IntersectionObserver' in window) {
    new IntersectionObserver(([entry]) => {
      visible = entry.isIntersecting;
      activate();
    }, {rootMargin:'100px 0px'}).observe(panel);
  } else visible = true;
  panel.hidden = false;
  return next => {
    state = next;
    panel.querySelector('[data-map-city]').textContent = next.label;
    clear.hidden = !next.selected;
    activate();
  };
};
