/* 두 컴포넌트(발행 현황 격자, 상세 패널)가 같이 쓰는 함수 — app.py에서 각 컴포넌트 JS 앞에 붙여서 등록한다. */

const ST = {
  ok:    { sym: '√', label: '성공' },
  fail:  { sym: '×', label: '실패' },
  run:   { sym: '•', label: '진행중' },
  sched: { sym: '·', label: '예정' },
  none:  { sym: '-', label: '미실행' },
};
const pad = n => String(n).padStart(2, '0');
const fmtShort = min => `${Math.floor(min / 60)}h${pad(min % 60)}`;

// 화면에서만 쓰는 상태(보기 전환·강조 셀 등). Python으로 보낼 필요 없는 값이라 브라우저에만 둔다.
const UI = (window.__dpmUI = window.__dpmUI || {});

function legendHtml() {
  return Object.entries(ST).map(([k, v]) =>
    `<span><i class="pd ${k}"></i>${v.label}</span>`).join('');
}

// 컴포넌트 안의 [data-tip] 요소에 마우스를 올리면 툴팁 표시 (원본과 같은 동작)
function bindTooltip(wrap) {
  wrap.onmousemove = e => {
    const tip = wrap.querySelector('#tip');
    if (!tip) return;
    const t = e.target.closest('[data-tip]');
    if (!t) { tip.style.display = 'none'; return; }
    tip.textContent = t.dataset.tip;
    tip.style.display = 'block';
    const x = Math.min(e.clientX + 12, window.innerWidth - tip.offsetWidth - 8);
    tip.style.left = x + 'px';
    tip.style.top = (e.clientY + 14) + 'px';
  };
  wrap.onmouseleave = () => {
    const tip = wrap.querySelector('#tip');
    if (tip) tip.style.display = 'none';
  };
}
