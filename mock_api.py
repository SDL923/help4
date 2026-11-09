"""가짜 API — 원본 HTML의 MOCK 데이터와 계산을 Python으로 옮긴 것.

실제 구현에서는 이 파일의 fetch_* 함수 안쪽만 Prometheus / Airflow API 호출로 바꾸면 된다.
화면(ui/*.js)은 여기서 돌려주는 dict 구조만 알면 되므로 손댈 필요가 없다.

상태 코드: ok=성공 / fail=실패 / run=진행중 / sched=예정 / none=미실행
"""
from __future__ import annotations

import math
import time
from datetime import datetime, timedelta

# 클릭마다 API를 부르는 느낌을 확인하고 싶으면 0.3 정도로 올려본다.
SIMULATED_LATENCY_SEC = 0.0

def _api(name: str) -> None:
    # 클릭할 때마다 어떤 API가 불리는지 터미널에서 확인용
    print(f"[API] {name}", flush=True)
    if SIMULATED_LATENCY_SEC:
        time.sleep(SIMULATED_LATENCY_SEC)


# =====================================================================
# 목업 데이터 (원본 HTML의 MOCK 그대로)
# =====================================================================
NOW = datetime(2026, 11, 4, 7, 30)

MOCK = {
    "pipeline": {
        "weeks": 7,
        "products": [
            {"name": "PBEQ", "clickable": True,  "history": ["ok", "ok", "ok", "fail", "ok", "ok", "ok", "run"]},
            {"name": "PBEJ", "clickable": True,  "history": ["ok", "ok", "ok", "ok", "ok", "fail", "ok", "run"]},
            {"name": "PBEK", "clickable": True,  "history": ["ok", "ok", "ok", "ok", "ok", "ok", "ok", "ok"]},
            {"name": "PBEM", "clickable": False, "history": ["ok", "fail", "ok", "ok", "ok", "ok", "ok", "fail"]},
            {"name": "PBFA", "clickable": False, "history": ["ok", "ok", "none", "ok", "ok", "ok", "ok", "ok"]},
            {"name": "PBFC", "clickable": False, "history": ["ok", "ok", "ok", "ok", "ok", "ok", "ok", "sched"]},
            {"name": "PBGD", "clickable": False, "history": ["none", "none", "ok", "ok", "ok", "ok", "ok", "sched"]},
            {"name": "PBGH", "clickable": False, "history": ["ok", "ok", "ok", "ok", "fail", "ok", "ok", "ok"]},
            {"name": "PBHS", "clickable": False, "history": ["ok", "ok", "ok", "ok", "ok", "ok", "none", "sched"]},
        ],
    },
    "steps": ["merge", "model", "stat", "gain", "rank", "filter"],
    "stepProfile": {
        "merge":  {"dur": [15, 30],  "memReq": 32, "memLim": 40, "mem": [0.45, 0.75], "cpuReq": 1.0, "cpuLim": 2.0, "cpu": [0.6, 1.2]},
        "model":  {"dur": [50, 80],  "memReq": 32, "memLim": 48, "mem": [0.60, 0.88], "cpuReq": 1.0, "cpuLim": 2.0, "cpu": [1.1, 1.6]},
        "stat":   {"dur": [30, 50],  "memReq": 32, "memLim": 48, "mem": [0.45, 0.80], "cpuReq": 1.0, "cpuLim": 3.0, "cpu": [1.3, 2.1]},
        "gain":   {"dur": [25, 45],  "memReq": 24, "memLim": 32, "mem": [0.45, 0.85], "cpuReq": 1.0, "cpuLim": 2.0, "cpu": [0.8, 1.3]},
        "rank":   {"dur": [60, 130], "memReq": 32, "memLim": 48, "mem": [0.50, 0.85], "cpuReq": 1.0, "cpuLim": 2.0, "cpu": [1.2, 1.8]},
        "filter": {"dur": [10, 20],  "memReq": 16, "memLim": 24, "mem": [0.20, 0.50], "cpuReq": 1.0, "cpuLim": 2.0, "cpu": [0.3, 0.7]},
    },
    "detail": {
        "PBEQ": {
            "status": "run",
            "dag": "dpm_pipeline_pbeq",
            "elapsedMin": 330,
            "modules": [
                {"name": "M01", "cells": ["D", "D", "D", "D", "D", "D"]},
                {"name": "M02", "cells": ["D", "D", "D", "D", "D", "D"]},
                {"name": "M03", "cells": ["D", "D", "D", "D", "R:2h10", "W"]},
                {"name": "M04", "cells": ["D", "D", "D", "R:1h45", "W", "W"]},
                {"name": "M05", "cells": ["D", "D", "R:1h20", "W", "W", "W"]},
                {"name": "M06", "cells": ["D", "R:0h55", "W", "W", "W", "W"]},
                {"name": "M07", "cells": ["R:0h25", "W", "W", "W", "W", "W"]},
                {"name": "M08", "cells": ["D", "D", "F", "N", "N", "N"]},
                {"name": "M09", "cells": ["W", "W", "W", "W", "W", "W"]},
                {"name": "M10", "cells": ["W", "W", "W", "W", "W", "W"]},
                {"name": "M11", "cells": ["W", "W", "W", "W", "W", "W"]},
                {"name": "M12", "cells": ["W", "W", "W", "W", "W", "W"]},
            ],
            "pods": [
                {"module": "M03", "step": "rank",  "mem": {"use": 22.4, "req": 32, "lim": 48}, "cpu": {"use": 1.8, "req": 1.0, "lim": 2.0, "throttle": 18}},
                {"module": "M04", "step": "gain",  "mem": {"use": 18.9, "req": 24, "lim": 32}, "cpu": {"use": 1.2, "req": 1.0, "lim": 2.0, "throttle": 0}},
                {"module": "M05", "step": "stat",  "mem": {"use": 25.1, "req": 32, "lim": 48}, "cpu": {"use": 2.1, "req": 1.0, "lim": 3.0, "throttle": 24}},
                {"module": "M06", "step": "model", "mem": {"use": 14.6, "req": 24, "lim": 32}, "cpu": {"use": 0.9, "req": 1.0, "lim": 2.0, "throttle": 0}},
                {"module": "M07", "step": "merge", "mem": {"use": 18.6, "req": 32, "lim": 40}, "cpu": {"use": 1.5, "req": 1.0, "lim": 2.0, "throttle": 6}},
            ],
            "failure": {"module": "M08", "step": "stat", "reason": "OOMKilled", "memAtFail": 47.8, "memLim": 48, "durMin": 48},
        },
        "PBEK": {
            "status": "ok",
            "dag": "dpm_pipeline_pbek",
            "modules": [{"name": f"M0{i}", "cells": ["D"] * 6} for i in range(1, 9)],
            "summary": {
                "start": "2026-11-02T02:00:00", "end": "2026-11-02T08:10:00", "retries": 0,
                "recentDurMin": [322, 341, 335, 350, 338, 344, 329, 370],
            },
            "overrides": {
                "M03.model": {"memPeak": 31.8},
                "M06.rank": {"memPeak": 30.9, "dur": 165},
                "M02.stat": {"thr": 22},
            },
        },
        "PBEJ": {
            "status": "run",
            "dag": "dpm_pipeline_pbej",
            "elapsedMin": 190,
            "modules": [
                {"name": "M01", "cells": ["D", "D", "D", "D", "D", "R:0h15"]},
                {"name": "M02", "cells": ["D", "D", "D", "R:0h40", "W", "W"]},
                {"name": "M03", "cells": ["D", "R:1h05", "W", "W", "W", "W"]},
                {"name": "M04", "cells": ["R:0h20", "W", "W", "W", "W", "W"]},
                {"name": "M05", "cells": ["R:0h05", "W", "W", "W", "W", "W"]},
            ],
            "pods": [
                {"module": "M01", "step": "filter", "mem": {"use": 9.8, "req": 16, "lim": 24}, "cpu": {"use": 0.6, "req": 1.0, "lim": 2.0, "throttle": 0}},
                {"module": "M02", "step": "gain",  "mem": {"use": 16.2, "req": 24, "lim": 32}, "cpu": {"use": 1.1, "req": 1.0, "lim": 2.0, "throttle": 3}},
                {"module": "M03", "step": "model", "mem": {"use": 27.8, "req": 32, "lim": 48}, "cpu": {"use": 1.9, "req": 1.0, "lim": 2.0, "throttle": 21}},
                {"module": "M04", "step": "merge", "mem": {"use": 11.5, "req": 24, "lim": 32}, "cpu": {"use": 0.7, "req": 1.0, "lim": 2.0, "throttle": 0}},
                {"module": "M05", "step": "merge", "mem": {"use": 6.3, "req": 24, "lim": 32}, "cpu": {"use": 0.4, "req": 1.0, "lim": 2.0, "throttle": 0}},
            ],
        },
    },
    "thisWeek": {
        "PBEM": {"failAt": "M04·rank"},
        "PBFA": {"durMin": 302, "avgMin": 311},
        "PBGH": {"durMin": 288, "avgMin": 285},
    },
    "schedule": {
        "PBEK": "월 02:00", "PBEM": "월 03:00",
        "PBFA": "화 02:00", "PBGH": "화 03:00",
        "PBEQ": "수 02:00", "PBEJ": "수 04:20",
        "PBFC": "목 02:00", "PBGD": "목 03:00",
        "PBHS": "금 02:00",
    },
    "rawData": {
        "days": 7,
        "products": [
            {"name": "PBEQ", "history": ["ok", "ok", "ok", "ok", "ok", "ok", "ok"]},
            {"name": "PBEJ", "history": ["ok", "ok", "fail", "ok", "ok", "ok", "ok"]},
            {"name": "PBEK", "history": ["ok", "ok", "ok", "ok", "ok", "ok", "run"]},
            {"name": "PBEM", "history": ["ok", "ok", "ok", "ok", "ok", "fail", "fail"]},
            {"name": "PBFA", "history": ["ok", "ok", "ok", "ok", "ok", "ok", "ok"]},
            {"name": "PBFC", "history": ["ok", "ok", "ok", "ok", "ok", "ok", "sched"]},
            {"name": "PBGD", "history": ["ok", "ok", "ok", "fail", "ok", "ok", "ok"]},
            {"name": "PBGH", "history": ["ok", "ok", "ok", "ok", "ok", "ok", "none"]},
        ],
        "profile": {"dur": [25, 60], "memReq": 16, "memLim": 24, "mem": [0.40, 0.92], "cpuReq": 1.0, "cpuLim": 2.0, "cpu": [0.5, 1.5]},
        "today": {
            "PBEQ": {"start": "01:00", "durMin": 38, "next": "내일 01:00"},
            "PBEJ": {"start": "01:00", "durMin": 41, "next": "내일 01:00"},
            "PBEK": {"start": "06:18", "durMin": 72, "next": "내일 01:00", "note": "평소 대비 +20분",
                     "pod": {"mem": {"use": 12.4, "req": 16, "lim": 24}, "cpu": {"use": 1.1, "req": 1.0, "lim": 2.0}}},
            "PBEM": {"start": "01:00", "durMin": 7, "next": "오늘 09:00 (재시도)", "note": "source table 미도착 · 재시도 1/3"},
            "PBFA": {"start": "01:00", "durMin": 29, "next": "내일 01:00"},
            "PBFC": {"start": "08:00", "next": "오늘 08:00"},
            "PBGD": {"start": "01:00", "durMin": 52, "next": "내일 01:00"},
            "PBGH": {"next": "내일 01:00", "note": "원천 시스템 점검으로 오늘 skip"},
        },
    },
}

