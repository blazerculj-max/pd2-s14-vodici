// Runewordi: filtri po bazi in socketih, iskanje po runah, ki jih imaš (podatki: assets/items.json)
(function () {
  var list = document.getElementById('rlist');
  if (!list) return;
  var count = document.getElementById('rcount');
  var more = document.getElementById('rmore');
  var PAGE = 40;
  var D = null, T = {}, RWS = [], BASES = [], RUNES = [], RUNE = {}, S14 = {};
  var state = { q: '', main: '', sub: '', sock: '', req: '', used: false, s14: false, sort: 'use', mode: 'any', have: {} };
  var shown = PAGE, results = [];

  // vrste baz: [ključ, oznaka, kam gre, tipi baz (prvi tip v verigi)]
  var GROUPS = [
    ['swor', 'Meči', 'weapon', ['swor', '2hcs']],
    ['axe', 'Sekire', 'weapon', ['axe']],
    ['mace', 'Maci in kladiva', 'weapon', ['club', 'mace', 'hamm']],
    ['scep', 'Žezla', 'weapon', ['scep']],
    ['knif', 'Bodala', 'weapon', ['knif']],
    ['spea', 'Kopja', 'weapon', ['spea', 'aspe']],
    ['pole', 'Polearmi', 'weapon', ['pole', 'sc9']],
    ['staf', 'Staffi', 'weapon', ['staf']],
    ['wand', 'Wandi', 'weapon', ['wand']],
    ['orb', 'Orbi (sorc)', 'weapon', ['orb']],
    ['h2h', 'Kremplji (assassin)', 'weapon', ['h2h', 'h2h2']],
    ['bow', 'Loki', 'weapon', ['bow', 'abow']],
    ['xbow', 'Samostreli', 'weapon', ['xbow']],
    ['thro', 'Metalno orožje', 'weapon', ['jave', 'ajav', 'tkni', 'taxe']],
    ['tors', 'Oklepi', 'armor', ['tors']],
    ['shie', 'Ščiti', 'shield', ['shie']],
    ['ashd', 'Paladin ščiti', 'shield', ['ashd']],
    ['head', 'Necro glave', 'shield', ['head']],
    ['helm', 'Helmi', 'helm', ['helm']],
    ['circ', 'Circleti', 'helm', ['circ']],
    ['pelt', 'Druid pelti', 'helm', ['pelt']],
    ['phlm', 'Barb helmi', 'helm', ['phlm']]
  ];
  var MAIN = { weapon: 'Orožje', armor: 'Oklep', shield: 'Ščit', helm: 'Helm' };
  var MAIN_ORDER = ['weapon', 'armor', 'shield', 'helm'];
  var G = {}, GROUP_OF = {};
  GROUPS.forEach(function (g) {
    G[g[0]] = { k: g[0], n: g[1], m: g[2] };
    g[3].forEach(function (t) { GROUP_OF[t] = g[0]; });
  });
  var SOCK = { weapon: 'Orožje', shield: 'Ščit', chest: 'Oklep', helm: 'Helm' };
  var PH = { s: 'začetek', m: 'prvi teden', e: 'endgame' };

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function strip(h) {
    return (h || '').replace(/<[^>]+>/g, ' ').replace(/&amp;/g, '&').replace(/&#x27;|&#39;/g, "'").replace(/&quot;/g, '"');
  }
  function img(path, alt) {
    return path ? '<img src="img/' + esc(path) + '" alt="' + esc(alt || '') + '" loading="lazy" onerror="this.remove()">' : '';
  }
  function tierCls(t) { return 't-' + String(t || '').toLowerCase().replace(/[^a-z]+/g, '-').replace(/^-|-$/g, ''); }
  function plural(n, one, two, few, many) {
    var k = n % 100;
    return n + ' ' + (k === 1 ? one : k === 2 ? two : (k === 3 || k === 4) ? few : many);
  }
  function pct(v) { return String(v).replace('.', ','); }

  // ---------- priprava ----------
  function fits(rw, b) {
    if (b.ms < rw.ru.length) return false;
    if (!(rw.it || []).some(function (t) { return b.ta.indexOf(t) >= 0; })) return false;
    return !(rw.et || []).some(function (t) { return b.ta.indexOf(t) >= 0; });
  }

  function prepare(data, tips) {
    D = data;
    T = tips || {};
    D.items.forEach(function (e) {
      if (e.c === 'base') BASES.push(e);
      else if (e.c === 'rune') RUNES.push(e);
    });
    RUNES.sort(function (a, b) { return a.rank - b.rank; });
    RUNES.forEach(function (r) { r.short = r.n.replace(' Rune', ''); RUNE[r.short] = r; });
    BASES.forEach(function (b) { b.nb = (b.u || []).length; b.g = GROUP_OF[b.ta[0]]; });
    D.items.forEach(function (e) {
      if (e.c !== 'runeword') return;
      e.nb = (e.u || []).length;
      e.bases = BASES.filter(function (b) { return fits(e, b); });
      e.gr = {};
      e.mains = {};
      e.bases.forEach(function (b) {
        if (!b.g) return;
        e.gr[b.g] = 1;
        e.mains[G[b.g].m] = 1;
      });
      e.ranks = e.ru.map(function (r) { return RUNE[r] ? RUNE[r].rank : 0; });
      e.top = Math.max.apply(null, e.ranks);
      e.sum = e.ranks.reduce(function (a, b) { return a + b; }, 0);
      e.s14 = S14[e.n] || null;
      e.txt = [e.n, e.ru.join(' '), strip(T[e.tip]), (e.var || []).map(function (v) { return v[0] + ' ' + strip(T[v[1]]); }).join(' '),
        e.s14 ? e.s14.note : ''].join(' ').toLowerCase();
      RWS.push(e);
    });
  }

  // koliko run manjka glede na rune, ki jih imaš (ponovitve štejejo)
  function missing(rw) {
    var left = {}, miss = [];
    Object.keys(state.have).forEach(function (r) { left[r] = state.have[r]; });
    rw.ru.forEach(function (r) { if (left[r] > 0) left[r]--; else miss.push(r); });
    return miss;
  }
  function haveAny() { return Object.keys(state.have).length > 0; }

  // ---------- filtri ----------
  function match(e, words) {
    if (state.main && !e.mains[state.main]) return false;
    if (state.sub && !e.gr[state.sub]) return false;
    if (state.sock && e.ru.length !== Number(state.sock)) return false;
    if (state.req && (e.r || 0) > Number(state.req)) return false;
    if (state.used && !e.nb) return false;
    if (state.s14 && !e.s14) return false;
    for (var i = 0; i < words.length; i++) if (e.txt.indexOf(words[i]) < 0) return false;
    e.miss = null;
    if (haveAny()) {
      var have = Object.keys(state.have);
      if (state.mode === 'any') return e.ru.some(function (r) { return state.have[r]; });
      if (state.mode === 'all') return have.every(function (r) { return e.ru.indexOf(r) >= 0; });
      e.miss = missing(e);
      return e.miss.length <= (state.mode === 'make' ? 0 : 1);
    }
    return true;
  }

  function sorter(a, b) {
    if (state.mode === 'one' && haveAny()) {
      var d = (a.miss || []).length - (b.miss || []).length;
      if (d) return d;
    }
    var s = state.sort;
    if (s === 'name') return a.n.localeCompare(b.n);
    if (s === 'req') return (a.r || 0) - (b.r || 0) || a.n.localeCompare(b.n);
    if (s === 'cheap') return a.top - b.top || a.sum - b.sum || a.n.localeCompare(b.n);
    if (s === 'dear') return b.top - a.top || b.sum - a.sum || a.n.localeCompare(b.n);
    return b.nb - a.nb || (b.s13 || 0) - (a.s13 || 0) || (a.r || 0) - (b.r || 0) || a.n.localeCompare(b.n);
  }

  function run() {
    if (!D) return;
    var words = state.q.toLowerCase().split(/\s+/).filter(Boolean);
    results = RWS.filter(function (e) { return match(e, words); });
    results.sort(sorter);
    shown = PAGE;
    render();
  }

  // ---------- izpis ----------
  function where(e) {
    var parts = [];
    MAIN_ORDER.forEach(function (m) {
      if (!e.mains[m]) return;
      var gs = GROUPS.filter(function (g) { return g[2] === m && e.gr[g[0]]; });
      var all = GROUPS.filter(function (g) { return g[2] === m; }).length;
      if (m === 'armor') parts.push('oklep');
      else if (gs.length === all) parts.push(m === 'weapon' ? 'vsa orožja' : m === 'shield' ? 'vsi ščiti' : 'vsi helmi');
      else if (gs.length > 4) parts.push(MAIN[m].toLowerCase() + ': ' + gs.slice(0, 3).map(function (g) { return g[1].toLowerCase(); }).join(', ') + ' in še ' + (gs.length - 3));
      else parts.push(gs.map(function (g) { return g[1].toLowerCase(); }).join(', '));
    });
    return parts.join(' · ');
  }

  // rune v vrstnem redu; označi tiste, ki jih imaš, in tiste, ki manjkajo
  function runeMarks(e) {
    var left = {};
    Object.keys(state.have).forEach(function (r) { left[r] = state.have[r]; });
    return e.ru.map(function (r) {
      var cls = '';
      if (haveAny()) {
        if (left[r] > 0) { left[r]--; cls = ' have'; } else if (state.mode === 'make' || state.mode === 'one') cls = ' miss';
      }
      return { r: r, cls: cls };
    });
  }

  function card(e) {
    var marks = runeMarks(e);
    var runes = marks.map(function (m) { return '<span class="rr' + m.cls + '">' + esc(m.r) + '</span>'; }).join('<span class="sep">·</span>');
    var badges = ['<span class="badge">' + e.ru.length + ' os</span>'];
    if (e.r) badges.push('<span class="badge">lvl ' + e.r + '</span>');
    if (e.s14) badges.push('<span class="badge ' + (e.s14.s === 'new' ? 't-starter">Novo v S14' : 't-top">S14 sprememba') + '</span>');
    if (e.nb) badges.push('<span class="badge t-good">' + plural(e.nb, 'build', 'builda', 'buildi', 'buildov') + '</span>');
    if (e.s13) badges.push('<span class="badge muted" title="Delež likov 90+ v S13 (pd2.tools)">S13 ' + pct(e.s13) + ' %</span>');
    if (e.miss && e.miss.length) badges.push('<span class="badge rmiss">manjka ' + esc(e.miss.join(', ')) + '</span>');
    return '<details class="wi rw" data-k="' + esc(e.k) + '"><summary>' +
      '<span class="ic"' + (T[e.tip] ? ' data-tip="' + esc(e.tip) + '"' : '') + '>' + img(e.i, e.n) + '</span>' +
      '<span class="wn"><b class="q-r">' + esc(e.n) + '</b><span class="rrunes">' + runes + '</span><span class="muted">' + esc(where(e)) + '</span></span>' +
      '<span class="wb">' + badges.join('') + '</span></summary><div class="wd"></div></details>';
  }

  function chip(e, label, extra) {
    return '<span class="chip' + (extra || '') + '"' + (T[e.tip] ? ' data-tip="' + esc(e.tip) + '" tabindex="0"' : '') + '>' + img(e.i, e.n) +
      '<span>' + esc(label || e.n) + '</span></span>';
  }

  function socketLines(kinds) {
    return kinds.filter(function (k) { return D.socket[k]; }).map(function (k) {
      var s = D.socket[k];
      return '<li><b>' + SOCK[k] + ':</b> ' + esc(s.recipe) + ' + bela ali superior baza (naključno ' + s.lo + '–' + s.hi + ' os)</li>';
    }).join('');
  }

  function usedBy(e) {
    if (!e.nb) return '<p class="muted">Noben build na tej strani ga ne nosi.</p>';
    var by = {};
    e.u.forEach(function (u) {
      var b = D.builds[u[0]];
      (by[b[0]] = by[b[0]] || []).push([b, u]);
    });
    return Object.keys(D.classes).filter(function (c) { return by[c]; }).map(function (c) {
      return '<div class="wcls"><b>' + esc(D.classes[c]) + '</b><ul>' + by[c].map(function (x) {
        var b = x[0], u = x[1];
        var ph = u[1].split('').map(function (p) { return PH[p]; }).join(', ');
        return '<li><a href="' + esc(b[0]) + '.html#b-' + esc(b[1]) + '">' + esc(b[2]) + '</a> <span class="' + tierCls(b[3]) + '">' +
          esc(b[3]) + '</span> <span class="muted">' + esc(ph) + (u[2].some(function (r) { return r.indexOf('merc') === 0; }) ? ', merc' : '') + '</span></li>';
      }).join('') + '</ul></div>';
    }).join('');
  }

  function details(e) {
    var stats = '';
    if (e.s14) stats += '<div class="note rs14"><b>' + (e.s14.s === 'new' ? 'Novo v S14' : 'Sprememba v S14') + ':</b> ' + esc(e.s14.note.replace(/^(Nov v S14|S14): ?/, '')) + '</div>';
    if (T[e.tip]) stats += '<div class="tt tt-static">' + T[e.tip] + '</div>';
    if (e.var) {
      stats += '<div><h4>Različice</h4><div class="chips">' + e.var.map(function (v) {
        return '<span class="chip" data-tip="' + esc(v[1]) + '" tabindex="0"><span class="q-r">' + esc(v[0]) + '</span></span>';
      }).join('') + '</div><p class="muted note-s">Isti runeword z izbiro oskilla.</p></div>';
    }
    var side = [];
    var marks = runeMarks(e);
    side.push('<div><h4>Recept</h4><div class="chips">' + marks.map(function (m) {
      var re = RUNE[m.r];
      return re ? chip(re, m.r, m.cls) : '<span class="chip">' + esc(m.r) + '</span>';
    }).join('<span class="plus">+</span>') + '</div><p class="note-s">Rune vstaviš po vrsti v belo ali superior bazo z natanko ' + e.ru.length + ' socketi.</p></div>');
    var order = { elite: 0, exceptional: 1, normal: 2 };
    var bases = e.bases.filter(function (b) { return !state.sub || b.g === state.sub; });
    bases.sort(function (a, b) { return b.nb - a.nb || order[a.t] - order[b.t] || (b.r || 0) - (a.r || 0); });
    var kinds = [];
    bases.forEach(function (b) { if (b.sk && kinds.indexOf(b.sk) < 0) kinds.push(b.sk); });
    side.push('<div><h4>Baze z ' + e.ru.length + ' os' + (state.sub ? ' · ' + esc(G[state.sub].n.toLowerCase()) : '') + ' (' + bases.length + ')</h4><div class="chips">' +
      bases.slice(0, 18).map(function (b) { return chip(b, b.n + (b.nb ? ' ★' : '')); }).join('') +
      (bases.length > 18 ? '<span class="muted note-s">in še ' + (bases.length - 18) + '</span>' : '') +
      '</div><p class="muted note-s">★ bazo nosi kak build s te strani. Najprej elite baze.</p></div>');
    side.push('<div><h4>Socketi</h4><ul class="plain">' + socketLines(kinds) +
      '<li><b>Larzuk</b> (A5 quest): beli bazi da največ socketov, kar jih baza in ilvl dopuščata.</li></ul></div>');
    side.push('<div class="wuse"><h4>Kdo ga nosi' + (e.nb ? ' (' + e.nb + ')' : '') + '</h4>' + usedBy(e) + '</div>');
    side.push('<p class="note-s"><a href="predmeti.html#k=' + encodeURIComponent(e.k) + '">Odpri v wikiju predmetov →</a></p>');
    return '<div class="wstats">' + stats + '</div><div class="wside">' + side.join('') + '</div>';
  }

  function render() {
    var n = results.length;
    var txt = 'Najdenih: ' + n;
    if (haveAny()) {
      txt += ' · tvoje rune: ' + haveText();
    }
    count.textContent = txt;
    list.innerHTML = results.slice(0, shown).map(card).join('') ||
      '<p class="muted">Ni zadetkov. Poskusi z drugo besedo, drugim načinom iskanja po runah ali odstrani kak filter.</p>';
    more.hidden = n <= shown;
    if (!more.hidden) more.textContent = 'Pokaži več (še ' + (n - shown) + ')';
  }

  function fillDetails(d) {
    var box = d.querySelector('.wd');
    if (box && !box.childNodes.length) box.innerHTML = details(RWS.filter(function (e) { return e.k === d.dataset.k; })[0]);
  }
  list.addEventListener('toggle', function (ev) {
    if (ev.target.matches && ev.target.matches('details.wi') && ev.target.open) fillDetails(ev.target);
  }, true);
  more.addEventListener('click', function () {
    var from = shown;
    shown += PAGE;
    list.insertAdjacentHTML('beforeend', results.slice(from, shown).map(card).join(''));
    more.hidden = results.length <= shown;
    if (!more.hidden) more.textContent = 'Pokaži več (še ' + (results.length - shown) + ')';
  });

  // ---------- rune, ki jih imaš ----------
  var haveInput = document.getElementById('rhave');
  var pal = document.getElementById('rpal');
  var clearBtn = document.getElementById('rclear');

  // »Ber, Mal, 2 Ist«, »Ist x2«, »2x Lo«; neznane besede ignorira
  function parseHave(text) {
    var have = {}, bad = [];
    var re = /(\d+)\s*[x×*]?\s*([a-zA-Zčšž]+)|([a-zA-Zčšž]+)(?:\s*[x×*]\s*(\d+))?/g, m;
    while ((m = re.exec(text))) {
      var name = (m[2] || m[3] || '').toLowerCase();
      var n = Number(m[1] || m[4] || 1);
      if (name === 'rune' || name === 'runa' || name === 'in') continue;
      var r = RUNES.filter(function (x) { return x.short.toLowerCase() === name; })[0];
      if (!r) { bad.push(name); continue; }
      have[r.short] = Math.min(3, (have[r.short] || 0) + n);
    }
    return { have: have, bad: bad };
  }
  function haveText() {
    return RUNES.filter(function (r) { return state.have[r.short]; }).map(function (r) {
      return (state.have[r.short] > 1 ? state.have[r.short] + ' ' : '') + r.short;
    }).join(', ');
  }
  function paintPalette() {
    pal.querySelectorAll('button').forEach(function (b) {
      var n = state.have[b.dataset.r] || 0;
      b.setAttribute('aria-pressed', String(n > 0));
      b.querySelector('.cnt').textContent = n > 1 ? '×' + n : '';
    });
    clearBtn.hidden = !haveAny();
  }
  function buildPalette() {
    pal.innerHTML = RUNES.map(function (r) {
      return '<button type="button" class="rpb" data-r="' + esc(r.short) + '" aria-pressed="false" title="' + esc(r.n) + ' (lvl ' + r.r + ')">' +
        img(r.i, r.short) + '<span>' + esc(r.short) + '</span><span class="cnt"></span></button>';
    }).join('');
    pal.addEventListener('click', function (ev) {
      var b = ev.target.closest('button[data-r]');
      if (!b) return;
      var r = b.dataset.r, n = (state.have[r] || 0) + 1;
      if (n > 3) delete state.have[r]; else state.have[r] = n;
      haveInput.value = haveText();
      paintPalette();
      run();
      writeHash();
    });
  }
  var htimer = null;
  haveInput.addEventListener('input', function () {
    clearTimeout(htimer);
    htimer = setTimeout(function () {
      state.have = parseHave(haveInput.value).have;
      paintPalette();
      run();
      writeHash();
    }, 150);
  });
  clearBtn.addEventListener('click', function () {
    state.have = {};
    haveInput.value = '';
    paintPalette();
    run();
    writeHash();
  });

  // ---------- kontrole ----------
  var q = document.getElementById('rq'), timer = null;
  q.addEventListener('input', function () {
    clearTimeout(timer);
    timer = setTimeout(function () { state.q = q.value.trim(); run(); }, 120);
  });
  var subBox = document.getElementById('rsub');
  function buildSub() {
    var gs = GROUPS.filter(function (g) { return g[2] === state.main; });
    subBox.hidden = !state.main || gs.length < 2;
    subBox.innerHTML = subBox.hidden ? '' : '<button type="button" data-g="" aria-pressed="' + String(!state.sub) + '">Vse</button>' +
      gs.map(function (g) { return '<button type="button" data-g="' + g[0] + '" aria-pressed="' + String(state.sub === g[0]) + '">' + esc(g[1]) + '</button>'; }).join('');
  }
  subBox.addEventListener('click', function (ev) {
    var b = ev.target.closest('button[data-g]');
    if (!b) return;
    state.sub = b.dataset.g;
    subBox.querySelectorAll('button').forEach(function (x) { x.setAttribute('aria-pressed', String(x === b)); });
    run();
  });
  var mbtns = Array.prototype.slice.call(document.querySelectorAll('#rmain [data-m]'));
  function setMain(m) {
    state.main = m;
    state.sub = '';
    mbtns.forEach(function (x) { x.setAttribute('aria-pressed', String(x.dataset.m === m)); });
    buildSub();
  }
  mbtns.forEach(function (b) { b.addEventListener('click', function () { setMain(b.dataset.m); run(); }); });
  var modeBtns = Array.prototype.slice.call(document.querySelectorAll('#rmode [data-mode]'));
  modeBtns.forEach(function (b) {
    b.addEventListener('click', function () {
      state.mode = b.dataset.mode;
      modeBtns.forEach(function (x) { x.setAttribute('aria-pressed', String(x === b)); });
      run();
      writeHash();
    });
  });
  [['rsock', 'sock'], ['rsort', 'sort']].forEach(function (p) {
    document.getElementById(p[0]).addEventListener('change', function (ev) { state[p[1]] = ev.target.value; run(); });
  });
  var req = document.getElementById('rreq');
  req.addEventListener('input', function () { state.req = req.value; run(); });
  [['rused', 'used'], ['rs14', 's14']].forEach(function (p) {
    var el = document.getElementById(p[0]);
    el.addEventListener('change', function () { state[p[1]] = el.checked; run(); });
  });

  // #r=Ber,2 Ist&m=make: povezava z izbranimi runami (npr. iz wikija predmetov)
  function writeHash() {
    if (!history.replaceState) return;
    var h = haveAny() ? '#r=' + encodeURIComponent(haveText()) + (state.mode !== 'any' ? '&m=' + state.mode : '') : '';
    history.replaceState(null, '', location.pathname + h);
  }
  function fromHash() {
    var m = /[#&]r=([^&]*)/.exec(location.hash);
    if (!m) return;
    var text = decodeURIComponent(m[1]);
    state.have = parseHave(text).have;
    haveInput.value = haveText();
    var mm = /[#&]m=(any|all|make|one)/.exec(location.hash);
    if (mm) {
      state.mode = mm[1];
      modeBtns.forEach(function (x) { x.setAttribute('aria-pressed', String(x.dataset.mode === state.mode)); });
    }
    paintPalette();
  }
  window.addEventListener('hashchange', function () { fromHash(); run(); });

  try { S14 = JSON.parse(document.getElementById('rw-s14').textContent); } catch (err) { S14 = {}; }
  Promise.all([
    fetch('assets/items.json').then(function (r) { return r.json(); }),
    new Promise(function (res) { window.PD2.tips(res); })
  ]).then(function (v) {
    prepare(v[0], v[1]);
    buildPalette();
    fromHash();
    run();
  }).catch(function () {
    count.textContent = 'Runewordov ni bilo mogoče naložiti. Osveži stran.';
  });
})();
