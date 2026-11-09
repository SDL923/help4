/* (2) 오른쪽 패널 — 이번 주 요약 / pipeline 실행 상세 / raw_data 실행 상세
   data:   { mode: 'week', week }  |  { mode: 'pipe' | 'raw', run }
   이벤트: nav → { action: 'pick', name }        이번 주 달력 카드 클릭 (pipeline 이번 주 상세로)
                 { action: 'rpick', name, w }    raw_data 최근 N일 띠 클릭
                 { action: 'back' }              ← 이번 주 요약
   보기 전환(상태/소요/메모리/throttle)과 셀 강조는 데이터가 새로 필요 없어서 브라우저 안에서만 처리한다. */

const VIEWS = [
  { key: 'status', label: '상태' },
  { key: 'dur',    label: '소요' },
  { key: 'mem',    label: '메모리 피크' },
  { key: 'thr',    label: 'throttle' },
];

function heat(t) {
  const a = [238, 244, 252], b = [31, 95, 191];
  return `rgb(${a.map((v, i) => Math.round(v + (b[i] - v) * t))})`;
}

function viewValue(m, v, maxDur) {
  if (v === 'dur') return { text: fmtShort(m.dur), t: m.dur / maxDur };
  if (v === 'mem') { const r = m.memPeak / m.memReq; return { text: m.memPeak.toFixed(1), t: Math.min(r, 1), warn: r >= 0.9 }; }
  if (v === 'cpu') return { text: m.cpuAvg.toFixed(1), t: Math.min(m.cpuAvg / m.cpuLim, 1) };
  if (v === 'thr') return { text: `${m.thr}%`, t: Math.min(m.thr / 30, 1), warn: m.thr >= 10 };
}

function cellTip(mod, step, code, m) {
  const st = code.startsWith('R') ? '실행중' : { D: '완료', W: '대기', F: '실패', N: '미실행' }[code];
  let t = `${mod} · ${step}  ${st}`;
  if (!m) return t;
  t += `\n${m.live ? '경과' : '소요'}    ${fmtShort(m.dur)}`;
  t += `\n메모리  ${m.live ? '현재' : '피크'} ${m.memPeak.toFixed(1)} / req ${m.memReq} / lim ${m.memLim} GiB`;
  if (m.memAvg != null) t += `  (평균 ${m.memAvg.toFixed(1)})`;
  t += `\nCPU     ${m.live ? '현재' : '평균'} ${m.cpuAvg.toFixed(1)}c`;
  if (m.cpuPeak != null) t += ` · 피크 ${m.cpuPeak.toFixed(1)}c`;
  t += ` / req ${m.cpuReq.toFixed(1)} / lim ${m.cpuLim.toFixed(1)}`;
  t += `\nthrottle ${m.thr}%`;
  return t;
}

function gridLegend(d, view) {
  if (view === 'status') return `
    <span><i class="sw" style="background:var(--ok-solid)"></i>완료</span>
    <span><i class="sw" style="background:var(--run-solid)"></i>실행중</span>
    <span><i class="sw" style="background:var(--gray-bg);border:1px solid #dde2e7"></i>대기</span>
    <span><i class="sw" style="background:var(--fail-solid)"></i>실패</span>
    <span><i class="sw" style="background:repeating-linear-gradient(135deg,#fff 0 3px,#eef0f3 3px 5px);border:1px solid var(--border-soft)"></i>미실행</span>`;
  const scale = { dur: '제품 내 최장 대비', mem: '피크 ÷ request', cpu: '평균 ÷ limit', thr: '0 ~ 30%' }[view];
  let h = `<span>낮음 <i class="grad"></i> 높음 <span style="color:var(--text3)">(${scale})</span></span>`;
  if (view === 'mem') h += `<span><i class="sw warn-mk"></i>request 90%↑</span>`;
  if (view === 'thr') h += `<span><i class="sw warn-mk"></i>10%↑</span>`;
  if (d.status === 'run') h += `<span><i class="sw" style="box-shadow:inset 0 0 0 2px var(--run)"></i>실행중 (현재값)</span>`;
  if (d.modules.some(m => m.cells.includes('F'))) h += `<span><i class="sw" style="box-shadow:inset 0 0 0 2px var(--fail)"></i>실패</span>`;
  return h;
}

