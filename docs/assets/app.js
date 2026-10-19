(function () {
  if ('scrollRestoration' in history) history.scrollRestoration = 'manual';
  // Odpri build iz povezave (#b-<id>)
  function openFromHash() {
    var id = location.hash.slice(1);
    if (!id) return;
    var el = document.getElementById(id);
    if (el && el.tagName === 'DETAILS') {
      el.open = true;
      el.scrollIntoView({ block: 'start' });
    }
  }
  window.addEventListener('hashchange', openFromHash);
  window.addEventListener('load', function () { setTimeout(openFromHash, 30); });

  // Ko odpreš build, se posodobi naslov v vrstici brskalnika
  document.querySelectorAll('details.build').forEach(function (d) {
    d.addEventListener('toggle', function () {
      if (d.open && history.replaceState) history.replaceState(null, '', '#' + d.id);
    });
  });

  // Filter buildov na strani razreda
  var buttons = Array.prototype.slice.call(document.querySelectorAll('.filters button'));
  var count = document.getElementById('fcount');
  function applyFilter(f) {
    var shown = 0;
    document.querySelectorAll('details.build').forEach(function (d) {
      var ok = f === 'all' || d.dataset.tier === f || (f === 'starter' && d.dataset.starter === '1') ||
        (f === 'guide' && d.dataset.guide === '1');
      d.hidden = !ok;
      if (ok) shown++;
    });
    buttons.forEach(function (b) { b.setAttribute('aria-pressed', String(b.dataset.f === f)); });
    if (count) count.textContent = shown + ' buildov';
  }
  buttons.forEach(function (b) { b.addEventListener('click', function () { applyFilter(b.dataset.f); }); });
  if (buttons.length) applyFilter('all');


  // ---------- Tooltipi: statsi predmetov in sinergije skillov ----------
  var tips = null, pending = null;
  var box = document.createElement('div');
  box.className = 'tt';
  box.id = 'tt';
  box.setAttribute('role', 'tooltip');
  box.hidden = true;
  document.body.appendChild(box);
  var current = null, pinned = false;

  function loadTips(cb) {
    if (tips) return cb();
    pending = cb;
    if (loadTips.started) return;
    loadTips.started = true;
    fetch('assets/tips.json').then(function (r) { return r.json(); }).then(function (j) {
      tips = j;
      if (pending) pending();
    }).catch(function () { loadTips.started = false; });
  }

  function esc(s) { var d = document.createElement('div'); d.textContent = s; return d.innerHTML; }

  function fill(el) {
    var key = el.getAttribute('data-tip');
    var h = tips && tips[key];
    if (!h) return false;
    var extra = '';
    if (el.dataset.eth) extra += '<div class="tt-inst tt-eth">Ethereal</div>';
    if (el.dataset.sock) extra += '<div class="tt-inst">Socketed: ' + esc(el.dataset.sock) + '</div>';
    if (el.dataset.corr) extra += '<div class="tt-inst tt-corr">Corrupted: ' + esc(el.dataset.corr) + '</div>';
    box.innerHTML = h + extra;
    if (el.dataset.skill) {
      var planner = el.closest('.planner');
      box.querySelectorAll('[data-syn]').forEach(function (d) {
        if (!planner || !d.dataset.syn) return;
        var chip = planner.querySelector('.sk[data-skill="' + d.dataset.syn + '"]');
        var pts = chip ? Number(chip.dataset.pts) : 0;
        var tag = document.createElement('span');
        tag.className = 'tt-pts';
        tag.textContent = pts ? ' · v buildu: ' + pts : ' · v buildu: 0';
        d.appendChild(tag);
        if (pts) d.classList.add('on');
      });
    }
    return true;
  }

  function place(el) {
    var r = el.getBoundingClientRect();
    var vw = document.documentElement.clientWidth, vh = window.innerHeight;
    box.style.left = '0px';
    box.style.top = '0px';
    var bw = box.offsetWidth, bh = box.offsetHeight;
    var left = Math.min(Math.max(8, r.left + r.width / 2 - bw / 2), vw - bw - 8);
    var top = r.bottom + 8;
    if (top + bh > vh - 8 && r.top - bh - 8 > 8) top = r.top - bh - 8;
    if (top + bh > vh - 8) top = Math.max(8, vh - bh - 8);
    box.style.left = Math.round(left) + 'px';
    box.style.top = Math.round(top) + 'px';
  }

  function show(el, pin) {
    loadTips(function () {
      if (!fill(el)) return;
      current = el;
      pinned = !!pin;
      box.classList.toggle('pinned', pinned);
      box.hidden = false;
      el.setAttribute('aria-describedby', 'tt');
      place(el);
    });
  }

  function hide() {
    if (current) current.removeAttribute('aria-describedby');
    box.hidden = true;
    current = null;
    pinned = false;
  }

  document.addEventListener('mouseover', function (ev) {
    if (pinned) return;
    var el = ev.target.closest && ev.target.closest('[data-tip]');
    if (el && el !== current) show(el, false);
  });
  document.addEventListener('mouseout', function (ev) {
    if (pinned || !current) return;
    var to = ev.relatedTarget;
    if (!to || !current.contains(to)) {
      var el = ev.target.closest && ev.target.closest('[data-tip]');
      if (el === current) hide();
    }
  });
  document.addEventListener('click', function (ev) {
    var el = ev.target.closest && ev.target.closest('[data-tip]');
    if (el) {
      // v vodičih je ime predmeta del oznake s kljukico: klik naj jo še vedno obkljuka
      if (!el.closest('label')) ev.preventDefault();
      if (pinned && current === el) hide(); else show(el, true);
      return;
    }
    // klik na ime v oznaki sproži še klik na kljukico: ta naj tooltipa ne zapre
    var lab = ev.target.matches && ev.target.matches('input') && ev.target.closest('label');
    if (lab && current && lab.contains(current)) return;
    if (!box.contains(ev.target)) hide();
  });
  document.addEventListener('focusin', function (ev) {
    var el = ev.target.closest && ev.target.closest('[data-tip]');
    if (el && !pinned) show(el, false);
  });
  document.addEventListener('focusout', function () { if (!pinned) hide(); });
  document.addEventListener('keydown', function (ev) {
    if (ev.key === 'Escape') hide();
    if ((ev.key === 'Enter' || ev.key === ' ') && ev.target.matches && ev.target.matches('[data-tip]')) {
      ev.preventDefault();
      show(ev.target, true);
    }
  });
  window.addEventListener('scroll', function () { if (current && !pinned) hide(); else if (current) place(current); }, { passive: true });
  window.addEventListener('resize', function () { if (current) place(current); });
  // naloži tooltipe vnaprej, ko je stran mirna
  setTimeout(function () { loadTips(function () {}); }, 1200);

  // Kljukice v naših vodičih (druid plan ima svojo skripto)
  if (document.body.classList.contains('page-druid')) return;
  var KEY = 'pd2s14:' + location.pathname;
  var state = {};
  try { state = JSON.parse(localStorage.getItem(KEY) || '{}') || {}; } catch (e) { state = {}; }
  function save() { try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) {} }
  function counts() {
    document.querySelectorAll('.phase').forEach(function (ph) {
      var c = ph.querySelector('.count');
      if (!c) return;
      var boxes = ph.querySelectorAll('input[type="checkbox"]');
      var done = Array.prototype.filter.call(boxes, function (b) { return b.checked; }).length;
      c.textContent = done + ' / ' + boxes.length + ' kosov';
      c.classList.toggle('done', boxes.length > 0 && done === boxes.length);
    });
  }
  document.querySelectorAll('.g input[type="checkbox"][id]').forEach(function (b) {
    b.checked = !!state[b.id];
    b.addEventListener('change', function () {
      if (b.checked) state[b.id] = true; else delete state[b.id];
      save(); counts();
    });
  });
  counts();
})();
