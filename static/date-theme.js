// Lịch chọn ngày tiếng Việt; giữ input và giá trị ISO cho API hiện có.
(() => {
  const fields = new Map();
  let active = null, view, focusDate;
  const popup = document.createElement('div');
  popup.className = 'ictu-calendar'; popup.hidden = true;
  popup.id = 'ictu-calendar'; popup.setAttribute('role', 'dialog'); popup.setAttribute('aria-label', 'Chọn ngày');
  document.body.append(popup);
  const iso = d => `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
  const parse = v => /^\d{4}-\d{2}-\d{2}$/.test(v) ? new Date(Number(v.slice(0,4)), Number(v.slice(5,7))-1, Number(v.slice(8,10))) : null;
  const allowed = d => (!active.min || iso(d) >= active.min) && (!active.max || iso(d) <= active.max);
  function sync(input) {
    const b = fields.get(input); if (!b) return;
    const d = parse(input.value);
    b.querySelector('span').textContent = d ? d.toLocaleDateString('vi-VN') : (input.getAttribute('aria-label') || 'Chọn ngày');
    b.disabled = input.disabled || input.readOnly;
    b.setAttribute('aria-label', `${input.getAttribute('aria-label') || 'Ngày'}: ${d ? d.toLocaleDateString('vi-VN') : 'chưa chọn'}`);
    b.setAttribute('aria-required', String(input.required));
  }
  function close(restore = false) {
    const b = fields.get(active); b?.setAttribute('aria-expanded','false');
    popup.hidden = true; active = null; if (restore) b?.focus();
  }
  function position() {
    if (!active) return;
    const r = fields.get(active).getBoundingClientRect();
    popup.style.width = `${Math.min(320, innerWidth-16)}px`;
    popup.style.left = `${Math.max(8,Math.min(r.left,innerWidth-popup.offsetWidth-8))}px`;
    popup.style.maxHeight = `${innerHeight-16}px`;
    popup.style.top = `${Math.max(8, r.bottom+8+popup.offsetHeight<=innerHeight ? r.bottom+8 : r.top-popup.offsetHeight-8)}px`;
  }
  function choose(d) {
    if (!allowed(d)) return;
    const input = active; input.value = iso(d); sync(input); close(true);
    input.dispatchEvent(new Event('input',{bubbles:true})); input.dispatchEvent(new Event('change',{bubbles:true}));
  }
  function render(focus = false) {
    popup.replaceChildren();
    const head = document.createElement('div'); head.className='ictu-calendar-head';
    const prev = document.createElement('button'), next = document.createElement('button'), title = document.createElement('strong');
    for (const [b, text, label, delta] of [[prev,'‹','Tháng trước',-1],[next,'›','Tháng sau',1]]) {
      b.type='button'; b.textContent=text; b.setAttribute('aria-label',label);
      b.onclick=()=>{view=new Date(view.getFullYear(),view.getMonth()+delta,1);focusDate=new Date(view);render();b===prev?popup.querySelector('button').focus():popup.querySelectorAll('.ictu-calendar-head button')[1].focus();};
    }
    title.textContent=`Tháng ${view.getMonth()+1}, ${view.getFullYear()}`; title.setAttribute('aria-live','polite');
    head.append(prev,title,next); popup.append(head);
    const week = document.createElement('div'); week.className='ictu-calendar-week';
    for(const name of ['T2','T3','T4','T5','T6','T7','CN']) {const el=document.createElement('span');el.textContent=name;week.append(el);}
    popup.append(week);
    const grid=document.createElement('div');grid.className='ictu-calendar-grid';
    const first=new Date(view.getFullYear(),view.getMonth(),1), offset=(first.getDay()+6)%7;
    const today=iso(new Date());
    for(let i=0;i<42;i++) {
      const d=new Date(view.getFullYear(),view.getMonth(),i-offset+1), key=iso(d);
      const b=document.createElement('button');b.type='button';b.textContent=d.getDate();b.dataset.date=key;
      b.setAttribute('aria-label',d.toLocaleDateString('vi-VN',{weekday:'long',day:'numeric',month:'long',year:'numeric'}));
      b.disabled=!allowed(d);b.tabIndex=key===iso(focusDate)?0:-1;
      if(d.getMonth()!==view.getMonth())b.classList.add('other-month');
      if(key===today){b.classList.add('today');b.setAttribute('aria-current','date');}
      if(key===active.value){b.classList.add('selected');b.setAttribute('aria-pressed','true');}
      b.onclick=()=>choose(d);grid.append(b);
    }
    popup.append(grid);
    const footer=document.createElement('div');footer.className='ictu-calendar-footer';
    const clear=document.createElement('button'), now=document.createElement('button');
    clear.type=now.type='button';clear.textContent='Xóa ngày';now.textContent='Hôm nay';now.disabled=!allowed(new Date());
    clear.onclick=()=>{const input=active;input.value='';sync(input);close(true);input.dispatchEvent(new Event('input',{bubbles:true}));input.dispatchEvent(new Event('change',{bubbles:true}));};
    now.onclick=()=>choose(new Date());footer.append(clear,now);popup.append(footer);position();
    if(focus)popup.querySelector(`[data-date="${iso(focusDate)}"]:not(:disabled)`)?.focus();
  }
  function open(input) {
    if(input.disabled||input.readOnly)return;
    close();active=input;focusDate=parse(input.value)||new Date();
    if(input.min && iso(focusDate)<input.min)focusDate=parse(input.min);
    if(input.max && iso(focusDate)>input.max)focusDate=parse(input.max);
    view=new Date(focusDate.getFullYear(),focusDate.getMonth(),1);
    fields.get(input).setAttribute('aria-expanded','true');popup.hidden=false;render(true);
  }
  function enhance(input) {
    if(fields.has(input))return;
    const wrap=document.createElement('div');wrap.className='ictu-date';
    const b=document.createElement('button');b.type='button';b.className='ictu-date-trigger';
    b.setAttribute('aria-haspopup','dialog');b.setAttribute('aria-controls',popup.id);b.setAttribute('aria-expanded','false');
    const text=document.createElement('span'),icon=document.createElement('span');icon.className='ictu-date-icon';icon.setAttribute('aria-hidden','true');icon.textContent='▦';b.append(text,icon);
    input.before(wrap);wrap.append(input,b);input.classList.add('ictu-date-native');input.tabIndex=-1;input.setAttribute('aria-hidden','true');fields.set(input,b);
    const descriptor=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value');
    Object.defineProperty(input,'value',{configurable:true,get(){return descriptor.get.call(this);},set(v){descriptor.set.call(this,v);sync(this);}});
    input.addEventListener('change',()=>sync(input));input.addEventListener('invalid',()=>b.focus());
    b.onclick=()=>active===input?close():open(input);b.onkeydown=e=>{if(e.key==='ArrowDown'){e.preventDefault();open(input);}};sync(input);
  }
  popup.addEventListener('keydown',e=>{
    if(e.key==='Escape'){e.preventDefault();close(true);return;}
    if(e.key==='Tab') {
      const list=[...popup.querySelectorAll('button:not(:disabled)')].filter(b=>b.tabIndex>=0);
      const index=list.indexOf(document.activeElement);
      if(e.shiftKey&&index===0){e.preventDefault();list.at(-1)?.focus();}
      else if(!e.shiftKey&&index===list.length-1){e.preventDefault();list[0]?.focus();}
      return;
    }
    const el=e.target.closest('[data-date]');if(!el)return;
    const d=parse(el.dataset.date), moves={ArrowLeft:-1,ArrowRight:1,ArrowUp:-7,ArrowDown:7};
    if(e.key in moves)d.setDate(d.getDate()+moves[e.key]);
    else if(e.key==='PageUp'||e.key==='PageDown'){const day=d.getDate();d.setDate(1);d.setMonth(d.getMonth()+(e.key==='PageUp'?-1:1));d.setDate(Math.min(day,new Date(d.getFullYear(),d.getMonth()+1,0).getDate()));}
    else if(e.key==='Home')d.setDate(d.getDate()-(d.getDay()+6)%7);
    else if(e.key==='End')d.setDate(d.getDate()+6-(d.getDay()+6)%7);
    else return;
    e.preventDefault();if(!allowed(d))return;focusDate=d;view=new Date(d.getFullYear(),d.getMonth(),1);render(true);
  });
  document.addEventListener('pointerdown',e=>{if(active&&!popup.contains(e.target)&&!fields.get(active).contains(e.target))close();});
  document.addEventListener('focusin',e=>{if(active&&!popup.contains(e.target)&&e.target!==fields.get(active))close();});
  addEventListener('resize',()=>close());document.addEventListener('scroll',e=>{if(active&&!popup.contains(e.target))close();},true);
  document.addEventListener('reset',()=>setTimeout(()=>fields.forEach((_,input)=>sync(input)),0));
  document.querySelectorAll('input[type="date"]').forEach(enhance);
  new MutationObserver(records=>{
    for(const r of records){
      if(popup.contains(r.target))continue;
      for(const n of r.addedNodes||[]){if(n.nodeType!==1)continue;if(n.matches('input[type="date"]'))enhance(n);n.querySelectorAll('input[type="date"]').forEach(enhance);}
      if(fields.has(r.target))sync(r.target);
    }
    for(const [input]of fields)if(!input.isConnected){if(active===input)close();fields.delete(input);}
  }).observe(document.body,{subtree:true,childList:true,attributes:true,attributeFilter:['value','disabled','readonly','min','max','required']});
})();