function gridHtml(d, view, focus) {
  const steps = d.steps, metrics = d.metrics;
  const maxDur = Math.max(1, ...metrics.flat().filter(Boolean).map(m => m.dur));
  let h = `<div class="viewbar">${VIEWS.map(v =>
    `<button data-view="${v.key}" class="${v.key === view ? 'on' : ''}">${v.label}</button>`).join('')}</div>`;
  h += `<div class="mgrid" style="grid-template-columns: auto repeat(${steps.length}, 36px)">`;
  h += '<div></div>' + steps.map(s => `<div class="mh">${s}</div>`).join('');
  d.modules.forEach((mod, mi) => {
    const mcls = mod.cells.includes('F') ? 'fail' : (mod.cells.every(c => c === 'D') ? 'done' : '');
    h += `<div class="ml ${mcls}">${mod.name}</div>`;
    mod.cells.forEach((c, i) => {
      const m = metrics[mi][i];
      const key = `${mod.name}.${steps[i]}`;
      const attrs = `data-cell="${key}" data-tip="${cellTip(mod.name, steps[i], c, m)}"`;
      const fc = focus === key ? ' focus' : '';
      if (view === 'status' || !m) {
        if (c.startsWith('R')) h += `<div class="mc run${fc}" ${attrs}>${c.split(':')[1]}</div>`;
        else h += `<div class="mc ${{ D: 'done', W: 'wait', F: 'fail', N: 'none' }[c]}${fc}" ${attrs}>${c === 'F' ? '×' : ''}</div>`;
      } else {
        const v = viewValue(m, view, maxDur);
        const cls = ['mc val', v.t > 0.55 && 'dark', m.live && 'live', m.failed && 'failed', v.warn && 'warn'].filter(Boolean).join(' ');
        h += `<div class="${cls}${fc}" style="background:${heat(v.t)}" ${attrs}>${v.text}</div>`;
      }
    });
  });
  h += `</div><div class="legend mlegend">${gridLegend(d, view)}</div>`;
  return h;
}

function barHtml(r, unit, decimals) {
  const pct = v => Math.min(100, (v / r.lim) * 100).toFixed(1);
  const tip = `값      ${r.use.toFixed(decimals)} ${unit}\nrequest ${r.req.toFixed(decimals)} ${unit}\nlimit   ${r.lim.toFixed(decimals)} ${unit}`;
  return `<div class="bar" data-tip="${tip}">
            <div class="fill" style="width:${pct(r.use)}%"></div>
            <div class="req" style="left:${pct(r.req)}%"></div>
          </div>
          <span class="rval">${r.use.toFixed(decimals)}<small> ${unit}</small></span>`;
}

function cpuHtml(cpu) {
  return `<span class="cpuv" data-tip="사용    ${cpu.use.toFixed(1)} c\nrequest ${cpu.req.toFixed(1)} c\nlimit   ${cpu.lim.toFixed(1)} c">${cpu.use.toFixed(1)}c</span>`;
}

function podsHtml(d) {
  let h = `<div class="sec-title">실행 중 Pod 리소스</div>`;
  const total = (k, f) => d.pods.reduce((a, p) => a + p[k][f], 0);
  const cpuUse = total('cpu', 'use'), cpuReq = total('cpu', 'req');
  h += `<div class="kpis">
    <div class="kpi"><div class="k">메모리 사용 / request 합</div>
      <div class="v">${total('mem', 'use').toFixed(1)} <small>/ ${total('mem', 'req')} GiB</small></div></div>
    <div class="kpi"><div class="k">CPU 사용 / request 합</div>
      <div class="v ${cpuUse > cpuReq ? 'warn' : ''}">${cpuUse.toFixed(1)}c <small>/ ${cpuReq.toFixed(1)}c</small></div></div>
  </div>
    <table class="rtable"><thead><tr><th>모듈·step</th><th>메모리</th><th>CPU</th></tr></thead><tbody>`;
  d.pods.forEach(p => {
    h += `<tr><td class="ms">${p.module}<span class="step">·${p.step}</span></td>
      <td><div class="rcell">${barHtml(p.mem, 'GiB', 1)}</div></td>
      <td>${cpuHtml(p.cpu)}</td></tr>`;
  });
  h += `</tbody></table>
    <div class="rnote"><span>막대 범위 0 ~ limit</span><span><i class="req-mark"></i>request</span></div>`;
  return h;
}

