"""The front page's script: inline, so the page fetches nothing. Every run button works without it."""

JS = r"""
(() => {
  const root = document.documentElement;
  root.classList.add('js');
  const still = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const esc = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const seen = (el, fn, opts) => {
    if (!('IntersectionObserver' in window)) { fn(el); return; }
    const io = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) { fn(e.target); io.unobserve(e.target); } }), opts || {rootMargin: '0px 0px -10% 0px'});
    io.observe(el);
  };

  // --- reveals, spotlight, scroll progress, hero tilt ---------------------------------
  document.querySelectorAll('section:not(.hero) .wrap > *:not(.how):not(.grid):not(.chips)').forEach(el => {
    el.classList.add('reveal'); seen(el, t => t.classList.add('in'));
  });
  document.querySelectorAll('.chat, .bars').forEach(el => seen(el, t => t.classList.add('in'), {threshold: .35}));
  document.addEventListener('pointermove', e => {
    const el = e.target.closest && e.target.closest('.spot');
    if (!el) return;
    const r = el.getBoundingClientRect();
    el.style.setProperty('--mx', (e.clientX - r.left) + 'px');
    el.style.setProperty('--my', (e.clientY - r.top) + 'px');
  }, {passive: true});
  const machine = document.getElementById('machine');
  let ticking = false;
  const onScroll = () => {
    if (ticking) return; ticking = true;
    requestAnimationFrame(() => {
      const h = document.body.scrollHeight - innerHeight;
      root.style.setProperty('--p', h > 0 ? (scrollY / h).toFixed(4) : 0);
      if (machine && !still) {
        const t = Math.max(0, Math.min(1, scrollY / (innerHeight * .6)));
        machine.style.setProperty('--tilt', (16 * (1 - t)).toFixed(2) + 'deg');
        machine.style.setProperty('--sc', (.94 + .06 * t).toFixed(4));
      }
      ticking = false;
    });
  };
  addEventListener('scroll', onScroll, {passive: true}); onScroll();

  // --- count-ups ------------------------------------------------------------------------
  document.querySelectorAll('[data-count]').forEach(el => {
    const end = parseFloat(el.dataset.count);
    const node = el.firstChild;
    if (still || !isFinite(end) || !node || node.nodeType !== 3) return;
    node.nodeValue = '0';
    seen(el, () => {
      const t0 = performance.now(), dur = 1400;
      const step = now => {
        const k = Math.min(1, (now - t0) / dur), e = 1 - Math.pow(1 - k, 4);
        node.nodeValue = Math.round(end * e);
        if (k < 1) requestAnimationFrame(step);
      };
      requestAnimationFrame(step);
    }, {threshold: .6});
  });

  // --- the replay -----------------------------------------------------------------------
  const dataEl = document.getElementById('replay-data');
  if (machine && dataEl) {
    const R = JSON.parse(dataEl.textContent);
    const rows = {};
    machine.querySelectorAll('.row').forEach(r => { rows[r.dataset.field] = r; });
    const cells = [...machine.querySelectorAll('.strip i')];
    const ans = machine.querySelector('.answer'), aText = ans.querySelector('.a-text');
    const aKeys = ans.querySelector('.a-keys'), badge = ans.querySelector('.a-badge');
    const narr = machine.querySelector('.narr'), fixc = machine.querySelector('.fixcard');
    const replay = machine.querySelector('.replay');
    const verb = {destroy: 'wiped', drop: 'removed', nudge: 'nudged'};
    const tag = {'inert': 'Doesn’t matter ✓', 'load-bearing': 'Matters ✓',
                 'silent passthrough': 'Ignored ✗', 'phantom sensitivity': 'Leaks in ✗'};
    const bad = R.fields.find(f => f.defect);
    let token = 0, visible = false;
    const wait = async (ms, t) => {
      let left = ms;
      while (left > 0) { await sleep(40); if (t !== token) throw 0; if (visible && !document.hidden) left -= 40; }
    };
    const keys = k => k.map(([a, b]) => '<span><small>' + esc(a) + '</small>' + esc(b) + '</span>').join('');
    const setAnswer = (o, state, label) => {
      aText.textContent = o.answer; aKeys.innerHTML = keys(o.keys);
      ans.dataset.state = state; badge.textContent = label;
      ans.classList.remove('flash'); void ans.offsetWidth; ans.classList.add('flash');
    };
    const pip = f => { const r = rows[f.field]; const el = r && r.querySelector('.pips i[data-kind="' + f.kind + '"]'); if (el) el.className = f.moved ? 'm' : 's'; };
    const setTag = (row, v) => { row.dataset.verdict = v; row.querySelector('.row-tag').textContent = tag[v] || v; };
    const reset = () => {
      Object.values(rows).forEach(r => {
        r.className = 'row'; delete r.dataset.kind; delete r.dataset.verdict;
        r.querySelector('.val').textContent = r.dataset.orig; r.querySelector('.row-tag').textContent = '';
        r.querySelectorAll('.pips i').forEach(i => { i.className = ''; });
      });
      cells.forEach(c => { c.className = ''; });
      if (fixc) fixc.classList.remove('on', 'typing');
      setAnswer(R.baseline, 'base', 'Original answer');
    };
    const final = () => {
      reset();
      R.forks.forEach((f, i) => { cells[i].className = f.moved ? 'm' : 's'; pip(f); });
      R.fields.forEach(fl => setTag(rows[fl.name], (R.after && R.after.verdicts[fl.name]) || fl.verdict));
      if (R.after) {
        R.after.forks.forEach((f, i) => { if (cells[i]) cells[i].className = f.moved ? 'm' : 's'; pip(f); });
        if (bad) rows[bad.name].classList.add('fixed');
        setAnswer(R.after, 'right', 'Right · proven fix');
      }
      if (fixc) fixc.classList.add('on');
      narr.innerHTML = bad ? 'The policy was ignored. Nemotron fixed one line, and the proof run shows it is used now.' : '';
    };
    async function play() {
      const t = ++token;
      try {
        for (;;) {
          reset();
          narr.innerHTML = 'One real customer request, frozen once. Now Loadbearing makes <em>' + R.forks.length + ' copies</em> and breaks one input in each.';
          await wait(3000, t);
          for (const [i, f] of R.forks.entries()) {
            const row = rows[f.field], key = f.field === (bad && bad.name);
            Object.values(rows).forEach(r => r.classList.toggle('active', r === row));
            row.dataset.kind = f.kind; row.querySelector('.val').textContent = f.value;
            cells[i].className = 'on';
            narr.innerHTML = 'Copy ' + (i + 1) + ' of ' + R.forks.length + ': <b>' + esc(f.field) + '</b>&nbsp;' + verb[f.kind];
            await wait(f.moved || key ? 700 : 300, t);
            setAnswer(f, f.moved ? 'moved' : 'same', f.moved ? 'Answer changed' : 'Same decision');
            pip(f);
            cells[i].className = f.moved ? 'm' : 's';
            narr.innerHTML += f.moved ? ' <em class="m">→ the answer changed</em>' : (key ? ' <em class="r">→ the answer did not change</em>' : ' <em>→ same decision</em>');
            await wait(f.moved || key ? 1700 : 700, t);
            row.querySelector('.val').textContent = row.dataset.orig; delete row.dataset.kind;
          }
          Object.values(rows).forEach(r => r.classList.remove('active'));
          for (const fl of R.fields) { setTag(rows[fl.name], fl.verdict); await wait(160, t); }
          if (!bad) { narr.innerHTML = 'Every input does what it should.'; await wait(5000, t); continue; }
          rows[bad.name].classList.add('bad');
          setAnswer(R.baseline, 'wrong', 'Wrong answer');
          narr.innerHTML = '<b>' + esc(bad.name) + '</b>&nbsp;was wiped and removed, and the answer never moved. <em class="r">The bot never read it.</em>';
          await wait(4200, t);
          if (fixc && R.fix) {
            fixc.classList.add('on', 'typing');
            narr.innerHTML = 'Nemotron 3 Ultra reads the code, names the line, and writes the smallest fix.';
            await wait(3400, t);
          }
          if (R.after) {
            narr.innerHTML = 'Proof: a fresh copy of the same snapshot runs every test again.';
            cells.forEach(c => { c.className = ''; });
            await wait(500, t);
            Object.values(rows).forEach(r => r.querySelectorAll('.pips i').forEach(i => { i.className = ''; }));
            for (const [i, f] of R.after.forks.entries()) { if (cells[i]) cells[i].className = f.moved ? 'm' : 's'; pip(f); await wait(110, t); }
            rows[bad.name].classList.remove('bad');
            R.fields.forEach(fl => { const v = R.after.verdicts[fl.name]; if (v) setTag(rows[fl.name], v); });
            rows[bad.name].classList.add('fixed');
            setAnswer(R.after, 'right', 'Right · proven fix');
            narr.innerHTML = 'Now wiping <b>' + esc(bad.name) + '</b>&nbsp;changes the answer, and nothing else broke. <em class="m">Fixed, and proven.</em>';
            await wait(7000, t);
          }
        }
      } catch (e) { /* a newer replay took over */ }
    }
    if (still) { final(); }
    else {
      if ('IntersectionObserver' in window) {
        new IntersectionObserver(es => es.forEach(e => { visible = e.isIntersecting; }), {threshold: .25}).observe(machine);
      } else { visible = true; }
      machine.classList.add('played');
      replay.hidden = false;
      replay.addEventListener('click', () => play());
      play();
    }
  }

  // --- how it works: the figure follows the step in view --------------------------------
  const fig = document.querySelector('.how-fig');
  if (fig && !still && 'IntersectionObserver' in window && matchMedia('(min-width: 981px)').matches) {
    const how = document.querySelector('.how'), steps = [...document.querySelectorAll('.steps li')];
    how.classList.add('how-on');
    fig.querySelectorAll('.t-before svg path').forEach((p, i) => { p.style.transitionDelay = (i * 35) + 'ms'; });
    const io = new IntersectionObserver(es => es.forEach(e => {
      if (!e.isIntersecting) return;
      steps.forEach(s => s.classList.toggle('on', s === e.target));
      fig.dataset.step = e.target.dataset.step;
    }), {rootMargin: '-45% 0px -45% 0px'});
    steps.forEach(s => io.observe(s));
    fig.dataset.step = '1'; steps[0].classList.add('on');
  }
  document.querySelectorAll('.tree').forEach(t => { t.scrollLeft = t.scrollWidth; });

  // --- the cards: filters, fold, run in place -----------------------------------------
  const grid = document.querySelector('.grid');
  const more = document.querySelector('.more');
  const unfold = () => { if (grid) grid.classList.remove('folded'); if (more) more.remove(); };
  if (grid && more) { more.hidden = false; more.addEventListener('click', unfold); }
  document.querySelectorAll('.chip').forEach(chip => chip.addEventListener('click', () => {
    unfold();
    document.querySelectorAll('.chip').forEach(c => c.classList.toggle('on', c === chip));
    const d = chip.dataset.domain;
    document.querySelectorAll('.grid .card').forEach(card => { card.hidden = !!d && card.dataset.domain !== d; });
  }));

  const cls = v => v.startsWith('silent') ? 'silent' : 'phantom';
  function verdict(found, truth) {
    const fk = Object.keys(found), tk = Object.keys(truth);
    const same = fk.length === tk.length && tk.every(k => found[k] === truth[k]);
    if (same) return tk.length ? '<span class="ok">✓ Found the planted bug</span>' : '<span class="ok">✓ No bug, no false alarm</span>';
    const missed = tk.filter(k => found[k] !== truth[k]), extra = fk.filter(k => !(k in truth));
    const bits = [];
    if (missed.length) bits.push('missed ' + missed.join(', '));
    if (extra.length) bits.push('false alarm on ' + extra.join(', '));
    return '<span class="miss">✗ ' + esc(bits.join('; ')) + '</span>';
  }
  async function probe(action) {
    const res = await fetch(action + '?format=json', {method: 'POST', headers: {Accept: 'application/json'}});
    if (!res.ok) throw new Error('HTTP ' + res.status);
    return res.json();
  }
  document.querySelectorAll('form.run').forEach(form => form.addEventListener('submit', async ev => {
    const card = form.closest('.card');
    if (!card || !window.fetch || form.dataset.ran === '1') return;
    ev.preventDefault();
    await runCard(card);
  }));
  async function runCard(card) {
    const form = card.querySelector('form.run');
    if (!form || form.dataset.ran === '1') return;
    card.classList.add('running');
    const result = card.querySelector('.result');
    result.innerHTML = '';
    try {
      const data = await probe(form.action);
      const found = {};
      (data.verdicts || []).forEach(v => { if (v.defect) found[v.field] = v.verdict; });
      const truth = JSON.parse(card.dataset.truth || '{}');
      const n = Object.keys(found).length;
      const list = n
        ? '<p class="count">' + n + ' defect' + (n === 1 ? '' : 's') + ' found</p><ul class="found">' + Object.entries(found).map(([f, v]) => '<li><b>' + esc(f) + '</b> <span class="v ' + cls(v) + '">' + esc(v) + '</span></li>').join('') + '</ul>'
        : '<p class="muted">No defects found.</p>';
      const t = data.timing || {};
      const took = t.runs ? '<p class="muted">' + t.runs + ' runs in ' + (t.fork_wall_seconds || 0).toFixed(2) + ' s</p>' : '';
      result.innerHTML = verdict(found, truth) + list + took;
      card.classList.toggle('hit', result.querySelector('.ok') !== null);
      card.classList.toggle('missed', result.querySelector('.miss') !== null);
      card.classList.add('just'); setTimeout(() => card.classList.remove('just'), 800);
      const btn = form.querySelector('button');
      btn.textContent = 'Open the full report';
      btn.classList.add('ghost');
      form.dataset.ran = '1';
    } catch (err) {
      result.innerHTML = '<span class="miss">Could not run: ' + esc(err.message) + '</span>';
    } finally {
      card.classList.remove('running');
    }
  }

  const all = document.getElementById('runall');
  if (all && window.fetch) {
    all.hidden = false;
    const score = document.querySelector('.score');
    const C = 2 * Math.PI * 52;
    const ok = score.querySelector('.r-ok'), miss = score.querySelector('.r-miss');
    const num = score.querySelector('.ring-right'), text = score.querySelector('.score-text');
    all.addEventListener('click', async () => {
      unfold();
      document.querySelectorAll('.chip').forEach(c => c.classList.toggle('on', !c.dataset.domain));
      document.querySelectorAll('.grid .card').forEach(card => { card.hidden = false; });
      const cards = [...document.querySelectorAll('.grid .card')].filter(c => c.querySelector('form.run'));
      score.classList.add('on'); all.disabled = true; all.textContent = 'Running…';
      let done = 0, right = 0;
      const wrong = [], total = cards.length, started = performance.now();
      const draw = () => {
        const a = C * right / total, b = C * (done - right) / total;
        ok.style.strokeDasharray = a + ' ' + C;
        miss.style.strokeDasharray = b + ' ' + C;
        miss.style.strokeDashoffset = -a;
        num.textContent = right;
        text.innerHTML = done + ' of ' + total + ' run · ' + ((performance.now() - started) / 1000).toFixed(1) + ' s' +
          (wrong.length ? '<br><small>Not right: ' + wrong.map(esc).join(', ') + '</small>' : '');
      };
      const queue = cards.slice();
      const worker = async () => {
        while (queue.length) {
          const card = queue.shift();
          await runCard(card);
          done++;
          if (card.classList.contains('hit')) right++; else wrong.push(card.dataset.name);
          draw();
        }
      };
      draw();
      await Promise.all([worker(), worker(), worker(), worker()]);
      all.textContent = 'Done: ' + right + ' of ' + total + ' exactly right';
    });
  }

  // --- the terminal: types the commands, then really runs the probe -----------------------
  const term = document.getElementById('term');
  if (term && !still) {
    const body = term.querySelector('.t-body');
    const cmds = [...body.querySelectorAll('.t-cmd')].map(c => c.textContent);
    const action = term.dataset.run;
    body.innerHTML = '<span class="caret"></span>';
    seen(term, async () => {
      body.innerHTML = '';
      for (const c of cmds) {
        const line = document.createElement('span');
        line.className = 't-cmd'; body.appendChild(line);
        const caret = document.createElement('span'); caret.className = 'caret';
        for (let i = 1; i <= c.length; i++) { line.textContent = c.slice(0, i); line.appendChild(caret); await sleep(c.length > 40 ? 14 : 24); }
        caret.remove();
        await sleep(260);
      }
      if (!action || !window.fetch) return;
      const out = (html, k) => { const s = document.createElement('span'); s.className = k || 't-out'; s.innerHTML = html; body.appendChild(s); };
      try {
        const data = await probe(action);
        const t = data.timing || {};
        out('checkpoint · ' + (data.forks || []).length + ' copies · ' + (t.runs || 0) + ' runs in ' + (t.fork_wall_seconds || 0).toFixed(2) + ' s');
        for (const v of data.verdicts || []) {
          await sleep(120);
          const k = v.verdict.startsWith('silent') ? 'silent' : v.verdict.startsWith('phantom') ? 'phantom' : v.verdict === 'inert' ? 'inert' : 'lb';
          out('<b>' + esc(v.field.padEnd(14)) + '</b><span class="' + k + '">' + esc(v.verdict.toUpperCase()) + '</span>');
        }
        await sleep(200);
        const n = (data.verdicts || []).filter(v => v.defect).length;
        out('✓ ' + n + ' defect' + (n === 1 ? '' : 's') + ' found · ran live on this server, just now', 't-ok');
      } catch (e) { out('could not run here: ' + esc(e.message)); }
    }, {threshold: .5});
  }
})();
"""