# =====================================================================
# 유틸 (원본 JS 함수 그대로 옮김)
# =====================================================================
DOW = ["일", "월", "화", "수", "목", "금", "토"]   # JS getDay() 순서
M32 = 0xFFFFFFFF


def dow(d: datetime) -> str:
    return DOW[(d.weekday() + 1) % 7]


def md(d: datetime) -> str:
    return f"{d.month:02d}/{d.day:02d}"


def js_round(x: float) -> int:
    return math.floor(x + 0.5)


def lerp(a, b, x):
    return a + (b - a) * x


def mean(arr):
    return sum(arr) / len(arr)


def parse_dur(s: str) -> int:
    h, m = s.split("h")
    return int(h) * 60 + int(m)


def fmt_short(minutes: int) -> str:
    return f"{minutes // 60}h{minutes % 60:02d}"


def fmt_elapsed(minutes: int) -> str:
    h, m = divmod(minutes, 60)
    return f"{h}시간 {m}분" if h else f"{m}분"


def fmt_dt(d: datetime) -> str:
    return f"{md(d)} ({dow(d)}) {d.hour:02d}:{d.minute:02d}"


def fmt_hm(d: datetime) -> str:
    return f"{d.hour:02d}:{d.minute:02d}"


def _imul(a: int, b: int) -> int:
    return (a * b) & M32