const BADGE = {
  run:   '<span class="badge run"><span class="dot">●</span>실행중</span>',
  sched: '<span class="badge sched">◷ 예정</span>',
  ok:    '<span class="badge ok">√ 완료</span>',
  fail:  '<span class="badge fail">× 실패</span>',
};

/* ---------- 이번 주 요약 ---------- */
function weekHtml(wk) {
  const sumHtml = counts => `<div class="wsum">${['ok', 'fail', 'run', 'sched'].map(st =>
    `<span><i class="pd ${st}"></i>${ST[st].label} <b>${counts[st]}</b></span>`).join('')}</div>`;

  let h = `<div class="panel-head"><h2>이번 주 요약</h2><span class="sub">${wk.range}</span></div>`;
  h += `<div class="wsec"><b>pipeline</b><span class="sub">주 1회</span>${sumHtml(wk.pipe.counts)}</div>`;
  h += '<div class="cal">';
  wk.pipe.days.forEach((day, i) => {
    h += `<div class="cal-col ${i === wk.todayIdx ? 'today' : ''}"><div class="cal-h">${day.dn} <span>${day.md}</span></div>`;
    day.items.forEach(it => {
      h += `<div class="card ${it.st}${it.pick ? ' pick' : ''}" ${it.pick ? `data-pick="${it.name}"` : ''}
               data-tip="${it.name} · ${day.dn} ${it.time}\n${ST[it.st].label}${it.pick ? '\n클릭 → 상세' : ''}">
        <div class="c1"><i class="pd ${it.st}"></i><b>${it.name}</b><span class="t">${it.time}</span></div>
        <div class="c2">${it.info}</div></div>`;
    });
    h += '</div>';
  });
  h += '</div>';

  h += `<div class="wsec second"><b>raw_data</b><span class="sub">매일 · 전 제품</span>${sumHtml(wk.raw.counts)}</div><div class="rsum">`;
  wk.raw.days.forEach((day, i) => {
    const dots = day.dots.map(r =>
      `<i class="pd ${r.st}" data-tip="${r.name} · ${day.md} (${day.dn})\n${ST[r.st].label}"></i>`).join('');
    h += `<div class="rs-col ${i === wk.todayIdx ? 'today' : ''}"><div class="cal-h">${day.dn} <span>${day.md}</span></div><div class="rs-dots">${dots}</div></div>`;
  });
  return h + '</div>';
}

const backBtn = '<button class="back" data-back>← 이번 주 요약</button>';

/* ---------- pipeline 실행 상세 ---------- */
function pipeHtml(d, view, focus) {
  let h = `<div class="panel-head"><h2>선택 제품 상세</h2><span class="sub">pipeline · ${d.when} 실행${d.finished ? ' (종료)' : ''}</span>${backBtn}</div>`;
  h += `<div class="dhead"><span class="pname">${d.name}</span>${BADGE[d.status]}`;
  if (d.status === 'run') h += `<span class="elapsed">전체 경과 <b>${d.elapsed}</b></span>`;
  if (d.finished) h += `<span class="elapsed">소요 <b>${d.took}</b> · ${d.startLabel} → ${d.endLabel}</span>`;
  h += `<span class="dag">${d.dag}</span></div>`;

  if (d.status === 'sched') {
    return h + `<div class="sched-box">
      <div class="big"><span class="t">${d.scheduleText}</span> 실행 예정</div>
      <div class="sub">모듈 ${d.moduleCount}개 × ${d.steps.length} step</div></div>`;
  }
  return h + `<div class="dbody"><div><div class="sec-title">모듈 × step</div>${gridHtml(d, view, focus)}</div>
    <div>${d.finished ? '<div class="sec-title">실행 요약</div><div class="tbd">미정</div>' : podsHtml(d)}</div></div>`;
}

