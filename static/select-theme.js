// Giao diện chọn thống nhất; select gốc vẫn giữ giá trị và sự kiện nghiệp vụ.
(() => {
  const controls = new Map();
  let active = null, cursor = -1, search = '', searchTime = 0, serial = 0;
  const menu = document.createElement('div');
  menu.className = 'ictu-select-menu';
  menu.id = 'ictu-select-menu';
  menu.setAttribute('role', 'listbox');
  menu.hidden = true;
  document.body.append(menu);
  const available = s => [...s.options].map((o, i) => ({o, i})).filter(({o}) => !o.disabled && !o.parentElement.disabled && !o.hidden);
  function sync(s) {
    const c = controls.get(s);
    if (!c) return;
    c.label.textContent = s.selectedOptions[0]?.textContent || 'Chọn lựa chọn';
    c.button.disabled = s.disabled;
    c.button.setAttribute('aria-label', `${s.getAttribute('aria-label') || 'Lựa chọn'}: ${c.label.textContent}`);
    c.button.setAttribute('aria-required', String(s.required));
  }
  function close() {
    if (active) {
      const b = controls.get(active)?.button;
      b?.setAttribute('aria-expanded', 'false');
      b?.removeAttribute('aria-activedescendant');
    }
    active = null; menu.hidden = true; menu.replaceChildren();
  }
  function position() {
    if (!active) return;
    const b = controls.get(active).button, r = b.getBoundingClientRect();
    const below = innerHeight - r.bottom - 12, above = r.top - 12;
    const space = below >= Math.min(260, menu.scrollHeight) || below >= above ? below : above;
    menu.style.width = `${Math.min(r.width, innerWidth - 16)}px`;
    menu.style.left = `${Math.max(8, Math.min(r.left, innerWidth - r.width - 8))}px`;
    menu.style.maxHeight = `${Math.max(64, Math.min(300, space - 6))}px`;
    menu.style.top = `${space === below ? r.bottom + 6 : Math.max(8, r.top - menu.offsetHeight - 6)}px`;
  }
  function highlight() {
    [...menu.children].forEach(el => {
      const on = Number(el.dataset.index) === cursor;
      el.classList.toggle('is-active', on);
      if (on) {
        controls.get(active).button.setAttribute('aria-activedescendant', el.id);
        el.scrollIntoView({block: 'nearest'});
      }
    });
  }
  function render() {
    menu.replaceChildren();
    [...active.options].forEach((o, i) => {
      if (o.hidden) return;
      const el = document.createElement('div');
      el.id = `ictu-option-${i}`; el.dataset.index = i;
      el.className = 'ictu-select-option'; el.setAttribute('role', 'option');
      el.setAttribute('aria-selected', String(i === active.selectedIndex));
      el.setAttribute('aria-disabled', String(o.disabled || !!o.parentElement.disabled));
      el.textContent = o.textContent;
      if (o.disabled || o.parentElement.disabled) el.classList.add('is-disabled');
      menu.append(el);
    });
    if (!menu.children.length) {
      const empty = document.createElement('div'); empty.className = 'ictu-select-empty';
      empty.textContent = 'Chưa có lựa chọn'; menu.append(empty);
    }
    position(); highlight();
  }
  function open(s) {
    if (s.disabled) return;
    close(); active = s; sync(s);
    cursor = available(s).some(x => x.i === s.selectedIndex) ? s.selectedIndex : (available(s)[0]?.i ?? -1);
    controls.get(s).button.setAttribute('aria-expanded', 'true');
    menu.hidden = false; render();
  }
  function choose(i) {
    if (!active || !available(active).some(x => x.i === i)) return;
    const s = active, b = controls.get(s).button;
    s.selectedIndex = i; sync(s); close(); b.focus();
    s.dispatchEvent(new Event('input', {bubbles: true}));
    s.dispatchEvent(new Event('change', {bubbles: true}));
  }
  function enhance(s) {
    if (controls.has(s) || s.multiple || s.size > 1) return;
    const wrap = document.createElement('div'); wrap.className = 'ictu-select';
    const button = document.createElement('button'); button.type = 'button';
    button.className = 'ictu-select-trigger'; button.setAttribute('role', 'combobox');
    button.setAttribute('aria-haspopup', 'listbox'); button.setAttribute('aria-expanded', 'false');
    button.setAttribute('aria-controls', menu.id); button.id = `ictu-select-${++serial}`;
    const label = document.createElement('span'); label.className = 'ictu-select-label';
    const arrow = document.createElement('span'); arrow.className = 'ictu-select-arrow'; arrow.setAttribute('aria-hidden', 'true');
    button.append(label, arrow); s.before(wrap); wrap.append(s, button);
    s.classList.add('ictu-select-native'); s.tabIndex = -1; s.setAttribute('aria-hidden', 'true');
    controls.set(s, {button, label, wrap});
    // Đồng bộ cả khi mã nghiệp vụ gán trực tiếp value/selectedIndex.
    for (const prop of ['value', 'selectedIndex']) {
      const d = Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, prop);
      Object.defineProperty(s, prop, {configurable: true, get() {return d.get.call(this);}, set(v) {d.set.call(this, v); sync(this);}});
    }
    s.addEventListener('change', () => sync(s));
    s.addEventListener('invalid', () => button.focus());
    button.addEventListener('click', () => active === s ? close() : open(s));
    button.addEventListener('keydown', e => {
      if (e.key === 'Tab') {close(); return;}
      if (e.key === 'Escape') {close(); e.preventDefault(); return;}
      if (['ArrowDown', 'ArrowUp', 'Home', 'End', 'Enter', ' '].includes(e.key)) {
        e.preventDefault();
        if (active !== s) {open(s); return;}
        if (e.key === 'Enter' || e.key === ' ') {choose(cursor); return;}
        const list = available(s), n = list.findIndex(x => x.i === cursor);
        cursor = list[e.key === 'Home' ? 0 : e.key === 'End' ? list.length - 1 : Math.max(0, Math.min(list.length - 1, n + (e.key === 'ArrowDown' ? 1 : -1)))]?.i ?? -1;
        highlight();
      } else if (e.key.length === 1 && !e.ctrlKey && !e.metaKey && !e.altKey) {
        e.preventDefault(); if (active !== s) open(s);
        search = Date.now() - searchTime > 700 ? e.key : search + e.key; searchTime = Date.now();
        const match = available(s).find(({o}) => o.textContent.trim().toLocaleLowerCase('vi').startsWith(search.toLocaleLowerCase('vi')));
        if (match) {cursor = match.i; highlight();}
      }
    });
    sync(s);
  }
  menu.addEventListener('pointerdown', e => e.preventDefault());
  menu.addEventListener('click', e => {const el = e.target.closest('[data-index]'); if (el) choose(Number(el.dataset.index));});
  document.addEventListener('pointerdown', e => {
    if (active && !menu.contains(e.target) && !controls.get(active).wrap.contains(e.target)) close();
  });
  document.addEventListener('focusin', e => {
    if (active && !controls.get(active).wrap.contains(e.target)) close();
  });
  addEventListener('resize', close);
  document.addEventListener('scroll', e => {if (active && !menu.contains(e.target)) close();}, true);
  document.addEventListener('reset', () => setTimeout(() => controls.forEach((_, s) => sync(s)), 0));
  document.querySelectorAll('select').forEach(enhance);
  const observer = new MutationObserver(records => {
    let rerender = false;
    for (const r of records) {
      if (r.target === menu || menu.contains(r.target)) continue;
      if (r.type === 'childList') for (const n of r.addedNodes) {
        if (n.nodeType !== 1) continue;
        if (n.matches('select')) enhance(n);
        n.querySelectorAll('select').forEach(enhance);
      }
      const s = r.target.closest?.('select');
      if (s && controls.has(s)) {sync(s); if (active === s) rerender = true;}
    }
    for (const [s] of controls) if (!s.isConnected) {if (active === s) close(); controls.delete(s);}
    if (rerender) {if (active.disabled) close(); else render();}
  });
  observer.observe(document.body, {subtree: true, childList: true, attributes: true, attributeFilter: ['disabled', 'selected', 'label', 'hidden', 'required'], characterData: true});
})();
