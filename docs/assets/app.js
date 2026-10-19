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
