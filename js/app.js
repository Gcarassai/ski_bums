/* Alpine Ski Resorts 2026/27 — application code. Vanilla JS, no dependencies. */
(() => {
  'use strict';

  // ---------- Constants ----------
  const COUNTRIES = [
    { code: 'FR', name: 'France' }, { code: 'IT', name: 'Italy' }, { code: 'AT', name: 'Austria' },
    { code: 'CH', name: 'Switzerland' }, { code: 'DE', name: 'Germany' }, { code: 'SI', name: 'Slovenia' },
  ];
  const COUNTRY_ORDER = Object.fromEntries(COUNTRIES.map((c, i) => [c.code, i]));
  const COUNTRY_NAME = Object.fromEntries(COUNTRIES.map((c) => [c.code, c.name]));
  const TYPES = [
    { value: 'Glacier', short: 'Glacier', cls: 'glacier' },
    { value: 'Glacier + non-glacier', short: 'Mixed', cls: 'mixed' },
    { value: 'Non-glacier', short: 'Non-glacier', cls: 'nonglacier' },
  ];
  const TYPE_BY_VALUE = Object.fromEntries(TYPES.map((t) => [t.value, t]));
  const TYPE_ORDER = Object.fromEntries(TYPES.map((t, i) => [t.value, i]));
  const CONF_ORDER = { high: 3, medium: 2, low: 1 };
  const DATE_STATUS_LABEL = {
    confirmed_2026_27: 'Confirmed for 2026/27',
    estimated_from_2025_26: 'Estimated from the 2025/26 season',
    year_round_glacier: 'Year-round glacier skiing',
    TBD: 'Opening date to be determined',
  };
  const PRICE_STATUS_LABEL = {
    published_2026_27: 'Published 2026/27 tariff',
    estimated_from_2025_26: 'Estimated from 2025/26 prices',
  };
  const WEATHER_SOURCES = [
    [/meteoswiss|meteoschweiz|meteosuisse|meteosvizzera/i, 'MeteoSwiss'],
    [/meteofrance/i, 'Météo-France'],
    [/geosphere|zamg/i, 'GeoSphere Austria'],
    [/(^|\.)dwd\.de/i, 'DWD'],
    [/arso\.gov\.si/i, 'ARSO'],
    [/meteotrentino/i, 'Meteotrentino'],
    [/provinc(ia|z|e)\.bz\.it/i, 'Provincia di Bolzano'],
    [/arpa\.piemonte/i, 'ARPA Piemonte'],
    [/arpalombardia/i, 'ARPA Lombardia'],
    [/arpa\.veneto/i, 'ARPAV'],
    [/regione\.vda/i, 'Centro Funzionale VdA'],
  ];
  const AVALANCHE_SOURCES = [
    [/slf\.ch|whiterisk/i, 'SLF'],
    [/meteofrance/i, 'Météo-France'],
    [/avalanche\.report|lawinen\.report|lawine\.report/i, 'avalanche.report'],
    [/lawinen-warnung\.eu/i, 'Lawinenwarndienste Österreich'],
    [/lawine\.salzburg/i, 'LWD Salzburg'],
    [/vorarlberg/i, 'LWD Vorarlberg'],
    [/ktn\.gv\.at|kaernten/i, 'LWD Kärnten'],
    [/steiermark/i, 'LWD Steiermark'],
    [/bayern/i, 'LWD Bayern'],
    [/aineva/i, 'AINEVA'],
    [/arso/i, 'ARSO'],
    [/regione\.vda/i, 'Regione VdA'],
    [/arpa\.piemonte/i, 'ARPA Piemonte'],
    [/arpalombardia/i, 'ARPA Lombardia'],
    [/arpa\.veneto/i, 'ARPAV'],
    [/meteotrentino/i, 'Meteotrentino'],
  ];
  // Table columns. `dir` is the direction of the first click; `num` right-aligns.
  const COLUMNS = [
    { key: 'resort', label: 'Resort', dir: 'asc', fixed: true },
    { key: 'country', label: 'Country', dir: 'asc' },
    { key: 'type', label: 'Type', dir: 'asc' },
    { key: 'opens', label: 'Opens', dir: 'asc' },
    { key: 'top', label: 'Top', dir: 'desc', num: true },
    { key: 'pistes', label: 'Pistes', dir: 'desc', num: true },
    { key: 'price', label: 'Day pass', dir: 'asc', num: true },
    { key: 'milan', label: 'From Milan', dir: 'asc', num: true },
    { key: 'freeride', label: 'Freeride', dir: 'desc' },
    { key: 'touring', label: 'Touring', dir: 'desc' },
    { key: 'links', label: 'Links', sortable: false },
    { key: 'confidence', label: 'Confidence', short: 'Conf.', dir: 'desc' },
  ];
  const MAX_HOURS = 8;
  const DEFAULT_SORT = { key: 'opens', dir: 'asc' };

  // ---------- Formatting helpers ----------
  const fmtInt = new Intl.NumberFormat('en-GB');
  const fmtShortDate = new Intl.DateTimeFormat('en-GB', { weekday: 'short', day: 'numeric', month: 'short', timeZone: 'UTC' });
  const fmtLongDate = new Intl.DateTimeFormat('en-GB', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' });
  const fmtDateNoWeekday = new Intl.DateTimeFormat('en-GB', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' });

  const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const isNum = (v) => typeof v === 'number' && Number.isFinite(v);
  const norm = (s) => String(s ?? '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  const parseISO = (iso) => { const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso || ''); return m ? new Date(Date.UTC(+m[1], +m[2] - 1, +m[3])) : null; };
  const icon = (id, cls = 'ic') => `<svg class="${cls}" aria-hidden="true" focusable="false"><use href="#${id}"/></svg>`;
  const flag = (code) => `<svg class="flag" aria-hidden="true" focusable="false"><use href="#flag-${esc(code)}"/></svg>`;

  function fmtHours(h) {
    if (!isNum(h)) return '—';
    const mins = Math.round(h * 60);
    return `${Math.floor(mins / 60)} h ${String(mins % 60).padStart(2, '0')}`;
  }
  function fmtMoney(a, b) {
    const dec = !Number.isInteger(a) || !Number.isInteger(b);
    const f = (v) => (dec ? v.toFixed(2) : String(v));
    return a === b ? f(a) : `${f(a)}–${f(b)}`;
  }
  function fmtPrice(r) {
    if (!isNum(r.ticket_price_min)) return null;
    const a = r.ticket_price_min, b = isNum(r.ticket_price_max) ? r.ticket_price_max : a;
    const range = fmtMoney(Math.min(a, b), Math.max(a, b));
    return r.currency === 'CHF' ? `CHF ${range}` : `€${range}`;
  }
  function fmtScore(v) { return isNum(v) ? v.toFixed(1) : '–'; }
  function sourceName(url, table) {
    let host = '';
    try { host = new URL(url).hostname.replace(/^www\./, ''); } catch { return 'source'; }
    for (const [re, name] of table) if (re.test(host)) return name;
    return host;
  }
  function domainOf(url) { try { return new URL(url).hostname.replace(/^www\./, ''); } catch { return url; } }
  function slugify(s) { return norm(s).replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '') || 'resort'; }

  // ---------- State ----------
  const allCountries = () => new Set(COUNTRIES.map((c) => c.code));
  const allTypes = () => new Set(TYPES.map((t) => t.value));
  const state = {
    q: '', countries: allCountries(), types: allTypes(), by: '', hours: MAX_HOURS, fr: 0, to: 0, hideLow: false,
    sort: { ...DEFAULT_SORT }, resort: null,
  };
  let DATA = [];
  let META = { generated_at: '', row_count: 0, sample: false, season: '2026/27' };
  let BY_SLUG = new Map();
  let visibleRows = [];
  let colPrefs = {};
  try { colPrefs = JSON.parse(localStorage.getItem('cols') || '{}') || {}; } catch { colPrefs = {}; }

  const $ = (id) => document.getElementById(id);
  const el = {
    header: $('site-header'), subtitle: $('subtitle'), search: $('search'), searchClear: $('search-clear'), searchToggle: $('search-toggle'),
    searchForm: $('search-form'), theme: $('theme-toggle'), banner: $('sample-banner'),
    filtersDialog: $('filters-dialog'), filters: $('filters'), filtersOpen: $('filters-open'), filtersClose: $('filters-close'), filtersDone: $('filters-done'),
    filterBadge: $('filter-badge'), countryChips: $('country-chips'), typeChips: $('type-chips'), openBy: $('f-openby'), openByClear: $('openby-clear'),
    openByNote: $('openby-note'), hours: $('f-hours'), hoursOut: $('hours-out'), fr: $('f-fr'), frOut: $('fr-out'), to: $('f-to'), toOut: $('to-out'),
    hideLow: $('f-hidelow'), reset: $('reset'), resetTop: $('reset-top'), emptyReset: $('empty-reset'), count: $('count'), countCopy: $('count-copy'),
    mobileSort: $('mobile-sort'), copyLink: $('copy-link'), colMenu: $('col-menu'), colBody: $('col-body'),
    results: $('results'), empty: $('empty'), loadError: $('load-error'), footerData: $('footer-data'), footerSeason: $('footer-season'),
    detail: $('detail'), detailInner: $('detail-inner'), toast: $('toast'),
  };
  const mqDesktop = window.matchMedia('(min-width: 768px)');
  const isDesktop = () => mqDesktop.matches;

  // ---------- URL state ----------
  function stateToParams() {
    const p = new URLSearchParams();
    if (state.q) p.set('q', state.q);
    if (state.countries.size !== COUNTRIES.length) p.set('c', COUNTRIES.map((c) => c.code).filter((c) => state.countries.has(c)).join(',') || '-');
    if (state.types.size !== TYPES.length) p.set('t', TYPES.map((t) => t.cls).filter((t) => state.types.has(TYPES.find((x) => x.cls === t).value)).join(',') || '-');
    if (state.by) p.set('by', state.by);
    if (state.hours < MAX_HOURS) p.set('h', String(state.hours));
    if (state.fr > 0) p.set('fr', String(state.fr));
    if (state.to > 0) p.set('to', String(state.to));
    if (state.hideLow) p.set('hl', '1');
    if (state.sort.key !== DEFAULT_SORT.key || state.sort.dir !== DEFAULT_SORT.dir) { p.set('sort', state.sort.key); p.set('dir', state.sort.dir); }
    if (state.resort) p.set('resort', state.resort);
    return p;
  }
  function urlFor(params) { const s = params.toString(); return location.pathname + (s ? '?' + s : '') ; }
  function syncURL(method = 'replaceState') {
    const url = urlFor(stateToParams());
    if (url !== location.pathname + location.search) history[method](null, '', url);
  }
  function readURL() {
    const p = new URLSearchParams(location.search);
    state.q = p.get('q') || '';
    if (p.has('c')) { const v = p.get('c'); state.countries = new Set(v === '-' ? [] : v.split(',').filter((c) => COUNTRY_ORDER[c] !== undefined)); }
    else state.countries = allCountries();
    if (p.has('t')) { const v = p.get('t'); state.types = new Set(v === '-' ? [] : v.split(',').map((cls) => TYPES.find((t) => t.cls === cls)).filter(Boolean).map((t) => t.value)); }
    else state.types = allTypes();
    state.by = /^\d{4}-\d{2}-\d{2}$/.test(p.get('by') || '') ? p.get('by') : '';
    const h = parseFloat(p.get('h')); state.hours = isNum(h) ? Math.min(MAX_HOURS, Math.max(1, Math.round(h * 4) / 4)) : MAX_HOURS;
    const fr = parseFloat(p.get('fr')); state.fr = isNum(fr) ? Math.min(5, Math.max(0, Math.round(fr * 2) / 2)) : 0;
    const to = parseFloat(p.get('to')); state.to = isNum(to) ? Math.min(5, Math.max(0, Math.round(to * 2) / 2)) : 0;
    state.hideLow = p.get('hl') === '1';
    const sk = p.get('sort'), sd = p.get('dir');
    const col = COLUMNS.find((c) => c.key === sk && c.sortable !== false);
    state.sort = col ? { key: col.key, dir: sd === 'desc' ? 'desc' : 'asc' } : { ...DEFAULT_SORT };
    state.resort = p.get('resort') || null;
  }

  // ---------- Data preparation ----------
  function prepare(rows) {
    const slugs = new Map();
    for (const r of rows) {
      const d = parseISO(r.opening_date_2026_27);
      r._date = d;
      r._iso = d ? r.opening_date_2026_27 : null;
      // Sort key: real dates first (by date), then year-round, then TBD/unknown.
      r._dateKey = r.opening_date_status === 'year_round_glacier' ? '1' + (r._iso || '') : (r._iso ? '0' + r._iso : '2');
      r._hay = norm([r.resort_name, r.local_name, r.ski_area, r.region, COUNTRY_NAME[r.country]].filter(Boolean).join(' '));
      let slug = slugify(r.resort_name);
      if (slugs.has(slug)) slug = `${slug}-${String(r.country || '').toLowerCase()}`;
      let n = 2; const base = slug;
      while (slugs.has(slug)) slug = `${base}-${n++}`;
      slugs.set(slug, r); r._slug = slug;
    }
    BY_SLUG = slugs;
    return rows;
  }

  // ---------- Filtering & sorting ----------
  function matches(r, skipCountry = false) {
    if (!skipCountry && !state.countries.has(r.country)) return false;
    if (!state.types.has(r.type)) return false;
    if (state.by) {
      if (r.opening_date_status === 'year_round_glacier') { /* always open */ }
      else if (!r._iso || r.opening_date_status === 'TBD') return false;
      else if (r._iso > state.by) return false;
    }
    if (state.hours < MAX_HOURS && !(isNum(r.driving_time_h_from_milan) && r.driving_time_h_from_milan <= state.hours)) return false;
    if (state.fr > 0 && !(isNum(r.freeride_score_0_5) && r.freeride_score_0_5 >= state.fr)) return false;
    if (state.to > 0 && !(isNum(r.ski_touring_score_0_5) && r.ski_touring_score_0_5 >= state.to)) return false;
    if (state.hideLow && r.confidence === 'low') return false;
    if (state._words.length && !state._words.every((w) => r._hay.includes(w))) return false;
    return true;
  }
  function sortKey(r, key) {
    switch (key) {
      case 'resort': return norm(r.resort_name);
      case 'country': return COUNTRY_ORDER[r.country] ?? 99;
      case 'type': return TYPE_ORDER[r.type] ?? 99;
      case 'opens': return r._dateKey;
      case 'top': return isNum(r.max_elevation_m) ? r.max_elevation_m : null;
      case 'pistes': return isNum(r.piste_km) ? r.piste_km : null;
      case 'price': return isNum(r.ticket_price_min) ? r.ticket_price_min : null;
      case 'milan': return isNum(r.driving_time_h_from_milan) ? r.driving_time_h_from_milan : null;
      case 'freeride': return isNum(r.freeride_score_0_5) ? r.freeride_score_0_5 : null;
      case 'touring': return isNum(r.ski_touring_score_0_5) ? r.ski_touring_score_0_5 : null;
      case 'confidence': return CONF_ORDER[r.confidence] ?? null;
      default: return null;
    }
  }
  function sortRows(rows) {
    const { key, dir } = state.sort; const sign = dir === 'desc' ? -1 : 1;
    const byName = (a, b) => norm(a.resort_name).localeCompare(norm(b.resort_name));
    return rows.slice().sort((a, b) => {
      const ka = sortKey(a, key), kb = sortKey(b, key);
      if (ka === null && kb === null) return byName(a, b);
      if (ka === null) return 1; // unknown values always last
      if (kb === null) return -1;
      const c = typeof ka === 'string' ? ka.localeCompare(kb) : ka - kb;
      return c ? c * sign : byName(a, b);
    });
  }

  // ---------- Rendering: cells ----------
  function opensCell(r, long = false) {
    const st = r.opening_date_status;
    if (st === 'year_round_glacier') {
      const when = r._date ? ` · winter season from ${fmtDateNoWeekday.format(r._date)}` : '';
      return `<span class="yr" title="Year-round glacier skiing${esc(when)}">${icon('i-snow')}Year-round</span>`;
    }
    if (!r._date || st === 'TBD') return `<span class="tbd" title="Opening date to be determined">TBD</span>`;
    const short = fmtShortDate.format(r._date), full = fmtLongDate.format(r._date);
    if (st === 'estimated_from_2025_26') return `<time class="est" datetime="${esc(r._iso)}" title="Estimated from 2025/26 season · ${esc(full)}">${esc(long ? full : short)}</time>`;
    return `<time datetime="${esc(r._iso)}" title="${esc(full)}">${esc(long ? full : short)}</time>`;
  }
  function priceCell(r) {
    const p = fmtPrice(r);
    if (!p) return `<span class="dash" aria-label="price unknown">—</span>`;
    if (r.price_status === 'estimated_from_2025_26') return `<span class="est" title="Estimated from 2025/26 season">${esc(p)}</span>`;
    return `<span title="${esc(PRICE_STATUS_LABEL[r.price_status] || '')}">${esc(p)}</span>`;
  }
  function scoreCell(v, label, notes) {
    let segs = '';
    for (let i = 0; i < 5; i++) segs += `<i style="--f:${Math.max(0, Math.min(1, (isNum(v) ? v : 0) - i))}"></i>`;
    const aria = `${label} ${isNum(v) ? v.toFixed(1) : 'unknown'} out of 5`;
    return `<span class="score" role="img" aria-label="${esc(aria)}" title="${esc(notes || aria)}"><span class="bar">${segs}</span><span class="num">${fmtScore(v)}</span></span>`;
  }
  function confCell(r) {
    const c = r.confidence || 'unknown';
    const shape = c === 'high' ? '<circle cx="7" cy="7" r="6"/>' : c === 'medium' ? '<path d="M7 1l6 6-6 6-6-6z"/>' : '<circle cx="7" cy="7" r="5.5" fill="none" stroke="currentColor" stroke-width="1.6"/>';
    return `<span class="conf conf-${esc(c)}" title="Confidence: ${esc(c)}"><svg viewBox="0 0 14 14" fill="currentColor" aria-hidden="true">${shape}</svg><span class="sr-only">${esc(c)}</span></span>`;
  }
  function typeBadge(r) {
    const t = TYPE_BY_VALUE[r.type];
    return t ? `<span class="badge ${t.cls}" title="${esc(r.type)}">${esc(t.short)}</span>` : `<span class="badge nonglacier">${esc(r.type || 'unknown')}</span>`;
  }
  function linkButtons(r, big) {
    const name = r.resort_name; const out = [];
    const add = (href, ic, aria, tip, label, sub) => {
      if (big) out.push(`<a class="biglink" href="${esc(href)}" target="_blank" rel="noopener noreferrer" aria-label="${esc(aria)}">${icon(ic)}<span>${esc(label)}${sub ? `<small>${esc(sub)}</small>` : ''}</span></a>`);
      else out.push(`<a class="lnk" href="${esc(href)}" target="_blank" rel="noopener noreferrer" aria-label="${esc(aria)}" title="${esc(tip)}">${icon(ic)}</a>`);
    };
    if (isNum(r.latitude) && isNum(r.longitude)) {
      const q = `${r.latitude},${r.longitude}`;
      add(`https://www.google.com/maps/search/?api=1&query=${q}`, 'i-map', `Map of ${name} (main base lift)`, 'Google Maps', 'Open in Google Maps', 'Pin on the main base lift');
      const rh = r.road_head ? ` · to road head: ${r.road_head}` : '';
      add(`https://www.google.com/maps/dir/?api=1&origin=Piazza+del+Duomo,+Milano&destination=${q}&travelmode=driving`, 'i-dir',
        `Driving directions from Milan to ${name}${r.road_head ? ` (road head ${r.road_head})` : ''}`, `Directions from Milan${rh}`, 'Directions from Milan', r.road_head ? `To road head: ${r.road_head}` : 'By car from Piazza del Duomo');
    }
    if (r.weather_url) { const s = sourceName(r.weather_url, WEATHER_SOURCES); add(r.weather_url, 'i-weather', `Weather forecast for ${name} (${s})`, `Weather: ${s}`, 'Weather', s); }
    if (r.avalanche_url) { const s = sourceName(r.avalanche_url, AVALANCHE_SOURCES); add(r.avalanche_url, 'i-avalanche', `Avalanche bulletin for ${name} (${s})`, `Avalanche bulletin: ${s}`, 'Avalanche bulletin', s); }
    if (r.webcam_url) add(r.webcam_url, 'i-webcam', `Webcam for ${name}`, `Webcam: ${domainOf(r.webcam_url)}`, 'Webcam', domainOf(r.webcam_url));
    return out.join('');
  }
  function detailHref(slug) { const p = stateToParams(); p.set('resort', slug); return urlFor(p); }

  // ---------- Rendering: table ----------
  function colVisible(key) { return colPrefs[key] !== false; }
  function tableHTML(rows) {
    const { key: sk, dir: sd } = state.sort;
    const ths = COLUMNS.filter((c) => colVisible(c.key)).map((c) => {
      const cls = `col-${c.key}${c.num ? ' num' : ''}`;
      if (c.sortable === false) return `<th scope="col" class="${cls}">${esc(c.label)}</th>`;
      const active = c.key === sk;
      const aria = active ? ` aria-sort="${sd === 'asc' ? 'ascending' : 'descending'}"` : '';
      const ic = active ? (sd === 'asc' ? 'i-up' : 'i-down') : 'i-down';
      const text = c.short ? `<abbr title="${esc(c.label)}">${esc(c.short)}</abbr>` : esc(c.label);
      return `<th scope="col" class="${cls}"${aria}><button type="button" class="sort-btn" data-sort="${c.key}" aria-label="Sort by ${esc(c.label)}${active ? (sd === 'asc' ? ', currently ascending' : ', currently descending') : ''}">${text}${icon(ic)}</button></th>`;
    }).join('');
    const trs = rows.map((r) => {
      const cells = [];
      const v = (k) => colVisible(k);
      if (v('resort')) {
        const local = r.local_name && norm(r.local_name) !== norm(r.resort_name) ? `<span class="sub">${esc(r.local_name)}</span>` : '';
        const area = r.ski_area && norm(r.ski_area) !== norm(r.resort_name) && norm(r.ski_area) !== norm(r.local_name || '') ? `<span class="sub">${esc(r.ski_area)}</span>` : '';
        cells.push(`<td class="col-resort"><svg class="flag inline-flag" aria-hidden="true" focusable="false"><use href="#flag-${esc(r.country)}"/></svg><a class="name-link" href="${esc(detailHref(r._slug))}" data-open="${esc(r._slug)}">${esc(r.resort_name)}</a>${local}${area}</td>`);
      }
      if (v('country')) cells.push(`<td class="col-country"><span class="country-cell" title="${esc(COUNTRY_NAME[r.country] || r.country)}">${flag(r.country)}<span>${esc(r.country)}</span></span></td>`);
      if (v('type')) cells.push(`<td class="col-type">${typeBadge(r)}</td>`);
      if (v('opens')) cells.push(`<td class="col-opens nowrap">${opensCell(r)}</td>`);
      if (v('top')) cells.push(`<td class="col-top num">${isNum(r.max_elevation_m) ? esc(fmtInt.format(r.max_elevation_m)) + ' m' : '<span class="dash">—</span>'}</td>`);
      if (v('pistes')) cells.push(`<td class="col-pistes num">${isNum(r.piste_km) ? esc(fmtInt.format(r.piste_km)) + ' km' : '<span class="dash">—</span>'}</td>`);
      if (v('price')) cells.push(`<td class="col-price num nowrap">${priceCell(r)}</td>`);
      if (v('milan')) cells.push(`<td class="col-milan num nowrap">${isNum(r.driving_distance_km_from_milan) ? esc(fmtInt.format(r.driving_distance_km_from_milan)) + ' km · ' : ''}${esc(fmtHours(r.driving_time_h_from_milan))}</td>`);
      if (v('freeride')) cells.push(`<td class="col-freeride">${scoreCell(r.freeride_score_0_5, 'Freeride', r.score_notes)}</td>`);
      if (v('touring')) cells.push(`<td class="col-touring">${scoreCell(r.ski_touring_score_0_5, 'Ski touring', r.score_notes)}</td>`);
      if (v('links')) cells.push(`<td class="col-links"><span class="links">${linkButtons(r, false)}</span></td>`);
      if (v('confidence')) cells.push(`<td class="col-confidence">${confCell(r)}</td>`);
      return `<tr>${cells.join('')}</tr>`;
    }).join('');
    const force = COLUMNS.filter((c) => colPrefs[c.key] === true).map((c) => ` data-force-${c.key}=""`).join('');
    return `<table class="grid"${force}><caption class="sr-only">Alpine ski resorts, ${rows.length} of ${DATA.length} shown</caption><thead><tr>${ths}</tr></thead><tbody>${trs}</tbody></table>`;
  }

  // ---------- Rendering: cards ----------
  function cardsHTML(rows) {
    const items = rows.map((r) => `
      <li class="card">
        <a class="card-main" href="${esc(detailHref(r._slug))}" data-open="${esc(r._slug)}" aria-label="${esc(r.resort_name)}, open details">
          <div class="l1">${flag(r.country)}<strong>${esc(r.resort_name)}</strong>${typeBadge(r)}</div>
          <div class="l2">${opensCell(r)}<span aria-hidden="true">·</span><span class="nowrap">${esc(fmtHours(r.driving_time_h_from_milan))} from Milan</span></div>
          <div class="l3">
            <span class="score" role="img" aria-label="Freeride ${esc(fmtScore(r.freeride_score_0_5))} out of 5"><span class="lab">Freeride</span>${bar5(r.freeride_score_0_5)}<span class="num">${fmtScore(r.freeride_score_0_5)}</span></span>
            <span class="score" role="img" aria-label="Ski touring ${esc(fmtScore(r.ski_touring_score_0_5))} out of 5"><span class="lab">Touring</span>${bar5(r.ski_touring_score_0_5)}<span class="num">${fmtScore(r.ski_touring_score_0_5)}</span></span>
          </div>
        </a>
        <div class="card-links">${linkButtons(r, false)}</div>
      </li>`).join('');
    return `<ul class="cards" aria-label="Resorts">${items}</ul>`;
  }
  function bar5(v) { let s = '<span class="bar">'; for (let i = 0; i < 5; i++) s += `<i style="--f:${Math.max(0, Math.min(1, (isNum(v) ? v : 0) - i))}"></i>`; return s + '</span>'; }

  // ---------- Rendering: detail ----------
  function detailHTML(r) {
    const local = r.local_name && norm(r.local_name) !== norm(r.resort_name) ? esc(r.local_name) : '';
    const metaBits = [local, esc(r.region), r.ski_area && norm(r.ski_area) !== norm(r.resort_name) ? esc(r.ski_area) : ''].filter(Boolean).join(' · ');
    const price = fmtPrice(r);
    const scoreBar = (label, v) => `<div class="bigscore"><span>${label}</span><span class="track" aria-hidden="true"><span class="fill" style="width:${isNum(v) ? (v / 5) * 100 : 0}%"></span></span><span class="val" aria-label="${label} ${esc(fmtScore(v))} out of 5">${fmtScore(v)}</span></div>`;
    const sources = String(r.sources || '').split('|').map((s) => s.trim()).filter((s) => /^https?:\/\//.test(s));
    return `
      <div class="detail-head">
        ${flag(r.country)}
        <div>
          <h2 id="detail-title" tabindex="-1">${esc(r.resort_name)}</h2>
          <p class="meta">${metaBits}</p>
          <div class="badges">${typeBadge(r)}<span class="badge conf-${esc(r.confidence)}">Confidence: ${esc(r.confidence || 'unknown')}</span></div>
        </div>
        <button type="button" class="icon-btn close" id="detail-close" aria-label="Close details">${icon('i-x')}</button>
      </div>
      <dl class="facts">
        <div><dt>Opens</dt><dd>${opensCell(r, true)}<span class="status">${esc(DATE_STATUS_LABEL[r.opening_date_status] || 'Status unknown')}</span></dd></div>
        <div><dt>Top elevation</dt><dd>${isNum(r.max_elevation_m) ? esc(fmtInt.format(r.max_elevation_m)) + ' m' : '—'}</dd></div>
        <div><dt>Pistes</dt><dd>${isNum(r.piste_km) ? esc(fmtInt.format(r.piste_km)) + ' km' : '—'}</dd></div>
        <div><dt>Day pass</dt><dd>${price ? (r.price_status === 'estimated_from_2025_26' ? `<span class="est">${esc(price)}</span>` : esc(price)) : '—'}<span class="status">${esc(price ? (PRICE_STATUS_LABEL[r.price_status] || '') : 'Price not published')}</span></dd></div>
        <div class="${r.road_head ? '' : 'wide'}"><dt>From Milan</dt><dd>${isNum(r.driving_distance_km_from_milan) ? esc(fmtInt.format(r.driving_distance_km_from_milan)) + ' km · ' : ''}${esc(fmtHours(r.driving_time_h_from_milan))}<span class="status">By car from Piazza del Duomo, free-flow estimate</span></dd></div>
        ${r.road_head ? `<div><dt>Road head</dt><dd>${esc(r.road_head)}<span class="status">Car-free resort. Drive to ${esc(r.road_head)}, then continue by train, cable car or shuttle.</span></dd></div>` : ''}
      </dl>
      <h3>Scores</h3>
      ${scoreBar('Freeride', r.freeride_score_0_5)}
      ${scoreBar('Ski touring', r.ski_touring_score_0_5)}
      ${r.score_notes ? `<p class="notes">${esc(r.score_notes)}</p>` : ''}
      <h3>Links</h3>
      <div class="biglinks">${linkButtons(r, true) || '<p class="muted">No links available.</p>'}</div>
      ${r.comments ? `<h3>Comments</h3><p class="comments">${esc(r.comments)}</p>` : ''}
      ${sources.length ? `<h3>Sources</h3><ul class="sources">${sources.map((s) => `<li><a href="${esc(s)}" target="_blank" rel="noopener noreferrer">${esc(domainOf(s))}</a></li>`).join('')}</ul>` : ''}
      <p class="detail-foot">Data confidence: ${esc(r.confidence || 'unknown')} · Last updated ${esc(META.generated_at || '—')}</p>`;
  }

  // ---------- Main render ----------
  let renderQueued = false;
  function scheduleRender() { if (renderQueued) return; renderQueued = true; requestAnimationFrame(() => { renderQueued = false; render(); }); }
  function render() {
    state._words = norm(state.q).split(/\s+/).filter(Boolean);
    const filtered = DATA.filter((r) => matches(r));
    visibleRows = sortRows(filtered);
    el.results.innerHTML = visibleRows.length ? (isDesktop() ? tableHTML(visibleRows) : cardsHTML(visibleRows)) : '';
    el.results.setAttribute('aria-busy', 'false');
    el.empty.hidden = visibleRows.length > 0 || DATA.length === 0;
    const txt = `Showing ${fmtInt.format(visibleRows.length)} of ${fmtInt.format(DATA.length)} resorts`;
    el.count.textContent = txt; el.countCopy.textContent = txt;
    // Per-country counts given every other filter.
    const counts = {}; for (const r of DATA) if (matches(r, true)) counts[r.country] = (counts[r.country] || 0) + 1;
    el.countryChips.querySelectorAll('.cnt').forEach((span) => { span.textContent = counts[span.dataset.c] || 0; });
    const active = activeFilterCount();
    el.filterBadge.hidden = active === 0; el.filterBadge.textContent = String(active);
    el.filterBadge.setAttribute('aria-label', `${active} active`);
    const sortVal = `${state.sort.key}:${state.sort.dir}`;
    if ([...el.mobileSort.options].some((o) => o.value === sortVal)) el.mobileSort.value = sortVal;
    else { let o = el.mobileSort.querySelector('option[data-custom]'); if (!o) { o = document.createElement('option'); o.dataset.custom = '1'; el.mobileSort.appendChild(o); } o.value = sortVal; o.textContent = `Sorted by ${COLUMNS.find((c) => c.key === state.sort.key)?.label || state.sort.key}`; el.mobileSort.value = sortVal; }
    syncURL();
  }
  function activeFilterCount() {
    let n = 0;
    if (state.countries.size !== COUNTRIES.length) n++;
    if (state.types.size !== TYPES.length) n++;
    if (state.by) n++;
    if (state.hours < MAX_HOURS) n++;
    if (state.fr > 0) n++;
    if (state.to > 0) n++;
    if (state.hideLow) n++;
    return n;
  }

  // ---------- Controls <-> state ----------
  function buildChips() {
    el.countryChips.innerHTML = COUNTRIES.map((c) => `<label class="chip"><input type="checkbox" name="c" value="${c.code}" checked><span class="tick">${icon('i-check', 'tick')}</span>${flag(c.code)}<span>${c.code}</span><span class="sr-only">${esc(c.name)}</span><span class="cnt" data-c="${c.code}" aria-hidden="true"></span></label>`).join('');
    el.typeChips.innerHTML = TYPES.map((t) => `<label class="chip"><input type="checkbox" name="t" value="${esc(t.value)}" checked><span class="tick">${icon('i-check', 'tick')}</span><span>${esc(t.value)}</span></label>`).join('');
  }
  function controlsFromState() {
    el.search.value = state.q; el.searchClear.hidden = !state.q;
    el.countryChips.querySelectorAll('input').forEach((i) => { i.checked = state.countries.has(i.value); });
    el.typeChips.querySelectorAll('input').forEach((i) => { i.checked = state.types.has(i.value); });
    el.openBy.value = state.by; el.openByNote.hidden = !state.by; el.openByClear.hidden = !state.by;
    el.hours.value = String(state.hours); updateHoursOut();
    el.fr.value = String(state.fr); el.frOut.textContent = state.fr ? state.fr.toFixed(1) : '0';
    el.to.value = String(state.to); el.toOut.textContent = state.to ? state.to.toFixed(1) : '0';
    el.hideLow.checked = state.hideLow;
  }
  function updateHoursOut() {
    const v = parseFloat(el.hours.value);
    const txt = v >= MAX_HOURS ? 'No limit' : `≤ ${fmtHours(v)}`;
    el.hoursOut.textContent = txt; el.hours.setAttribute('aria-valuetext', txt);
  }
  function resetAll() {
    state.q = ''; state.countries = allCountries(); state.types = allTypes(); state.by = ''; state.hours = MAX_HOURS; state.fr = 0; state.to = 0; state.hideLow = false;
    state.sort = { ...DEFAULT_SORT };
    controlsFromState(); render();
  }

  // ---------- Column chooser ----------
  function buildColumnMenu() {
    el.colBody.innerHTML = COLUMNS.map((c) => `<label><input type="checkbox" data-col="${c.key}" ${colVisible(c.key) ? 'checked' : ''} ${c.fixed ? 'disabled' : ''}> ${esc(c.label)}</label>`).join('');
    el.colBody.addEventListener('change', (e) => {
      const cb = e.target.closest('input[data-col]'); if (!cb) return;
      colPrefs[cb.dataset.col] = cb.checked;
      try { localStorage.setItem('cols', JSON.stringify(colPrefs)); } catch { /* ignore */ }
      render();
    });
    document.addEventListener('click', (e) => { if (el.colMenu.open && !el.colMenu.contains(e.target)) el.colMenu.open = false; });
    el.colMenu.addEventListener('keydown', (e) => { if (e.key === 'Escape' && el.colMenu.open) { el.colMenu.open = false; el.colMenu.querySelector('summary').focus(); } });
  }

  // ---------- Theme ----------
  const THEMES = [
    { v: 'system', ic: 'i-monitor', label: 'Theme: follows system' },
    { v: 'light', ic: 'i-sun', label: 'Theme: light' },
    { v: 'dark', ic: 'i-moon', label: 'Theme: dark' },
  ];
  function applyTheme(v) {
    if (v === 'light' || v === 'dark') document.documentElement.setAttribute('data-theme', v); else document.documentElement.removeAttribute('data-theme');
    try { if (v === 'system') localStorage.removeItem('theme'); else localStorage.setItem('theme', v); } catch { /* ignore */ }
    const t = THEMES.find((x) => x.v === v) || THEMES[0];
    el.theme.innerHTML = icon(t.ic); el.theme.setAttribute('aria-label', t.label); el.theme.title = t.label;
  }
  function currentTheme() { try { return localStorage.getItem('theme') || 'system'; } catch { return 'system'; } }

  // ---------- Detail dialog with history integration ----------
  let detailPushed = false, suppressHistory = false, lastTrigger = null;
  function openDetail(slug, { push = true, trigger = null } = {}) {
    const r = BY_SLUG.get(slug); if (!r) return false;
    state.resort = slug; lastTrigger = trigger || document.activeElement;
    el.detailInner.innerHTML = detailHTML(r);
    if (!el.detail.open) el.detail.showModal();
    el.detailInner.scrollTop = 0;
    if (push) { history.pushState(null, '', urlFor(stateToParams())); detailPushed = true; }
    document.title = `${r.resort_name} · Alpine Ski Resorts 2026/27`;
    requestAnimationFrame(() => { $('detail-title')?.focus(); });
    return true;
  }
  function closeDetail() { if (el.detail.open) el.detail.close(); }
  el.detail.addEventListener('close', () => {
    state.resort = null; document.title = 'Ski Bums · Alpine Ski Resorts 2026/27';
    if (suppressHistory) suppressHistory = false;
    else if (detailPushed) { detailPushed = false; history.back(); }
    else syncURL();
    if (lastTrigger && document.contains(lastTrigger)) lastTrigger.focus(); lastTrigger = null;
  });
  el.detail.addEventListener('click', (e) => {
    if (e.target.closest('#detail-close')) closeDetail();
    else if (e.target === el.detail) closeDetail(); // backdrop click
  });
  window.addEventListener('popstate', () => {
    readURL(); controlsFromState(); render();
    if (state.resort && !el.detail.open) { if (!openDetail(state.resort, { push: false })) { state.resort = null; syncURL(); } }
    else if (!state.resort && el.detail.open) { suppressHistory = true; detailPushed = false; el.detail.close(); }
    else if (state.resort && el.detail.open) { const r = BY_SLUG.get(state.resort); if (r) el.detailInner.innerHTML = detailHTML(r); }
  });

  // ---------- Filters dialog (mobile modal / desktop inline) ----------
  let filtersModal = false;
  function placeFilters() {
    if (isDesktop()) { if (el.filtersDialog.open && filtersModal) el.filtersDialog.close(); if (!el.filtersDialog.open) el.filtersDialog.show(); filtersModal = false; }
    else if (el.filtersDialog.open && !filtersModal) el.filtersDialog.close();
  }
  function openFilters() { if (isDesktop()) return; if (el.filtersDialog.open) el.filtersDialog.close(); filtersModal = true; el.filtersDialog.showModal(); el.filtersClose.focus(); }
  function closeFilters() { if (filtersModal && el.filtersDialog.open) el.filtersDialog.close(); }
  el.filtersDialog.addEventListener('close', () => { if (filtersModal) { filtersModal = false; el.filtersOpen.focus(); } });
  el.filtersDialog.addEventListener('click', (e) => { if (filtersModal && e.target === el.filtersDialog) closeFilters(); });

  // ---------- Toast ----------
  let toastTimer = null;
  function toast(msg) { el.toast.textContent = msg; el.toast.classList.add('show'); clearTimeout(toastTimer); toastTimer = setTimeout(() => el.toast.classList.remove('show'), 2200); }

  // ---------- Wire up events ----------
  function wire() {
    let searchTimer = null;
    el.search.addEventListener('input', () => { clearTimeout(searchTimer); el.searchClear.hidden = !el.search.value; searchTimer = setTimeout(() => { state.q = el.search.value.trim(); render(); }, 150); });
    el.searchForm.addEventListener('submit', (e) => { e.preventDefault(); clearTimeout(searchTimer); state.q = el.search.value.trim(); render(); el.search.blur(); });
    el.searchClear.addEventListener('click', () => { el.search.value = ''; state.q = ''; el.searchClear.hidden = true; render(); el.search.focus(); });
    el.searchToggle.addEventListener('click', () => { el.header.classList.add('search-open'); el.searchToggle.setAttribute('aria-expanded', 'true'); el.search.focus(); });
    el.search.addEventListener('blur', () => { if (!isDesktop() && !el.search.value) { el.header.classList.remove('search-open'); el.searchToggle.setAttribute('aria-expanded', 'false'); } });
    el.search.addEventListener('keydown', (e) => { if (e.key === 'Escape') { if (el.search.value) { el.search.value = ''; state.q = ''; el.searchClear.hidden = true; render(); } else el.search.blur(); } });

    el.filters.addEventListener('change', (e) => {
      const t = e.target;
      if (t.name === 'c') { state.countries = new Set([...el.countryChips.querySelectorAll('input:checked')].map((i) => i.value)); }
      else if (t.name === 't') { state.types = new Set([...el.typeChips.querySelectorAll('input:checked')].map((i) => i.value)); }
      else if (t === el.openBy) { state.by = /^\d{4}-\d{2}-\d{2}$/.test(t.value) ? t.value : ''; el.openByNote.hidden = !state.by; el.openByClear.hidden = !state.by; }
      else if (t === el.hideLow) state.hideLow = t.checked;
      else return;
      render();
    });
    el.filters.addEventListener('input', (e) => {
      const t = e.target;
      if (t === el.hours) { state.hours = parseFloat(t.value); updateHoursOut(); scheduleRender(); }
      else if (t === el.fr) { state.fr = parseFloat(t.value); el.frOut.textContent = state.fr ? state.fr.toFixed(1) : '0'; scheduleRender(); }
      else if (t === el.to) { state.to = parseFloat(t.value); el.toOut.textContent = state.to ? state.to.toFixed(1) : '0'; scheduleRender(); }
    });
    el.filters.addEventListener('click', (e) => {
      const b = e.target.closest('button[data-step]'); if (!b) return;
      const input = $(b.dataset.step); const v = Math.min(5, Math.max(0, parseFloat(input.value) + parseFloat(b.dataset.delta)));
      input.value = String(v); input.dispatchEvent(new Event('input', { bubbles: true }));
    });
    el.filters.addEventListener('submit', (e) => e.preventDefault());
    el.openByClear.addEventListener('click', () => { el.openBy.value = ''; state.by = ''; el.openByNote.hidden = true; el.openByClear.hidden = true; render(); el.openBy.focus(); });
    el.reset.addEventListener('click', resetAll); el.resetTop.addEventListener('click', resetAll); el.emptyReset.addEventListener('click', resetAll);
    el.filtersOpen.addEventListener('click', openFilters);
    el.filtersClose.addEventListener('click', closeFilters);
    el.filtersDone.addEventListener('click', closeFilters);

    el.mobileSort.addEventListener('change', () => { const [key, dir] = el.mobileSort.value.split(':'); state.sort = { key, dir }; render(); });
    el.results.addEventListener('click', (e) => {
      const sortBtn = e.target.closest('button[data-sort]');
      if (sortBtn) {
        const key = sortBtn.dataset.sort; const col = COLUMNS.find((c) => c.key === key);
        state.sort = state.sort.key === key ? { key, dir: state.sort.dir === 'asc' ? 'desc' : 'asc' } : { key, dir: col.dir || 'asc' };
        render();
        // keep focus on the same header after re-render
        el.results.querySelector(`button[data-sort="${key}"]`)?.focus();
        return;
      }
      const open = e.target.closest('a[data-open]');
      if (open) { e.preventDefault(); openDetail(open.dataset.open, { trigger: open }); }
    });
    el.copyLink.addEventListener('click', async () => {
      const url = location.href;
      try { await navigator.clipboard.writeText(url); toast('Link to this view copied'); }
      catch { window.prompt('Copy this link', url); }
    });
    el.theme.addEventListener('click', () => { const i = THEMES.findIndex((t) => t.v === currentTheme()); applyTheme(THEMES[(i + 1) % THEMES.length].v); });

    mqDesktop.addEventListener('change', () => { placeFilters(); render(); });
    const ro = new ResizeObserver(() => { document.documentElement.style.setProperty('--header-h', `${el.header.offsetHeight}px`); });
    ro.observe(el.header);
  }

  // ---------- Boot ----------
  async function loadJSON(url) { const res = await fetch(url, { cache: 'no-cache' }); if (!res.ok) throw new Error(`${url}: HTTP ${res.status}`); return res.json(); }
  async function boot() {
    buildChips(); buildColumnMenu(); applyTheme(currentTheme()); readURL(); controlsFromState(); placeFilters(); wire();
    try {
      const [rows, meta] = await Promise.all([loadJSON('data/resorts.json'), loadJSON('data/meta.json').catch(() => ({}))]);
      if (!Array.isArray(rows)) throw new Error('resorts.json is not an array');
      META = { ...META, ...meta, row_count: rows.length };
      DATA = prepare(rows);
    } catch (err) {
      console.error(err);
      el.loadError.hidden = false; el.results.setAttribute('aria-busy', 'false'); el.count.textContent = 'Data unavailable'; el.subtitle.textContent = 'Data unavailable';
      return;
    }
    el.subtitle.textContent = `${fmtInt.format(DATA.length)} resorts · data as of ${META.generated_at || 'unknown'}`;
    el.footerData.textContent = `Data as of ${META.generated_at || 'unknown'}`;
    el.footerSeason.textContent = `Season ${META.season || '2026/27'}`;
    el.banner.hidden = !META.sample;
    render();
    if (state.resort && !openDetail(state.resort, { push: false })) { state.resort = null; syncURL(); }
    if ('serviceWorker' in navigator && (location.protocol === 'https:' || ['localhost', '127.0.0.1'].includes(location.hostname))) {
      navigator.serviceWorker.register('./sw.js').catch(() => undefined);
    }
  }
  boot();
})();
