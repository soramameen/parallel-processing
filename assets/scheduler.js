/* 配分戦略シミュレータ — バッチ生成・貪欲スケジュール・ガントチャート描画。
   レッスン間で再利用する共通コンポーネント（0003 で初出）。 */
const Scheduler = (() => {
  const strategies = {
    block: (n, size) => {
      const batches = [];
      for (let i = 0; i < n; i += size) {
        batches.push(range(i, Math.min(i + size, n)));
      }
      return batches;
    },
    reversed: (n, size) => {
      const idx = range(0, n).reverse();
      const batches = [];
      for (let i = 0; i < n; i += size) {
        batches.push(idx.slice(i, i + size));
      }
      return batches;
    },
    interleave: (n, size) => {
      const k = Math.ceil(n / size);
      const batches = [];
      for (let b = 0; b < k; b++) {
        const batch = [];
        for (let i = b; i < n; i += k) batch.push(i);
        batches.push(batch);
      }
      return batches;
    },
  };

  function range(a, b) {
    return Array.from({ length: b - a }, (_, i) => a + i);
  }

  /* imap_unordered の理想化: 空いた worker が次のバッチを順に取る。
     コアは均質・競合なしという仮定を置いている点が実測との差になる。 */
  function simulate(batches, weights, workers) {
    const free = Array(workers).fill(0);
    const tasks = [];
    for (const [bi, batch] of batches.entries()) {
      const w = free.indexOf(Math.min(...free));
      const dur = batch.reduce((s, i) => s + weights[i], 0);
      tasks.push({ worker: w, start: free[w], end: free[w] + dur, batch: bi });
      free[w] += dur;
    }
    const makespan = Math.max(...free);
    const busy = free.reduce((a, b) => a + b, 0);
    return { tasks, makespan, busy, idle: 1 - busy / (workers * makespan) };
  }

  function renderGantt(el, result, workers, palette) {
    const W = 640, rowH = 34, pad = 44, H = workers * rowH + 30;
    const sx = (W - pad - 10) / result.makespan;
    let s = `<svg viewBox="0 0 ${W} ${H}" role="img">`;
    for (let w = 0; w < workers; w++) {
      const y = 10 + w * rowH;
      s += `<text x="0" y="${y + 17}" font-size="12" fill="var(--ink-soft)">w${w}</text>`;
      s += `<rect x="${pad}" y="${y}" width="${W - pad - 10}" height="${rowH - 10}"
             fill="none" stroke="var(--line)"/>`;
    }
    for (const t of result.tasks) {
      const y = 10 + t.worker * rowH;
      s += `<rect x="${pad + t.start * sx}" y="${y}" width="${(t.end - t.start) * sx}"
             height="${rowH - 10}" fill="${palette[t.batch % palette.length]}"
             stroke="var(--bg)" stroke-width="1.5"><title>バッチ${t.batch}: ${t.end - t.start}</title></rect>`;
      if ((t.end - t.start) * sx > 22) {
        s += `<text x="${pad + (t.start + t.end) / 2 * sx}" y="${y + 16}" font-size="11"
               text-anchor="middle" fill="var(--bg)">b${t.batch}</text>`;
      }
    }
    s += `<line x1="${pad + result.makespan * sx}" y1="6" x2="${pad + result.makespan * sx}"
          y2="${H - 24}" stroke="var(--ng)" stroke-dasharray="4 3"/>`;
    s += `<text x="${pad + result.makespan * sx}" y="${H - 8}" font-size="12"
          text-anchor="end" fill="var(--ng)">完了 = ${result.makespan}</text></svg>`;
    el.innerHTML = s;
  }

  /* 頂点列を重み比例の幅で1本の帯として描く（バッチ構成の可視化） */
  function renderStrip(el, batches, weights, palette) {
    const total = weights.reduce((a, b) => a + b, 0);
    const W = 640, H = 46;
    let s = `<svg viewBox="0 0 ${W} ${H}" role="img">`;
    const owner = [];
    for (const [bi, batch] of batches.entries()) for (const i of batch) owner[i] = bi;
    let x = 0;
    for (let i = 0; i < weights.length; i++) {
      const w = (weights[i] / total) * W;
      s += `<rect x="${x}" y="4" width="${Math.max(w - 1.2, 0.8)}" height="30"
             fill="${palette[owner[i] % palette.length]}"><title>頂点${i}（重さ${weights[i]}）→ バッチ${owner[i]}</title></rect>`;
      x += w;
    }
    s += `<text x="0" y="${H - 2}" font-size="11" fill="var(--ink-soft)">← 縮退順序の先頭（軽い）</text>`;
    s += `<text x="${W}" y="${H - 2}" font-size="11" text-anchor="end" fill="var(--ink-soft)">末尾（重い）→</text></svg>`;
    el.innerHTML = s;
  }

  return { strategies, simulate, renderGantt, renderStrip };
})();