def rng(seed: str):
    """원본 JS rng()와 같은 수열을 내는 시드 난수 — 같은 셀은 항상 같은 목업 값."""
    h = 2166136261
    for ch in seed:
        h = _imul(h ^ ord(ch), 16777619)
    state = [h]

    def nxt() -> float:
        state[0] = (state[0] + 0x6D2B79F5) & M32
        t = state[0]
        t = _imul(t ^ (t >> 15), t | 1)
        t = (t ^ ((t + _imul(t ^ (t >> 7), t | 61)) & M32)) & M32
        return ((t ^ (t >> 14)) & M32) / 4294967296

    return nxt


def _monday() -> datetime:
    d = NOW.replace(hour=0, minute=0, second=0, microsecond=0)
    return d - timedelta(days=d.weekday())


def week_ranges(n: int) -> list[dict]:
    mon = _monday()
    out = []
    for i in range(n - 1, -1, -1):
        s = mon - timedelta(days=7 * i)
        e = s + timedelta(days=6)
        out.append({"start": md(s), "end": md(e)})
    return out


def raw_days() -> list[datetime]:
    n = MOCK["rawData"]["days"]
    today = NOW.replace(hour=0, minute=0, second=0, microsecond=0)
    return [today - timedelta(days=n - 1 - i) for i in range(n)]


