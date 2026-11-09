"""DPM 운영 대시보드 — Streamlit 버전 (dpm_dashboard.html 디자인을 그대로 옮김)

실행:  streamlit run app.py      (Streamlit 1.51 이상 필요: st.components.v2 사용)

구성
  - 상단바, 페이지 배경·여백 ............ Streamlit (st.html)
  - (1) 발행 현황 격자 .................. 커스텀 컴포넌트 ui/status_grid.js
  - (2) 이번 주 요약 / 선택 제품 상세 ... 커스텀 컴포넌트 ui/detail_panel.js
  - 데이터 ............................. mock_api.py (실제 구현 시 Prometheus 등 API 호출로 교체)

흐름: 칸 클릭 → JS가 클릭값을 Python으로 보냄 → 콜백이 session_state 갱신
      → 이 fragment만 다시 실행 → 필요한 API만 호출 → 컴포넌트에 새 데이터 전달
"""
from pathlib import Path

import streamlit as st

import mock_api as api

st.set_page_config(page_title="DPM 운영 대시보드", page_icon="📊", layout="wide",
                   initial_sidebar_state="collapsed")

# ---------------------------------------------------------------------
# 컴포넌트 등록 (HTML/CSS/JS 문자열을 그대로 넘김 — npm·빌드 없음)
# ---------------------------------------------------------------------
UI_DIR = Path(__file__).parent / "ui"


def _read(name: str) -> str:
    return (UI_DIR / name).read_text(encoding="utf-8")


CSS = _read("dpm.css")
COMMON_JS = _read("common.js")

status_grid = st.components.v2.component(
    "dpm_status_grid",
    html='<div class="dpm"></div>',
    css=CSS,
    js=COMMON_JS + _read("status_grid.js"),
)
detail_panel = st.components.v2.component(
    "dpm_detail_panel",
    html='<div class="dpm"></div>',
    css=CSS,
    js=COMMON_JS + _read("detail_panel.js"),
)

# ---------------------------------------------------------------------
# 페이지 전체 스타일: Streamlit 기본 헤더·여백을 없애고 원본 배경·상단바에 맞춤
# ---------------------------------------------------------------------
st.html(f"""
<style>
  header[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"],
  [data-testid="stStatusWidget"], footer {{ display: none !important; }}
  .stApp {{ background: #f5f7fa; }}
  [data-testid="stMainBlockContainer"] {{ padding: 0 !important; max-width: none !important; }}
  [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] {{ gap: 0; }}

  .dpm-topbar {{
    display: flex; align-items: center; gap: 24px;
    padding: 0 24px; height: 48px;
    background: #ffffff; border-bottom: 1px solid #d8dee4; color: #1f2328;
    font: 13px/1.45 "Pretendard", "Malgun Gothic", "Apple SD Gothic Neo", system-ui, sans-serif;
  }}
  .dpm-topbar .brand {{ font-weight: 700; font-size: 15px; letter-spacing: -0.2px; }}
  .dpm-topbar .meta {{ margin-left: auto; color: #8c959f; font-size: 12px; }}

  /* 원본 main: padding 20px 24px 32px, 두 패널 사이 16px, 두 패널 높이 같게 */
  .st-key-dpm_main {{ padding: 20px 24px 32px; gap: 16px !important; align-items: stretch !important; }}
  .st-key-dpm_main .stBidiComponent, .st-key-dpm_main .stBidiComponent > div {{ height: 100%; }}
</style>
<header class="dpm-topbar">
  <div class="brand">DPM</div>
  <div class="meta">{api.fetch_meta()["now_label"]}</div>
</header>
""")

# ---------------------------------------------------------------------
# 상태: 발행 현황 탭 / 선택한 칸
# ---------------------------------------------------------------------
ss = st.session_state
ss.setdefault("tab", "pipeline")   # pipeline | raw
ss.setdefault("selected", None)    # {"kind": "pipe"|"raw", "name", "w"} — None이면 이번 주 요약


def _event(component_key: str, event: str):
    """컴포넌트가 setTriggerValue(event, value)로 보낸 값 꺼내기"""
    v = ss.get(component_key)
    if v is None:
        return None
    return v.get(event) if hasattr(v, "get") else getattr(v, event, None)


def on_grid_tab():
    tab = _event("grid", "tab")
    if tab and tab != ss.tab:
        ss.tab, ss.selected = tab, None


def on_grid_pick():
    p = _event("grid", "pick")
    if not p:
        return
    same = ss.selected and all(ss.selected.get(k) == p.get(k) for k in ("kind", "name", "w"))
    ss.selected = None if same else {"kind": p["kind"], "name": p["name"], "w": int(p["w"])}


def on_detail_nav():
    n = _event("detail", "nav")
    if not n:
        return
    if n["action"] == "back":
        ss.selected = None
    elif n["action"] == "pick":     # 이번 주 달력 카드 → pipeline 이번 주 상세
        ss.tab = "pipeline"
        ss.selected = {"kind": "pipe", "name": n["name"], "w": api.MOCK["pipeline"]["weeks"] - 1}
    elif n["action"] == "rpick":    # raw_data 최근 N일 띠 → 그 날짜 상세
        ss.tab = "raw"
        ss.selected = {"kind": "raw", "name": n["name"], "w": int(n["w"])}


# ---------------------------------------------------------------------
# 본문 — fragment라서 클릭하면 이 함수만 다시 실행됨 (상단바는 그대로)
# ---------------------------------------------------------------------
@st.fragment
def main_area():
    # 왼쪽 격자 데이터: 현재 탭에 맞는 API만 호출
    grid = api.fetch_pipeline_grid() if ss.tab == "pipeline" else api.fetch_raw_grid()

    # 오른쪽 패널 데이터: 선택한 칸이 있으면 그 실행 상세, 없으면 이번 주 요약
    detail = None
    sel = ss.selected
    if sel:
        run = api.fetch_pipeline_run(sel["name"], sel["w"]) if sel["kind"] == "pipe" \
            else api.fetch_raw_run(sel["name"], sel["w"])
        if run:
            detail = {"mode": sel["kind"], "run": run}
        else:
            ss.selected = None
    if detail is None:
        detail = {"mode": "week", "week": api.fetch_week_summary()}

    with st.container(horizontal=True, key="dpm_main", gap=None):
        status_grid(
            key="grid",
            data={"tab": ss.tab, "grid": grid, "selected": ss.selected},
            width=418,   # 원본 격자 380px + 패널 안쪽 여백
            on_tab_change=on_grid_tab,
            on_pick_change=on_grid_pick,
        )
        detail_panel(
            key="detail",
            data=detail,
            width="stretch",
            on_nav_change=on_detail_nav,
        )


main_area()
