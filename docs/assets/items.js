// Wiki predmetov: iskalnik, filtri, recepti in buildi, ki predmet uporabljajo (podatki: assets/items.json)
(function () {
  var list = document.getElementById('wlist');
  if (!list) return;
  var count = document.getElementById('wcount');
  var more = document.getElementById('wmore');
  var PAGE = 60;
  var D = null, T = {}, BY = {}, ALIAS = {}, BASES = [], RWS = [], SETS = {};
  var state = { q: '', c: 'all', slot: '', cls: '', ph: '', req: '', used: false, sort: 'use', focus: null };
  var shown = PAGE, results = [];

  var CAT = { unique: 'Unique', set: 'Set', runeword: 'Runeword', craft: 'Craft', rune: 'Runa', gem: 'Dragulj',
    jewel: 'Jewel', charm: 'Charm', base: 'Baza' };
  var SLOT = { weapon: 'orožje', offhand: 'druga roka', helm: 'helm', armor: 'oklep', gloves: 'rokavice', belt: 'pas',
    boots: 'škornji', amulet: 'amulet', ring: 'prstan', ring1: 'prstan', ring2: 'prstan', charm: 'charm',
    socket: 'socket', swapWeapon: 'switch', swapOffhand: 'switch 2' };
  var PH = { s: 'začetek', m: 'prvi teden', e: 'endgame' };
  var SOCK = { weapon: 'Orožje', shield: 'Ščit', chest: 'Oklep', helm: 'Helm' };
  var TIER = { normal: 'normal', exceptional: 'exceptional', elite: 'elite' };

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function strip(h) {
    return (h || '').replace(/<[^>]+>/g, ' ').replace(/&amp;/g, '&').replace(/&#x27;|&#39;/g, "'").replace(/&quot;/g, '"');
  }
  function pct(v) { return String(v).replace('.', ','); }
  function img(path, alt) {
    return path ? '<img src="img/' + esc(path) + '" alt="' + esc(alt || '') + '" loading="lazy" onerror="this.remove()">' : '';
  }
  function tierCls(t) { return 't-' + String(t || '').toLowerCase().replace(/[^a-z]+/g, '-').replace(/^-|-$/g, ''); }
  function plural(n, one, two, few, many) {
    var k = n % 100;
    return n + ' ' + (k === 1 ? one : k === 2 ? two : (k === 3 || k === 4) ? few : many);
  }

  // ---------- priprava ----------
  function prepare(data, tips) {
    D = data;
    T = tips || {};
    D.items.forEach(function (e) {
      BY[e.k] = e;
      (e.a || []).forEach(function (a) { ALIAS[a] = e.k; });
      e.nb = (e.u || []).length;
      e.cls = {};
      e.phs = '';
      (e.u || []).forEach(function (u) {
        e.cls[D.builds[u[0]][0]] = 1;
        for (var i = 0; i < u[1].length; i++) if (e.phs.indexOf(u[1][i]) < 0) e.phs += u[1][i];
      });
      var extra = [e.n, e.b, e.set, (e.ru || []).join(' '), CAT[e.c], e.cat, strip(T[e.tip])];
      (e.var || []).forEach(function (v) { extra.push(v[0], strip(T[v[1]])); });
      e.txt = extra.join(' ').toLowerCase();
      if (e.c === 'base') BASES.push(e);
      if (e.c === 'runeword') RWS.push(e);
      if (e.set) (SETS[e.set] = SETS[e.set] || []).push(e);
    });
  }

  function fits(rw, b) {
    if (b.ms < rw.ru.length) return false;
    var ok = (rw.it || []).some(function (t) { return b.ta.indexOf(t) >= 0; });
    if (!ok) return false;
    return !(rw.et || []).some(function (t) { return b.ta.indexOf(t) >= 0; });
  }

  // ---------- filtri ----------
  function match(e, words) {
    if (state.c === 'all') {
      if (e.c === 'base' && !words.length) return false;
    } else if (state.c === 'gemjewel') {
      if (e.c !== 'gem' && e.c !== 'jewel') return false;
    } else if (e.c !== state.c) return false;
    if (state.slot && (e.s || []).indexOf(state.slot) < 0) return false;
    if (state.req && (e.r || 0) > Number(state.req)) return false;
    if (state.used && !e.nb) return false;
    if (state.cls || state.ph) {
      if (!e.nb) return false;
      var ok = e.u.some(function (u) {
        return (!state.cls || D.builds[u[0]][0] === state.cls) && (!state.ph || u[1].indexOf(state.ph) >= 0);
      });
      if (!ok) return false;
    }
    for (var i = 0; i < words.length; i++) if (e.txt.indexOf(words[i]) < 0) return false;
    return true;
  }

  function sorter(a, b) {
    var s = state.sort;
    if (s === 'name') return a.n.localeCompare(b.n);
    if (s === 'req') return (a.r || 0) - (b.r || 0) || (a.rank || 0) - (b.rank || 0) || a.n.localeCompare(b.n);
    if (s === 'reqd') return (b.r || 0) - (a.r || 0) || (b.rank || 0) - (a.rank || 0) || a.n.localeCompare(b.n);
    if (s === 's13') return (b.s13 || 0) - (a.s13 || 0) || b.nb - a.nb || a.n.localeCompare(b.n);
    return b.nb - a.nb || (b.s13 || 0) - (a.s13 || 0) || a.n.localeCompare(b.n);
  }

  function run() {
    if (!D) return;
    if (state.focus) {
      var f = BY[state.focus];
      results = f ? [f] : [];
    } else {
      var words = state.q.toLowerCase().split(/\s+/).filter(Boolean);
      results = D.items.filter(function (e) { return match(e, words); });
      results.sort(sorter);
    }
    shown = PAGE;
    render();
  }

  // ---------- izpis ----------
  function card(e, open) {
    var sub = [];
    if (e.b) sub.push(esc(e.b));
    if (e.t) sub.push(esc(TIER[e.t] || e.t));
    if (e.set) sub.push('set ' + esc(e.set));
    if (e.cat) sub.push(esc(e.cat) + ' craft');
    if (e.ru) sub.push('<span class="runes-c">' + esc(e.ru.join(' · ')) + '</span>');
    var badges = [];
    badges.push('<span class="badge q-' + esc(e.q) + '">' + esc(CAT[e.c] || e.c) + '</span>');
    if (e.r) badges.push('<span class="badge">lvl ' + e.r + '</span>');
    if (e.nb) badges.push('<span class="badge t-good">' + plural(e.nb, 'build', 'builda', 'buildi', 'buildov') + '</span>');
    if (e.s13) badges.push('<span class="badge muted" title="Delež likov 90+ v S13 (pd2.tools)">S13 ' + pct(e.s13) + ' %</span>');
    return '<details class="wi" data-k="' + esc(e.k) + '"' + (open ? ' open' : '') + '><summary>' +
      '<span class="ic"' + (T[e.tip] ? ' data-tip="' + esc(e.tip) + '"' : '') + '>' + img(e.i, e.n) + '</span>' +
      '<span class="wn"><b class="q-' + esc(e.q) + '">' + esc(e.n) + '</b><span class="muted">' + sub.join(' · ') + '</span></span>' +
      '<span class="wb">' + badges.join('') + '</span></summary><div class="wd"></div></details>';
  }

  function chip(e, label) {
    return '<span class="chip"' + (T[e.tip] ? ' data-tip="' + esc(e.tip) + '" tabindex="0"' : '') + '>' + img(e.i, e.n) +
      '<span class="q-' + esc(e.q) + '">' + esc(label || e.n) + '</span></span>';
  }
  function wikiLink(e) { return '<a href="#k=' + encodeURIComponent(e.k) + '" class="wl">' + esc(e.n) + '</a>'; }

  function socketLines(kinds) {
    return kinds.filter(function (k) { return D.socket[k]; }).map(function (k) {
      var s = D.socket[k];
      return '<li><b>' + SOCK[k] + ':</b> ' + esc(s.recipe) + ' + bela ali superior baza (naključno ' + s.lo + '–' + s.hi + ' os)</li>';
    }).join('');
  }

  function roleText(r) {
    var merc = r.indexOf('merc ') === 0;
    var x = merc ? r.slice(5) : r;
    var out;
    if (SLOT[x]) out = SLOT[x];
    else if (x.indexOf('socket: ') === 0) out = 'socket v ' + (SLOT[x.slice(8)] || x.slice(8));
    else if (x.indexOf('baza: ') === 0) out = 'baza za ' + x.slice(6);
    else out = 'za ' + x;
    return (merc ? 'merc: ' : '') + out;
  }

  function usedBy(e) {
    if (!e.nb) return '<p class="muted">Noben build na tej strani ga ne nosi.</p>';
    var by = {};
    e.u.forEach(function (u) {
      var b = D.builds[u[0]];
      (by[b[0]] = by[b[0]] || []).push([b, u]);
    });
    var html = '';
    Object.keys(D.classes).forEach(function (c) {
      if (!by[c]) return;
      html += '<div class="wcls"><b>' + esc(D.classes[c]) + '</b><ul>' + by[c].map(function (x) {
        var b = x[0], u = x[1];
        var ph = u[1].split('').map(function (p) { return PH[p]; }).join(', ');
        return '<li><a href="' + esc(b[0]) + '.html#b-' + esc(b[1]) + '">' + esc(b[2]) + '</a> <span class="' + tierCls(b[3]) + '">' +
          esc(b[3]) + '</span> <span class="muted">' + esc(u[2].map(roleText).join(', ')) + ' · ' + esc(ph) + '</span></li>';
      }).join('') + '</ul></div>';
    });
    return html;
  }

  function details(e) {
    var stats = '';
    if (T[e.tip]) stats = '<div class="tt tt-static">' + T[e.tip] + '</div>';
    var side = [];
    if (e.var) {
      side.push('<div><h4>Različice</h4><div class="chips">' + e.var.map(function (v) {
        return '<span class="chip" data-tip="' + esc(v[1]) + '" tabindex="0"><span class="q-r">' + esc(v[0]) + '</span></span>';
      }).join('') + '</div><p class="muted note-s">Isti runeword z izbiro oskilla. Premakni miško na različico za njene statse.</p></div>');
    }
    if (e.c === 'runeword') {
      var runes = e.ru.map(function (r, i) {
        var re = BY['so:' + r.toLowerCase() + '_rune'];
        return re ? chip(re, r) : '<span class="chip">' + img(e.ri[i], r) + esc(r) + '</span>';
      }).join('<span class="plus">+</span>');
      var bases = BASES.filter(function (b) { return fits(e, b); });
      var order = { elite: 0, exceptional: 1, normal: 2 };
      bases.sort(function (a, b) { return b.nb - a.nb || order[a.t] - order[b.t] || (a.r || 0) - (b.r || 0); });
      var kinds = [];
      bases.forEach(function (b) { if (b.sk && kinds.indexOf(b.sk) < 0) kinds.push(b.sk); });
      side.push('<div><h4>Recept</h4><div class="chips">' + runes + '</div><p class="note-s">Rune vstaviš po vrsti v belo ali superior bazo z natanko ' +
        e.ru.length + ' socketi (' + esc(e.b) + ').</p></div>');
      side.push('<div><h4>Baze z ' + e.ru.length + ' os (' + bases.length + ')</h4><div class="chips">' +
        bases.slice(0, 16).map(function (b) { return chip(b, b.n + (b.nb ? ' ★' : '')); }).join('') +
        (bases.length > 16 ? '<span class="muted note-s">in še ' + (bases.length - 16) + '</span>' : '') +
        '</div><p class="muted note-s">★ bazo nosi kak build s te strani. Najprej so elite baze.</p></div>');
      side.push('<div><h4>Socketi</h4><ul class="plain">' + socketLines(kinds) +
        '<li><b>Larzuk</b> (A5 quest): beli bazi da največ socketov, kar jih baza in ilvl dopuščata.</li></ul></div>');
    }
    if (e.c === 'craft') {
      side.push('<div><h4>Recept</h4><ul class="plain"><li>' + esc(e.ing.join(' + ')) + ' + magic ali rare ' + esc((e.b || '').toLowerCase()) + '</li>' +
        (e.alt ? '<li>ali ' + esc(e.alt.join(' + ')) + ' + baza (infuzije padajo od Treasure Fallen v mapah)</li>' : '') +
        '<li class="muted">Ilvl crafta = clvl/2 + ilvl baze/2. Eth baza da eth craft. Predpisani affixi so v statsih, poleg pride do 4 naključnih.</li></ul></div>');
    }
    if (e.c === 'rune') {
      if (e.up) side.push('<div><h4>Nadgradnja v cubu</h4><p>' + esc(e.up) + ' → 1× ' + esc(e.n.replace(' Rune', '')) + '</p><p class="muted note-s">V S14 ključ ni več potreben.</p></div>');
      var nm = e.n.replace(' Rune', '');
      var rws = RWS.filter(function (r) { return r.ru.indexOf(nm) >= 0; });
      rws.sort(function (a, b) { return b.nb - a.nb || (a.r || 0) - (b.r || 0); });
      if (rws.length) side.push('<div><h4>Runewordi s to runo (' + rws.length + ')</h4><div class="chips">' +
        rws.map(function (r) { return '<a class="chip" href="#k=' + encodeURIComponent(r.k) + '"><span class="q-r">' + esc(r.n) + '</span></a>'; }).join('') +
        '</div><p class="note-s"><a href="runewordi.html#r=' + encodeURIComponent(nm) + '">V iskalniku runewordov s filtri →</a></p></div>');
    }
    if (e.c === 'base') {
      var fitting = RWS.filter(function (r) { return fits(r, e); });
      fitting.sort(function (a, b) { return b.nb - a.nb || (a.r || 0) - (b.r || 0); });
      side.push('<div><h4>Socketi</h4><ul class="plain"><li>Največ ' + e.ms + ' os (pri ilvl 41+).</li>' + socketLines(e.sk ? [e.sk] : []) + '</ul></div>');
      if (fitting.length) side.push('<div><h4>Runewordi za to bazo (' + fitting.length + ')</h4><div class="chips">' +
        fitting.map(function (r) { return '<a class="chip" href="#k=' + encodeURIComponent(r.k) + '"><span class="q-r">' + esc(r.n) + '</span> <span class="muted">' + r.ru.length + ' os</span></a>'; }).join('') + '</div></div>');
    }
    if (e.up && e.c !== 'rune') side.push('<div><h4>Nadgradnja v cubu</h4><p>' + esc(e.up) + '</p></div>');
    if (e.set && SETS[e.set]) {
      side.push('<div><h4>Set ' + esc(e.set) + '</h4><div class="chips">' + SETS[e.set].map(function (x) {
        return x === e ? chip(x) : '<a class="chip" href="#k=' + encodeURIComponent(x.k) + '"' + (T[x.tip] ? ' data-tip="' + esc(x.tip) + '"' : '') + '>' + img(x.i, x.n) + '<span class="q-s">' + esc(x.n) + '</span></a>';
      }).join('') + '</div></div>');
    }
    if (e.cl) side.push('<p class="muted note-s">Samo za razred ' + esc(e.cl) + '.</p>');
    side.push('<div class="wuse"><h4>Kdo ga nosi' + (e.nb ? ' (' + e.nb + ')' : '') + '</h4>' + usedBy(e) + '</div>');
    return (stats ? '<div class="wstats">' + stats + '</div>' : '') + '<div class="wside">' + side.join('') + '</div>';
  }

  function render() {
    var n = results.length;
    if (state.focus) {
      count.innerHTML = 'Prikazan en predmet. <button type="button" class="linkbtn" id="wall">Pokaži vse</button>';
      document.getElementById('wall').addEventListener('click', function () { clearFocus(); run(); });
    } else {
      count.textContent = 'Najdenih: ' + n + (state.c === 'all' && !state.q ? ' (baze so pod »Baze« ali pri iskanju)' : '');
    }
    list.innerHTML = results.slice(0, shown).map(function (e) { return card(e, !!state.focus); }).join('') ||
      '<p class="muted">Ni zadetkov. Poskusi z drugo besedo ali odstrani kak filter.</p>';
    if (state.focus) list.querySelectorAll('details.wi').forEach(fillDetails);
    more.hidden = n <= shown;
    if (!more.hidden) more.textContent = 'Pokaži več (še ' + (n - shown) + ')';
  }

  function fillDetails(d) {
    var box = d.querySelector('.wd');
    if (box && !box.childNodes.length) box.innerHTML = details(BY[d.dataset.k]);
  }
  list.addEventListener('toggle', function (ev) {
    if (ev.target.matches && ev.target.matches('details.wi') && ev.target.open) fillDetails(ev.target);
  }, true);

  more.addEventListener('click', function () {
    var from = shown;
    shown += PAGE;
    list.insertAdjacentHTML('beforeend', results.slice(from, shown).map(function (e) { return card(e, false); }).join(''));
    more.hidden = results.length <= shown;
    if (!more.hidden) more.textContent = 'Pokaži več (še ' + (results.length - shown) + ')';
  });

  // ---------- kontrole ----------
  function clearFocus() {
    if (!state.focus) return;
    state.focus = null;
    if (history.replaceState) history.replaceState(null, '', location.pathname);
  }
  var q = document.getElementById('wq'), timer = null;
  q.addEventListener('input', function () {
    clearTimeout(timer);
    timer = setTimeout(function () { clearFocus(); state.q = q.value.trim(); run(); }, 120);
  });
  var cbtns = Array.prototype.slice.call(document.querySelectorAll('.wfilters [data-c]'));
  cbtns.forEach(function (b) {
    b.addEventListener('click', function () {
      clearFocus();
      state.c = b.dataset.c;
      cbtns.forEach(function (x) { x.setAttribute('aria-pressed', String(x === b)); });
      run();
    });
  });
  [['wslot', 'slot'], ['wcls', 'cls'], ['wph', 'ph'], ['wsort', 'sort']].forEach(function (p) {
    document.getElementById(p[0]).addEventListener('change', function (ev) { clearFocus(); state[p[1]] = ev.target.value; run(); });
  });
  var req = document.getElementById('wreq');
  req.addEventListener('input', function () { clearFocus(); state.req = req.value; run(); });
  var used = document.getElementById('wused');
  used.addEventListener('change', function () { clearFocus(); state.used = used.checked; run(); });

  function fromHash() {
    var m = /^#k=(.+)$/.exec(location.hash);
    if (!m || !D) return false;
    var key = decodeURIComponent(m[1]);
    key = BY[key] ? key : ALIAS[key];
    if (!key) return false;
    state.focus = key;
    run();
    window.scrollTo(0, list.getBoundingClientRect().top + window.pageYOffset - 120);
    return true;
  }
  window.addEventListener('hashchange', fromHash);

  Promise.all([
    fetch('assets/items.json').then(function (r) { return r.json(); }),
    new Promise(function (res) { window.PD2.tips(res); })
  ]).then(function (v) {
    prepare(v[0], v[1]);
    if (!fromHash()) run();
  }).catch(function () {
    count.textContent = 'Predmetov ni bilo mogoče naložiti. Osveži stran.';
  });
})();