def module_progress(name: str) -> str | None:
    d = MOCK["detail"].get(name)
    if not d:
        return None
    if "modules" not in d:
        return f"0/{d['moduleCount']}"
    done = sum(all(c == "D" for c in m["cells"]) for m in d["modules"])
    return f"{done}/{len(d['modules'])}"


# =====================================================================
# 내부 계산 (원본 getRun / getRawRun / cellMetric)
# =====================================================================
def _pipe_history(name: str) -> list[str]:
    p = next(x for x in MOCK["pipeline"]["products"] if x["name"] == name)
    return p["history"][-MOCK["pipeline"]["weeks"]:]


def _get_run(name: str, w: int) -> dict | None:
    base = MOCK["detail"].get(name)
    if not base:
        return None
    last = MOCK["pipeline"]["weeks"] - 1
    if w == last:
        return base
    st = _pipe_history(name)[w]
    if st not in ("ok", "fail"):
        return None
    seed = f"{name}#{w}"
    r = rng(seed)
    n = len(MOCK["steps"])
    fail_mod = math.floor(r() * len(base["modules"])) if st == "fail" else -1
    fail_step = 1 + math.floor(r() * (n - 1))
    modules = []
    for mi, m in enumerate(base["modules"]):
        cells = []
        for si in range(n):
            if mi != fail_mod:
                cells.append("D")
            else:
                cells.append("D" if si < fail_step else "F" if si == fail_step else "N")
        modules.append({"name": m["name"], "cells": cells})
    day, tm = MOCK["schedule"].get(name, "월 02:00").split(" ")
    start = _monday() - timedelta(days=7 * (last - w)) + timedelta(days=["월", "화", "수", "목", "금"].index(day))
    hh, mm = map(int, tm.split(":"))
    start = start.replace(hour=hh, minute=mm)
    end = start + timedelta(minutes=js_round(lerp(280, 380, r())))
    return {"status": st, "dag": base["dag"], "modules": modules,
            "summary": {"start": start, "end": end}, "seed": seed}


