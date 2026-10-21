// Tier liste: zavihki, filter po razredu ter izbira bossa in težavnosti
(function () {
  var tabs = Array.prototype.slice.call(document.querySelectorAll('.ttabs [role="tab"]'));
  if (!tabs.length) return;
  var state = { cls: '', boss: 'dclone', lvl: 't0' };

  function showTab(key, push) {
    var tab = document.getElementById('tab-' + key) || tabs[0];
    tabs.forEach(function (t) {
      var on = t === tab;
      t.setAttribute('aria-selected', String(on));
      t.tabIndex = on ? 0 : -1;
      document.getElementById(t.getAttribute('aria-controls')).hidden = !on;
    });
    if (push && history.replaceState) history.replaceState(null, '', '#' + tab.id.slice(4));
  }
  tabs.forEach(function (t, i) {
    t.addEventListener('click', function () { showTab(t.id.slice(4), true); });
    t.addEventListener('keydown', function (ev) {
      var d = ev.key === 'ArrowRight' ? 1 : ev.key === 'ArrowLeft' ? -1 : 0;
      if (!d) return;
      var n = tabs[(i + d + tabs.length) % tabs.length];
      n.focus();
      showTab(n.id.slice(4), true);
    });
  });

  // filter po razredu: skrije čipe drugih razredov in posodobi števce v vrsticah
  var dhBud = document.getElementById('dhbud'), dhFort = document.getElementById('dhfort'), dhCount = document.getElementById('dhcount');
  function applyClass() {
    document.querySelectorAll('.tchip, .dhc[data-c]').forEach(function (c) { c.hidden = !!state.cls && c.dataset.c !== state.cls; });
    var shown = 0;
    document.querySelectorAll('.dht tbody tr').forEach(function (r) {
      var hide = (!!state.cls && r.dataset.c !== state.cls) || (dhBud && dhBud.checked && Number(r.dataset.b) < 2) ||
        (dhFort && dhFort.checked && Number(r.dataset.f) < 2);
      r.hidden = hide;
      if (!hide) shown++;
    });
    if (dhCount) dhCount.textContent = shown + ' buildov';
    document.querySelectorAll('.trow').forEach(function (r) {
      var n = r.querySelectorAll('.tchip:not([hidden])').length;
      r.querySelector('.tcount').textContent = n;
      r.classList.toggle('empty', !n);
    });
  }
  function pressGroup(sel, attr, val) {
    document.querySelectorAll(sel + ' button').forEach(function (b) { b.setAttribute('aria-pressed', String(b.dataset[attr] === val)); });
  }
  document.querySelectorAll('.tcls button').forEach(function (b) {
    b.addEventListener('click', function () { state.cls = b.dataset.cls; pressGroup('.tcls', 'cls', state.cls); applyClass(); });
  });

  function applyBoss() {
    document.querySelectorAll('.bpanel').forEach(function (p) { p.hidden = p.dataset.boss !== state.boss || p.dataset.lvl !== state.lvl; });
    document.querySelectorAll('.dhboss').forEach(function (p) { p.hidden = p.dataset.boss !== state.boss; });
    var lvl = document.getElementById('blvl');
    if (lvl) lvl.hidden = state.boss === 'uber';
  }
  [dhBud, dhFort].forEach(function (el) { if (el) el.addEventListener('change', applyClass); });
  document.querySelectorAll('#bboss button').forEach(function (b) {
    b.addEventListener('click', function () { state.boss = b.dataset.boss; pressGroup('#bboss', 'boss', state.boss); applyBoss(); });
  });
  document.querySelectorAll('#blvl button').forEach(function (b) {
    b.addEventListener('click', function () { state.lvl = b.dataset.lvl; pressGroup('#blvl', 'lvl', state.lvl); applyBoss(); });
  });

  var start = location.hash.slice(1);
  if (start && document.getElementById('tab-' + start)) showTab(start, false);
  window.addEventListener('hashchange', function () {
    var k = location.hash.slice(1);
    if (document.getElementById('tab-' + k)) showTab(k, false);
  });
  document.querySelectorAll('.tnone').forEach(function (n) { n.remove(); });
  applyClass();
})();