/* ---------- raw_data 실행 상세 ---------- */
function rawHtml(r) {
  let h = `<div class="panel-head"><h2>선택 제품 상세</h2><span class="sub">raw_data · ${r.when} 실행${r.finished ? ' (종료)' : ''}</span>${backBtn}</div>`;
  h += `<div class="dhead"><span class="pname">${r.name}</span>${BADGE[r.status]}`;
  h += r.finished
    ? `<span class="elapsed">소요 <b>${r.dur}</b> · ${r.startLabel} → ${r.endLabel}</span>`
    : `<span class="elapsed">경과 <b>${r.dur}</b> · ${r.startLabel} 시작</span>`;
  h += `<span class="dag">${r.dag}</span></div>`;

  const strip = r.strip.map(s => `<div class="r7 ${s.i === r.w ? 'on' : ''}${s.pick ? ' pick' : ''}" ${s.pick ? `data-rpick="${r.name}|${s.i}"` : ''}
      data-tip="${s.md} (${s.dow}) · ${ST[s.st].label}">
    <span class="d">${s.dow}</span><i class="pd ${s.st}"></i>
    <span class="v">${s.dur || '—'}</span></div>`).join('');

  const kv = [];
  if (r.diff != null) kv.push(['평소 대비', `<span class="wd ${r.diff > 0 ? 'up' : 'down'}">${r.diff > 0 ? '+' : ''}${r.diff}%</span> <span class="muted">평균 ${r.avg}</span>`]);
  if (r.next) kv.push(['다음 예정', r.next]);
  if (r.note) kv.push(['비고', `<span class="${r.status === 'fail' ? 'nfail' : ''}">${r.note}</span>`]);

  h += `<div class="dbody"><div class="rleft"><div class="sec-title">최근 ${r.days}일 · 소요</div><div class="r7s">${strip}</div>`;
  if (kv.length) h += `<dl class="kv">${kv.map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join('')}</dl>`;
  h += '</div><div>';
  if (!r.finished) {
    h += `<div class="sec-title">실행 중 Pod 리소스</div>
      <table class="rtable"><thead><tr><th>메모리</th><th>CPU</th></tr></thead><tbody><tr>
        <td><div class="rcell">${barHtml(r.pod.mem, 'GiB', 1)}</div></td><td>${cpuHtml(r.pod.cpu)}</td>
      </tr></tbody></table>`;
  } else {
    h += `<div class="sec-title">리소스 기록</div>
      <table class="rtable"><thead><tr><th>메모리 피크</th><th>throttle</th></tr></thead><tbody><tr>
        <td><div class="rcell">${barHtml(r.res.mem, 'GiB', 1)}</div></td>
        <td><span class="thr ${r.res.thr >= 10 ? 'hot' : ''}">${r.res.thr}%</span></td>
      </tr></tbody></table>`;
  }
  return h + `<div class="rnote"><span>막대 범위 0 ~ limit</span><span><i class="req-mark"></i>request</span></div></div></div>`;
}

export default function ({ parentElement, data, setTriggerValue }) {
  const wrap = parentElement.querySelector('.dpm');
  UI.view = UI.view || 'status';

  // 다른 실행을 선택하면 강조 셀은 풀고, 보기(상태/소요/…)는 유지 (원본과 같음)
  const runId = data.mode === 'week' ? 'week' : `${data.run.kind}|${data.run.name}|${data.run.w}`;
  if (UI.runId !== runId) { UI.focus = null; UI.runId = runId; }

  const draw = () => {
    const body = data.mode === 'week' ? weekHtml(data.week)
      : data.mode === 'raw' ? rawHtml(data.run)
      : pipeHtml(data.run, UI.view, UI.focus);
    wrap.innerHTML = `<section class="panel" id="p2">${body}</section><div id="tip"></div>`;
  };
  draw();

  wrap.onclick = e => {
    const pk = e.target.closest('[data-pick]');
    if (pk) { setTriggerValue('nav', { action: 'pick', name: pk.dataset.pick }); return; }
    const rp = e.target.closest('[data-rpick]');
    if (rp) { const [n, i] = rp.dataset.rpick.split('|'); setTriggerValue('nav', { action: 'rpick', name: n, w: +i }); return; }
    if (e.target.closest('[data-back]')) { setTriggerValue('nav', { action: 'back' }); return; }

    // 아래 두 가지는 Python 왕복 없이 바로 다시 그림
    const b = e.target.closest('[data-view]');
    if (b) { UI.view = b.dataset.view; draw(); return; }
    const c = e.target.closest('[data-cell]');
    if (c) { UI.focus = UI.focus === c.dataset.cell ? null : c.dataset.cell; draw(); }
  };
  bindTooltip(wrap);
}