def _cell_metric(pname: str, d: dict, mod: str, step: str, code: str) -> dict | None:
    if code in ("W", "N"):
        return None
    if code.startswith("R"):
        pod = next((p for p in d.get("pods", []) if p["module"] == mod and p["step"] == step), None)
        if pod:
            return {
                "live": True, "failed": False, "dur": parse_dur(code.split(":")[1]),
                "memPeak": pod["mem"]["use"], "memAvg": None, "memReq": pod["mem"]["req"], "memLim": pod["mem"]["lim"],
                "cpuAvg": pod["cpu"]["use"], "cpuPeak": None, "cpuReq": pod["cpu"]["req"], "cpuLim": pod["cpu"]["lim"],
                "thr": pod["cpu"]["throttle"],
            }
    P = MOCK["stepProfile"][step]
    r = rng(f"{pname}.{mod}.{step}")
    mem_peak = round(P["memReq"] * lerp(P["mem"][0], P["mem"][1], r()), 1)
    cpu_avg = round(lerp(P["cpu"][0], P["cpu"][1], r()), 1)
    cpu_peak = round(min(P["cpuLim"], cpu_avg * lerp(1.2, 1.6, r())), 1)
    m = {
        "live": False, "failed": code == "F",
        "dur": js_round(lerp(P["dur"][0], P["dur"][1], r())),
        "memPeak": mem_peak, "memAvg": round(mem_peak * lerp(0.6, 0.85, r()), 1),
        "memReq": P["memReq"], "memLim": P["memLim"],
        "cpuAvg": cpu_avg, "cpuPeak": cpu_peak, "cpuReq": P["cpuReq"], "cpuLim": P["cpuLim"],
    }
    m["thr"] = js_round(lerp(10, 28, r())) if cpu_peak >= P["cpuLim"] * 0.9 else js_round(lerp(0, 6, r()))
    if m["failed"] and d.get("failure"):
        m["memPeak"] = d["failure"]["memAtFail"]
        m["dur"] = d["failure"]["durMin"]
    m.update(d.get("overrides", {}).get(f"{mod}.{step}", {}))
    return m


def _get_raw_run(name: str, i: int) -> dict | None:
    R = MOCK["rawData"]
    p = next((x for x in R["products"] if x["name"] == name), None)
    if not p:
        return None
    st = p["history"][-R["days"]:][i]
    if st not in ("ok", "fail", "run"):
        return None
    last = R["days"] - 1
    t = R["today"].get(name, {}) if i == last else {}
    P = R["profile"]
    r = rng(f"raw.{name}#{i}")
    date = raw_days()[i]
    hh, mm = map(int, t.get("start", "01:00").split(":"))
    start = date.replace(hour=hh, minute=mm)
    if t.get("durMin") is not None:
        dur = t["durMin"]
    else:
        dur = js_round(lerp(3, 15, r()) if st == "fail" else lerp(P["dur"][0], P["dur"][1], r()))
    run = {
        "status": st, "dag": f"dpm_raw_{name.lower()}", "date": date, "start": start, "durMin": dur,
        "end": None if st == "run" else start + timedelta(minutes=dur),
        "next": t.get("next", ""), "note": t.get("note") or ("source table 미도착" if st == "fail" else ""),
    }
    if st == "run":
        run["pod"] = t.get("pod")
    else:
        mem_peak = round(P["memReq"] * lerp(P["mem"][0], P["mem"][1], r()), 1)
        cpu_avg = round(lerp(P["cpu"][0], P["cpu"][1], r()), 1)
        cpu_peak = min(P["cpuLim"], cpu_avg * lerp(1.2, 1.6, r()))
        run["res"] = {
            "mem": {"use": mem_peak, "req": P["memReq"], "lim": P["memLim"]},
            "thr": js_round(lerp(10, 28, r())) if cpu_peak >= P["cpuLim"] * 0.9 else js_round(lerp(0, 6, r())),
        }
    return run


