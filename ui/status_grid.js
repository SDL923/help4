/* (1) 발행 현황 — pipeline / raw_data 격자
   data:   { tab, grid: {headers, rows}, selected: {kind, name, w} | null }
   이벤트: tab  → 'pipeline' | 'raw'
           pick → { kind, name, w }   (실행 상세를 볼 수 있는 칸을 클릭) */

function fmtElapsed(min) {
  const h = Math.floor(min / 60), m = min % 60;
  return h ? `${h}시간 ${m}분` : `${m}분`;
}

function pipeGridHtml(g, sel) {
  const last = g.headers.length - 1;
  let h = '<thead><tr><th class="prod-h">제품</th>';
  g.headers.forEach((w, i) => {
    h += `<th class="${i === last ? 'cur' : ''}">${w.start}<br><span class="end">~${w.end}</span></th>`;
  });
  h += '</tr></thead><tbody>';
  g.rows.forEach(p => {
    const selRow = sel && sel.kind === 'pipe' && sel.name === p.name;
    const cls = [p.clickable && 'clickable', selRow && 'selected'].filter(Boolean).join(' ');
    h += `<tr class="${cls}"><td class="prod">${p.name}</td>`;
    p.cells.forEach((c, i) => {
      const tipRun = c.st === 'run' && p.elapsedMin ? ` · 경과 ${fmtElapsed(p.elapsedMin)}` : '';
      const isSel = selRow && sel.w === i;
      const tcls = [i === last && 'cur', c.pick && 'pick', isSel && 'sel'].filter(Boolean).join(' ');
      const w = g.headers[i];
      h += `<td class="${tcls}" ${c.pick ? `data-cellpick="pipe|${p.name}|${i}"` : ''} data-tip="${p.name} · ${w.start}~${w.end}\n${ST[c.st].label}${tipRun}${c.pick ? '\n클릭 → 실행 상세' : ''}"><i class="pd ${c.st}"></i></td>`;
    });
    h += '</tr>';
  });
  return h + '</tbody>';
}

function rawGridHtml(g, sel) {
  const last = g.headers.length - 1;
  let h = '<thead><tr><th class="prod-h">제품</th>';
  g.headers.forEach((d, i) => {
    h += `<th class="${i === last ? 'cur' : ''}">${d.md}<br><span class="end">${d.dow}</span></th>`;
  });
  h += '</tr></thead><tbody>';
  g.rows.forEach(p => {
    const selRow = sel && sel.kind === 'raw' && sel.name === p.name;
    h += `<tr class="clickable ${selRow ? 'selected' : ''}"><td class="prod">${p.name}</td>`;
    p.cells.forEach((c, i) => {
      const d = g.headers[i];
      const extra = c.pick ? ` · ${c.st === 'run' ? '경과' : '소요'} ${fmtElapsed(c.durMin)}` : '';
      const isSel = selRow && sel.w === i;
      const tcls = [i === last && 'cur', c.pick && 'pick', isSel && 'sel'].filter(Boolean).join(' ');
      h += `<td class="${tcls}" ${c.pick ? `data-cellpick="raw|${p.name}|${i}"` : ''} data-tip="${p.name} · ${d.md} (${d.dow})\n${ST[c.st].label}${extra}${c.pick ? '\n클릭 → 실행 상세' : ''}"><i class="pd ${c.st}"></i></td>`;
    });
    h += '</tr>';
  });
  return h + '</tbody>';
}

export default function ({ parentElement, data, setTriggerValue }) {
  const wrap = parentElement.querySelector('.dpm');
  const { tab, grid, selected } = data;

  wrap.innerHTML = `
    <section class="panel" id="p1">
      <div class="panel-head">
        <h2>발행 현황</h2>
        <div class="viewbar seg" id="dagtab">
          <button data-tab="pipeline" class="${tab === 'pipeline' ? 'on' : ''}">pipeline</button><button data-tab="raw" class="${tab === 'raw' ? 'on' : ''}">raw_data</button>
        </div>
      </div>
      <div id="gridbox"><table class="pgrid">${tab === 'raw' ? rawGridHtml(grid, selected) : pipeGridHtml(grid, selected)}</table></div>
      <div class="panel-foot"><div class="legend">${legendHtml()}</div></div>
    </section>
    <div id="tip"></div>`;

  // 처음 그린 pipeline 격자 높이로 상자 고정 → raw_data로 바꿔도 크기 유지 (원본과 같음)
  const gb = wrap.querySelector('#gridbox');
  if (tab === 'pipeline' && gb.offsetHeight) UI.gridMinH = gb.offsetHeight;
  if (UI.gridMinH) gb.style.minHeight = UI.gridMinH + 'px';

  wrap.onclick = e => {
    const b = e.target.closest('[data-tab]');
    if (b) {
      if (b.dataset.tab !== tab) setTriggerValue('tab', b.dataset.tab);
      return;
    }
    const td = e.target.closest('td.pick');
    if (td) {
      const [kind, name, w] = td.dataset.cellpick.split('|');
      // Python 응답을 기다리는 동안에도 바로 선택된 것처럼 보이게
      // (같은 칸을 다시 누르면 선택 해제 — 원본과 같음)
      const wasSel = td.classList.contains('sel');
      wrap.querySelectorAll('td.sel').forEach(x => x.classList.remove('sel'));
      if (!wasSel) td.classList.add('sel');
      setTriggerValue('pick', { kind, name, w: +w });
    }
  };
  bindTooltip(wrap);
}
