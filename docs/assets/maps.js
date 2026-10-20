// Mape: filter po elementu (označi mape brez imunitete na izbrani element)
(function () {
  var cards = Array.prototype.slice.call(document.querySelectorAll('details.mapc'));
  if (!cards.length) return;
  var buttons = Array.prototype.slice.call(document.querySelectorAll('[data-el]'));
  var hide = document.getElementById('hide-imm');
  var count = document.getElementById('mcount');
  var NAME = { phys: 'Physical', magic: 'Magic', fire: 'Fire', light: 'Lightning', cold: 'Cold', poison: 'Poison' };
  var el = '';
  try { el = localStorage.getItem('pd2s14:el') || ''; } catch (e) { el = ''; }

  function apply() {
    var ok = 0;
    cards.forEach(function (c) {
      var imm = (c.dataset.imm || '').split(' ');
      var bad = el && imm.indexOf(el) >= 0;
      c.classList.toggle('is-bad', !!bad);
      c.classList.toggle('is-ok', !!el && !bad);
      c.hidden = !!(bad && hide && hide.checked);
      var fit = c.querySelector('.fit');
      if (fit) fit.textContent = el ? (bad ? 'imuni na ' + NAME[el] : '✓') : '';
      if (!bad) ok++;
    });
    buttons.forEach(function (b) { b.setAttribute('aria-pressed', String(b.dataset.el === el)); });
    if (count) count.textContent = el ? ok + ' od ' + cards.length + ' map nima imunitete na ' + NAME[el] + '.' : '';
  }
  buttons.forEach(function (b) {
    b.addEventListener('click', function () {
      el = b.dataset.el;
      try { localStorage.setItem('pd2s14:el', el); } catch (e) {}
      apply();
    });
  });
  if (hide) hide.addEventListener('change', apply);
  apply();
})();