# =====================================================================
# 화면이 부르는 API — 반환값은 전부 JSON으로 보낼 수 있는 dict
# =====================================================================
def fetch_meta() -> dict:
    return {"now_label": f"기준 {md(NOW)} ({dow(NOW)}) {NOW.hour:02d}:{NOW.minute:02d} · 목업 데이터"}


def fetch_pipeline_grid() -> dict:
    """발행 현황 > pipeline 탭: 제품 × 최근 N주"""
    _api("fetch_pipeline_grid")
    n = MOCK["pipeline"]["weeks"]
    rows = []
    for p in MOCK["pipeline"]["products"]:
        d = MOCK["detail"].get(p["name"])
        rows.append({
            "name": p["name"],
            "clickable": p["clickable"],
            "elapsedMin": d.get("elapsedMin") if d else None,
            "cells": [{"st": s, "pick": _get_run(p["name"], i) is not None}
                      for i, s in enumerate(p["history"][-n:])],
        })
    return {"headers": week_ranges(n), "rows": rows}


def fetch_raw_grid() -> dict:
    """발행 현황 > raw_data 탭: 제품 × 최근 N일"""
    _api("fetch_raw_grid")
    R = MOCK["rawData"]
    days = raw_days()
    rows = []
    for p in R["products"]:
        cells = []
        for i, s in enumerate(p["history"][-R["days"]:]):
            run = _get_raw_run(p["name"], i)
            cells.append({"st": s, "pick": run is not None, "durMin": run["durMin"] if run else None})
        rows.append({"name": p["name"], "cells": cells})
    return {"headers": [{"md": md(d), "dow": dow(d)} for d in days], "rows": rows}


def fetch_week_summary() -> dict:
    """오른쪽 패널 기본 화면: 이번 주 요약 (pipeline 달력 + raw_data 점)"""
    _api("fetch_week_summary")
    DAYS = ["월", "화", "수", "목", "금", "토", "일"]
    mon = _monday()
    today_idx = NOW.weekday()

    items = []
    for p in MOCK["pipeline"]["products"]:
        st = p["history"][-1]
        d = MOCK["detail"].get(p["name"])
        w = MOCK["thisWeek"].get(p["name"], {})
        day, tm = (MOCK["schedule"].get(p["name"], "") + " ").split(" ")[:2]
        info = ""
        if st == "fail":
            info = f"{w.get('failAt', '')} 실패"
        if st == "run" and d:
            info = f"{module_progress(p['name'])} · {fmt_short(d['elapsedMin'])}"
        if st == "ok":
            dur = w.get("durMin")
            if d and d.get("summary"):
                dur = d["summary"]["recentDurMin"][-1]
            if dur:
                info = fmt_short(dur)
        if st == "sched":
            info = "예정"
        if st == "none":
            info = "실행 없음"
        items.append({"name": p["name"], "st": st, "info": info,
                      "day": DAYS.index(day) if day in DAYS else -1, "time": tm,
                      "pick": bool(p["clickable"] and d)})

    pipe_days = []
    for i, dn in enumerate(DAYS):
        dt = mon + timedelta(days=i)
        lst = sorted([it for it in items if it["day"] == i], key=lambda x: x["time"])
        pipe_days.append({"dn": dn, "md": md(dt), "items": lst})
    pipe_counts = {st: sum(it["st"] == st for it in items) for st in ("ok", "fail", "run", "sched")}

    # raw_data: 요일마다 제품별 점
    R = MOCK["rawData"]
    last = R["days"] - 1
    raw_counts = {"ok": 0, "fail": 0, "run": 0, "sched": 0}
    raw_cols = []
    for i, dn in enumerate(DAYS):
        dt = mon + timedelta(days=i)
        hi = last - (today_idx - i) if i <= today_idx else -1
        dots = [{"name": p["name"], "st": p["history"][-R["days"]:][hi] if hi >= 0 else "sched"}
                for p in R["products"]]
        if hi >= 0:
            for r in dots:
                if r["st"] in raw_counts:
                    raw_counts[r["st"]] += 1
        raw_cols.append({"dn": dn, "md": md(dt), "dots": dots})

    return {
        "range": f"{md(mon)} ~ {md(mon + timedelta(days=6))}",
        "todayIdx": today_idx,
        "pipe": {"counts": pipe_counts, "days": pipe_days},
        "raw": {"counts": raw_counts, "days": raw_cols},
    }


def fetch_pipeline_run(name: str, w: int) -> dict | None:
    """pipeline 실행 하나(제품 × 주차)의 상세 — 모듈×step 상태, 리소스 지표, 실행 중 Pod"""
    _api(f"fetch_pipeline_run({name}, {w})")
    d = _get_run(name, w)
    if not d:
        return None
    weeks = MOCK["pipeline"]["weeks"]
    finished = d["status"] in ("ok", "fail")
    wk = week_ranges(weeks)[w]
    out = {
        "kind": "pipe", "name": name, "w": w, "status": d["status"], "dag": d["dag"],
        "when": "이번 주" if w == weeks - 1 else f"{wk['start']}~{wk['end']}",
        "finished": finished, "steps": MOCK["steps"],
    }
    if d["status"] == "run":
        out["elapsed"] = fmt_elapsed(d["elapsedMin"])
    if finished:
        s, e = d["summary"]["start"], d["summary"]["end"]
        s = datetime.fromisoformat(s) if isinstance(s, str) else s
        e = datetime.fromisoformat(e) if isinstance(e, str) else e
        out["took"] = fmt_elapsed(round((e - s).total_seconds() / 60))
        out["startLabel"], out["endLabel"] = fmt_dt(s), fmt_hm(e)
    if d["status"] == "sched":
        out["scheduleText"], out["moduleCount"] = d.get("scheduleText"), d.get("moduleCount")
        return out
    out["modules"] = d["modules"]
    out["metrics"] = [[_cell_metric(d.get("seed", name), d, mod["name"], MOCK["steps"][i], c)
                       for i, c in enumerate(mod["cells"])] for mod in d["modules"]]
    out["pods"] = d.get("pods", [])
    return out


def fetch_raw_run(name: str, w: int) -> dict | None:
    """raw_data 실행 하나(제품 × 일자)의 상세 — 최근 N일 띠, 실행 정보, 리소스"""
    _api(f"fetch_raw_run({name}, {w})")
    r = _get_raw_run(name, w)
    if not r:
        return None
    R = MOCK["rawData"]
    last = R["days"] - 1
    finished = r["status"] != "run"
    days = raw_days()
    hist = next(x for x in R["products"] if x["name"] == name)["history"][-R["days"]:]

    strip = []
    for i, st in enumerate(hist):
        run = _get_raw_run(name, i)
        strip.append({"i": i, "st": st, "dow": dow(days[i]), "md": md(days[i]),
                      "pick": run is not None, "dur": fmt_short(run["durMin"]) if run else None})
    others = [_get_raw_run(name, i)["durMin"] for i, st in enumerate(hist) if st == "ok" and i != w]
    avg = js_round(mean(others)) if others else None
    diff = js_round((r["durMin"] / avg - 1) * 100) if avg and r["status"] == "ok" else None

    return {
        "kind": "raw", "name": name, "w": w, "status": r["status"], "dag": r["dag"],
        "when": "오늘" if w == last else f"{md(r['date'])} ({dow(r['date'])})",
        "finished": finished, "days": R["days"],
        "dur": fmt_elapsed(r["durMin"]), "startLabel": fmt_dt(r["start"]),
        "endLabel": fmt_hm(r["end"]) if r["end"] else None,
        "strip": strip,
        "diff": diff, "avg": fmt_elapsed(avg) if avg else None,
        "next": r["next"] if w == last else "",
        "note": r["note"],
        "pod": r.get("pod"), "res": r.get("res"),
    }
