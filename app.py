import streamlit as st
import pandas as pd
import json
import os
from datetime import date, datetime, timedelta

# ── 페이지 설정 ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="티켓 마케팅 대시보드",
    page_icon="🎫",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 데이터 파일 경로 ──────────────────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

FILES = {
    "schedules": os.path.join(DATA_DIR, "schedules.json"),    # 콘서트/컴백/팝업 일정
    "on_sale":   os.path.join(DATA_DIR, "on_sale.json"),      # 현재 판매중
    "past":      os.path.join(DATA_DIR, "past.json"),         # 판매 완료
}

SCHEDULE_TYPES = ["K-pop 콘서트", "J-pop 콘서트", "컴백", "팝업스토어", "스포츠"]

# ── 데이터 로드/저장 헬퍼 ────────────────────────────────────────────────────
def load(key: str) -> list[dict]:
    path = FILES[key]
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return []

def save(key: str, data: list[dict]):
    with open(FILES[key], "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)

def to_df(records: list[dict]) -> pd.DataFrame:
    if not records:
        return pd.DataFrame()
    df = pd.DataFrame(records)
    for col in df.columns:
        if "날짜" in col or "기간" in col or "date" in col.lower():
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df

# ── D-Day 계산 ───────────────────────────────────────────────────────────────
def dday(d) -> str:
    if pd.isna(d):
        return "-"
    diff = (d.date() - date.today()).days
    if diff == 0:
        return "D-Day"
    elif diff > 0:
        return f"D-{diff}"
    else:
        return f"D+{abs(diff)}"

# ── 상태 배지 색상 ────────────────────────────────────────────────────────────
def badge(label: str, color: str) -> str:
    return (
        f'<span style="background:{color};color:#fff;padding:2px 10px;'
        f'border-radius:12px;font-size:0.8em;font-weight:600">{label}</span>'
    )

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stSidebar"] {background: #0f0f1a;}
[data-testid="stSidebar"] * {color: #e0e0e0 !important;}
h1, h2, h3 {color: #6C63FF;}
.card {
    background: #1a1a2e; border-radius: 12px;
    padding: 16px 20px; margin-bottom: 12px;
    border-left: 4px solid #6C63FF;
}
.card-green  {border-left-color: #00c896;}
.card-orange {border-left-color: #ff9800;}
.card-gray   {border-left-color: #888;}
.metric-box {
    background: #1a1a2e; border-radius: 10px;
    padding: 18px; text-align: center;
}
.metric-box .num {font-size: 2.2em; font-weight: 700; color: #6C63FF;}
.metric-box .lbl {font-size: 0.85em; color: #aaa; margin-top: 4px;}
</style>
""", unsafe_allow_html=True)

# ── 사이드바 ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎫 마케팅 대시보드")
    st.markdown(f"**{date.today().strftime('%Y년 %m월 %d일')}** 기준")
    st.divider()
    page = st.radio(
        "페이지",
        ["📊 대시보드 홈", "📅 일정 관리", "🛒 판매중 티켓", "📋 판매 완료", "📈 QOO10 실적", "📥 데이터 업로드", "🗓️ QOO10 K-pop 캘린더"],
        label_visibility="collapsed",
    )
    st.divider()
    st.caption("데이터는 서버에 자동 저장됩니다")

# ════════════════════════════════════════════════════════════════════════════
# 페이지 1: 대시보드 홈
# ════════════════════════════════════════════════════════════════════════════
if page == "📊 대시보드 홈":
    st.title("📊 티켓 마케팅 대시보드")

    schedules = load("schedules")
    on_sale   = load("on_sale")
    past      = load("past")

    # 요약 지표
    upcoming = [s for s in schedules if s.get("날짜") and pd.to_datetime(s["날짜"], errors="coerce") >= pd.Timestamp(date.today())]
    this_month = [s for s in upcoming if pd.to_datetime(s["날짜"]).month == date.today().month]

    c1, c2, c3, c4 = st.columns(4)
    for col, num, lbl in [
        (c1, len(on_sale),   "현재 판매중 티켓"),
        (c2, len(upcoming),  "예정된 이벤트"),
        (c3, len(this_month),"이번달 이벤트"),
        (c4, len(past),      "판매 완료"),
    ]:
        col.markdown(
            f'<div class="metric-box"><div class="num">{num}</div>'
            f'<div class="lbl">{lbl}</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.subheader("🗓️ 다가오는 이벤트 (30일 이내)")
        cutoff = pd.Timestamp(date.today() + timedelta(days=30))
        soon = [s for s in upcoming if pd.to_datetime(s["날짜"], errors="coerce") <= cutoff]
        soon.sort(key=lambda x: x["날짜"])

        if not soon:
            st.info("30일 이내 예정된 이벤트가 없습니다.")
        for ev in soon[:10]:
            d = pd.to_datetime(ev["날짜"])
            dd = dday(d)
            color = "#6C63FF" if "콘서트" in ev.get("종류", "") else (
                "#00c896" if ev.get("종류") == "컴백" else "#ff9800"
            )
            st.markdown(
                f'<div class="card">'
                f'<b>{ev.get("아티스트", "-")}</b> &nbsp; {badge(ev.get("종류",""), color)}&nbsp;'
                f'{badge(dd, "#444")}<br>'
                f'<span style="color:#aaa;font-size:0.88em">'
                f'{d.strftime("%Y.%m.%d")} &nbsp;|&nbsp; {ev.get("장소", "-")}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

    with col_right:
        st.subheader("🛒 현재 판매중")
        if not on_sale:
            st.info("판매중인 티켓이 없습니다.")
        for ticket in on_sale[:6]:
            deadline = ticket.get("판매마감")
            dd_str = dday(pd.to_datetime(deadline, errors="coerce")) if deadline else "-"
            st.markdown(
                f'<div class="card card-green">'
                f'<b>{ticket.get("공연명", "-")}</b><br>'
                f'<span style="color:#aaa;font-size:0.85em">'
                f'{ticket.get("아티스트","-")} &nbsp;|&nbsp; {ticket.get("공연일","-")}<br>'
                f'판매 마감: {deadline or "-"} &nbsp; {badge(dd_str, "#00c896")}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

# ════════════════════════════════════════════════════════════════════════════
# 페이지 2: 일정 관리
# ════════════════════════════════════════════════════════════════════════════
elif page == "📅 일정 관리":
    st.title("📅 일정 관리")
    st.caption("K-pop/J-pop 콘서트·컴백·팝업스토어·스포츠 일정을 등록하고 관리합니다.")

    schedules = load("schedules")

    # 필터
    with st.expander("🔍 필터", expanded=True):
        fc1, fc2, fc3 = st.columns(3)
        keyword  = fc1.text_input("아티스트 검색", placeholder="아티스트명...")
        f_type   = fc2.multiselect("종류", SCHEDULE_TYPES, default=SCHEDULE_TYPES)
        f_period = fc3.selectbox("기간", ["전체", "이번달", "다음달", "3개월 이내"])

    df = to_df(schedules)
    if not df.empty:
        if keyword:
            df = df[df["아티스트"].str.contains(keyword, case=False, na=False)]
        if f_type:
            df = df[df["종류"].isin(f_type)]
        today_ts = pd.Timestamp(date.today())
        if f_period == "이번달":
            df = df[df["날짜"].dt.month == date.today().month]
        elif f_period == "다음달":
            nxt = (date.today().replace(day=1) + timedelta(days=32)).replace(day=1)
            df = df[(df["날짜"] >= pd.Timestamp(nxt)) & (df["날짜"].dt.month == nxt.month)]
        elif f_period == "3개월 이내":
            df = df[(df["날짜"] >= today_ts) & (df["날짜"] <= today_ts + timedelta(days=90))]
        df = df.sort_values("날짜", na_position="last")

    # 테이블 표시
    if df.empty:
        st.info("등록된 일정이 없습니다. 아래 폼으로 추가해 주세요.")
    else:
        df_show = df.copy()
        if "날짜" in df_show.columns:
            df_show["날짜"] = df_show["날짜"].dt.strftime("%Y.%m.%d")
            df_show.insert(0, "D-Day", df["날짜"].apply(dday))
        st.dataframe(df_show, use_container_width=True, hide_index=True)

    st.divider()

    # 신규 등록 폼
    with st.expander("➕ 새 일정 추가", expanded=False):
        with st.form("add_schedule", clear_on_submit=True):
            a1, a2 = st.columns(2)
            artist  = a1.text_input("아티스트 *", placeholder="예: IVE, BTS, 藤井風")
            ev_type = a2.selectbox("종류 *", SCHEDULE_TYPES)

            b1, b2 = st.columns(2)
            ev_date  = b1.date_input("날짜 *", value=date.today())
            venue    = b2.text_input("장소", placeholder="예: 도쿄돔, 오사카조홀")

            c1_, c2_ = st.columns(2)
            source   = c1_.text_input("정보 출처", placeholder="예: Weverse, 공식 SNS")
            link     = c2_.text_input("관련 링크", placeholder="https://...")
            note     = st.text_area("메모", placeholder="추가 정보를 입력하세요", height=80)

            submitted = st.form_submit_button("일정 추가", type="primary", use_container_width=True)
            if submitted:
                if not artist:
                    st.error("아티스트명은 필수입니다.")
                else:
                    schedules.append({
                        "아티스트": artist,
                        "종류": ev_type,
                        "날짜": str(ev_date),
                        "장소": venue,
                        "출처": source,
                        "링크": link,
                        "메모": note,
                        "등록일": str(date.today()),
                    })
                    save("schedules", schedules)
                    st.success(f"✅ {artist} 일정이 추가되었습니다!")
                    st.rerun()

    # 삭제
    if schedules:
        with st.expander("🗑️ 일정 삭제"):
            options = [
                f"{i}: {s.get('아티스트','-')} | {s.get('종류','-')} | {s.get('날짜','-')}"
                for i, s in enumerate(schedules)
            ]
            to_del = st.multiselect("삭제할 항목 선택", options)
            if st.button("선택 삭제", type="secondary"):
                indices = {int(o.split(":")[0]) for o in to_del}
                schedules = [s for i, s in enumerate(schedules) if i not in indices]
                save("schedules", schedules)
                st.success("삭제되었습니다.")
                st.rerun()

# ════════════════════════════════════════════════════════════════════════════
# 페이지 3: 판매중 티켓
# ════════════════════════════════════════════════════════════════════════════
elif page == "🛒 판매중 티켓":
    st.title("🛒 현재 판매중 티켓")
    st.caption("우리 사이트에서 현재 판매 중인 티켓 정보를 관리합니다.")

    on_sale = load("on_sale")
    df = to_df(on_sale)

    if df.empty:
        st.info("판매중인 티켓이 없습니다.")
    else:
        df_show = df.copy()
        for col in ["공연일", "판매마감"]:
            if col in df_show.columns:
                df_show[col] = pd.to_datetime(df_show[col], errors="coerce").dt.strftime("%Y.%m.%d")
        if "판매마감" in df.columns:
            df_show.insert(0, "D-Day", df["판매마감"].apply(dday))
        st.dataframe(df_show, use_container_width=True, hide_index=True)

    st.divider()

    with st.expander("➕ 판매 티켓 추가", expanded=False):
        with st.form("add_sale", clear_on_submit=True):
            s1, s2 = st.columns(2)
            title   = s1.text_input("공연명 *", placeholder="예: IVE Japan Tour 2025")
            artist  = s2.text_input("아티스트 *", placeholder="예: IVE")

            t1, t2 = st.columns(2)
            show_date = t1.date_input("공연 날짜 *", value=date.today())
            deadline  = t2.date_input("판매 마감일 *", value=date.today())

            u1, u2 = st.columns(2)
            venue   = u1.text_input("장소", placeholder="예: 마쿠하리멧세")
            price   = u2.text_input("티켓 가격", placeholder="예: ¥9,800~¥15,000")

            ticket_link = st.text_input("티켓 구매 링크 *", placeholder="https://...")
            note = st.text_area("메모/특이사항", height=70)

            sub = st.form_submit_button("추가", type="primary", use_container_width=True)
            if sub:
                if not title or not artist:
                    st.error("공연명과 아티스트는 필수입니다.")
                else:
                    on_sale.append({
                        "공연명": title,
                        "아티스트": artist,
                        "공연일": str(show_date),
                        "판매마감": str(deadline),
                        "장소": venue,
                        "가격": price,
                        "구매링크": ticket_link,
                        "메모": note,
                        "등록일": str(date.today()),
                    })
                    save("on_sale", on_sale)
                    st.success("✅ 티켓이 추가되었습니다!")
                    st.rerun()

    # 판매 완료로 이동
    if on_sale:
        with st.expander("✅ 판매 완료 처리"):
            opts = [
                f"{i}: {s.get('공연명','-')} | {s.get('아티스트','-')} | {s.get('공연일','-')}"
                for i, s in enumerate(on_sale)
            ]
            to_move = st.multiselect("완료 처리할 티켓", opts)
            if st.button("판매 완료로 이동", type="primary"):
                indices = {int(o.split(":")[0]) for o in to_move}
                moved = [s for i, s in enumerate(on_sale) if i in indices]
                on_sale = [s for i, s in enumerate(on_sale) if i not in indices]
                past = load("past")
                for m in moved:
                    m["완료일"] = str(date.today())
                    past.append(m)
                save("on_sale", on_sale)
                save("past", past)
                st.success(f"✅ {len(moved)}건이 판매 완료로 이동되었습니다.")
                st.rerun()

# ════════════════════════════════════════════════════════════════════════════
# 페이지 4: 판매 완료
# ════════════════════════════════════════════════════════════════════════════
elif page == "📋 판매 완료":
    st.title("📋 판매 완료 콘서트")
    st.caption("판매가 종료된 과거 티켓 이력입니다.")

    past = load("past")
    df = to_df(past)

    search = st.text_input("검색", placeholder="아티스트명 또는 공연명...")

    if df.empty:
        st.info("판매 완료된 티켓이 없습니다.")
    else:
        if search:
            mask = df.apply(lambda row: row.astype(str).str.contains(search, case=False).any(), axis=1)
            df = df[mask]
        for col in ["공연일", "판매마감", "완료일", "등록일"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime("%Y.%m.%d")
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.caption(f"총 {len(df)}건")

    # 수동 과거 기록 추가
    with st.expander("➕ 과거 판매 기록 직접 추가"):
        with st.form("add_past", clear_on_submit=True):
            p1, p2 = st.columns(2)
            title  = p1.text_input("공연명 *")
            artist = p2.text_input("아티스트 *")
            p3, p4 = st.columns(2)
            show_d = p3.date_input("공연 날짜", value=date.today())
            venue  = p4.text_input("장소")
            note   = st.text_area("메모", height=60)
            sub = st.form_submit_button("추가", type="primary", use_container_width=True)
            if sub:
                if not title or not artist:
                    st.error("공연명과 아티스트는 필수입니다.")
                else:
                    past = load("past")
                    past.append({
                        "공연명": title,
                        "아티스트": artist,
                        "공연일": str(show_d),
                        "장소": venue,
                        "메모": note,
                        "완료일": str(date.today()),
                    })
                    save("past", past)
                    st.success("추가되었습니다!")
                    st.rerun()

# ════════════════════════════════════════════════════════════════════════════
# 페이지 6: QOO10 실적 데이터
# ════════════════════════════════════════════════════════════════════════════
elif page == "📈 QOO10 실적":
    st.title("📈 QOO10 공연별 판매 실적")
    st.caption("Qoo10 TICKET.xlsx 데이터 기반 — 공연별 판매 건수·GMV·NB/RB 현황")

    qdata = load("qoo10_data") if os.path.exists(FILES.get("qoo10_data", "")) else []

    # FILES에 qoo10 경로 동적 추가
    q_path  = os.path.join(DATA_DIR, "qoo10_data.json")
    nb_path = os.path.join(DATA_DIR, "qoo10_nbrb.json")

    def load_json(path):
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        return []

    qdata = load_json(q_path)
    nbdata = load_json(nb_path)

    if not qdata:
        st.warning("데이터가 없습니다. 사이드바의 📥 데이터 업로드 또는 import_qoo10.py를 실행해 주세요.")
    else:
        df = pd.DataFrame(qdata)

        # ── 필터 ──────────────────────────────────────────────────────────
        with st.expander("🔍 필터", expanded=True):
            f1, f2, f3 = st.columns(3)
            years = sorted(df["연도"].dropna().unique().tolist())
            sel_years = f1.multiselect("연도", years, default=years)
            keyword = f2.text_input("공연명 검색", placeholder="예: MAMA, KCON...")
            has_sales = f3.checkbox("판매 데이터 있는 것만", value=False)

        df_f = df[df["연도"].isin(sel_years)].copy()
        if keyword:
            df_f = df_f[df_f["공연타이틀"].str.contains(keyword, case=False, na=False)]
        if has_sales:
            df_f = df_f[df_f["판매건수"].notna() & (df_f["판매건수"] > 0)]

        # ── 요약 지표 ──────────────────────────────────────────────────────
        total_sales  = df_f["판매건수"].sum(skipna=True)
        total_gmv    = df_f["총GMV"].sum(skipna=True)
        total_nb     = df_f["NB"].sum(skipna=True)
        total_buyers = df_f["구매자유니크"].sum(skipna=True)

        def fmt_gmv(v):
            if v >= 1_000_000_000:
                return f"¥{v/1_000_000_000:.1f}B"
            elif v >= 1_000_000:
                return f"¥{v/1_000_000:.0f}M"
            return f"¥{int(v):,}"

        m1, m2, m3, m4 = st.columns(4)
        for col, num, lbl in [
            (m1, f"{int(total_sales):,}건", "총 판매 건수"),
            (m2, fmt_gmv(total_gmv),        "총 판매 GMV"),
            (m3, f"{int(total_nb):,}명",    "New Buyer"),
            (m4, f"{int(total_buyers):,}명", "구매자 유니크"),
        ]:
            col.markdown(
                f'<div class="metric-box"><div class="num" style="font-size:1.6em">{num}</div>'
                f'<div class="lbl">{lbl}</div></div>',
                unsafe_allow_html=True,
            )

        st.markdown("---")

        # ── 탭: 공연별 데이터 / NB·RB ─────────────────────────────────────
        tab1, tab2 = st.tabs(["📋 공연별 데이터", "👥 NB/RB 분석"])

        with tab1:
            disp_cols = {
                "연도": "연도", "공연타이틀": "공연명", "판매기간": "판매기간",
                "판매건수": "판매건수", "판매매수": "판매매수",
                "구매자유니크": "구매자(유니크)",
                "총GMV": "총 GMV(¥)", "티켓GMV": "티켓 GMV(¥)",
                "NB": "NB", "RB": "RB", "NB_RB": "NB+RB", "스폰서십": "스폰서십(¥)",
            }
            df_show = df_f[[c for c in disp_cols if c in df_f.columns]].rename(columns=disp_cols).copy()

            for col in ["총 GMV(¥)", "티켓 GMV(¥)", "스폰서십(¥)"]:
                if col in df_show.columns:
                    df_show[col] = df_show[col].apply(
                        lambda x: f"¥{int(x):,}" if pd.notna(x) and x > 0 else ("-" if pd.isna(x) else str(int(x)))
                    )
            for col in ["판매건수", "판매매수", "구매자(유니크)", "NB", "RB", "NB+RB"]:
                if col in df_show.columns:
                    df_show[col] = df_show[col].apply(
                        lambda x: f"{int(x):,}" if pd.notna(x) else "-"
                    )

            st.dataframe(df_show, use_container_width=True, hide_index=True, height=420)
            st.caption(f"총 {len(df_show)}건 표시 중")

            # CSV 다운로드
            csv = df_f.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
            st.download_button("📥 CSV 다운로드", csv, "qoo10_실적.csv", "text/csv")

        with tab2:
            if not nbdata:
                st.info("NBRB 데이터가 없습니다.")
            else:
                nb_df = pd.DataFrame(nbdata)
                nb_df["NB비율%"] = (nb_df["NB비율"] * 100).round(2).apply(
                    lambda x: f"{x:.2f}%" if pd.notna(x) else "-"
                )
                for c in ["NB", "RB", "NB_RB", "기간중총NB"]:
                    nb_df[c] = nb_df[c].apply(lambda x: f"{int(x):,}" if pd.notna(x) else "-")

                nb_show = nb_df.rename(columns={
                    "이벤트기간": "이벤트 기간", "공연명": "공연명",
                    "NB": "New Buyer", "RB": "Reactive Buyer", "NB_RB": "NB+RB",
                    "기간중총NB": "기간중 총 NB", "NB비율%": "NB 비율",
                })
                st.dataframe(nb_show, use_container_width=True, hide_index=True, height=450)

    # ── 파일 재업로드 ──────────────────────────────────────────────────────
    with st.expander("🔄 Qoo10 TICKET.xlsx 다시 업로드"):
        up = st.file_uploader("새 버전 파일 선택", type=["xlsx", "xls"], key="qoo10_upload")
        if up:
            import tempfile, subprocess
            with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
                tmp.write(up.read())
                tmp_path = tmp.name
            try:
                xl2 = pd.ExcelFile(tmp_path)
                df_new = xl2.parse("공연별 데이터", header=None)
                df_new.columns = [
                    "연도", "공연타이틀", "셀러ID", "판매기간",
                    "NB", "RB", "NB_RB", "기간중총NB",
                    "판매건수", "판매매수", "응모자유니크", "구매자유니크",
                    "총GMV", "티켓GMV", "티켓외GMV", "스폰서십", "탈퇴수",
                ]
                df_new = df_new.iloc[3:].reset_index(drop=True)
                df_new = df_new[df_new["공연타이틀"].notna() & (df_new["공연타이틀"].astype(str).str.strip() != "")].copy()
                def to_year2(x):
                    try:
                        return str(int(float(x)))
                    except Exception:
                        return str(x) if pd.notna(x) else ""
                df_new["연도"] = df_new["연도"].apply(to_year2)
                nc = ["NB","RB","NB_RB","기간중총NB","판매건수","판매매수","응모자유니크","구매자유니크","총GMV","티켓GMV","티켓외GMV","스폰서십","탈퇴수"]
                for c in nc:
                    df_new[c] = pd.to_numeric(df_new[c].replace("-", None), errors="coerce")
                recs = df_new.to_dict(orient="records")
                with open(q_path, "w", encoding="utf-8") as f:
                    json.dump(recs, f, ensure_ascii=False, indent=2, default=str)
                st.success(f"✅ {len(recs)}건 업데이트 완료!")
                st.rerun()
            except Exception as e:
                st.error(f"파일 처리 오류: {e}")

# ════════════════════════════════════════════════════════════════════════════
# 페이지 7: QOO10 K-pop 캘린더
# ════════════════════════════════════════════════════════════════════════════
elif page == "📥 데이터 업로드":
    st.title("📥 CSV / Excel 업로드")
    st.caption("엑셀이나 CSV 파일로 데이터를 일괄 업로드할 수 있습니다.")

    target = st.selectbox(
        "업로드할 데이터 종류",
        ["일정 (schedules)", "판매중 티켓 (on_sale)", "판매 완료 (past)"],
    )
    key_map = {
        "일정 (schedules)": "schedules",
        "판매중 티켓 (on_sale)": "on_sale",
        "판매 완료 (past)": "past",
    }

    samples = {
        "일정 (schedules)": ["아티스트", "종류", "날짜(YYYY-MM-DD)", "장소", "출처", "링크", "메모"],
        "판매중 티켓 (on_sale)": ["공연명", "아티스트", "공연일", "판매마감", "장소", "가격", "구매링크", "메모"],
        "판매 완료 (past)": ["공연명", "아티스트", "공연일", "장소", "메모", "완료일"],
    }
    st.markdown(f"**필요한 열:** `{'`, `'.join(samples[target])}`")

    uploaded = st.file_uploader("파일 선택 (CSV 또는 Excel)", type=["csv", "xlsx", "xls"])
    mode = st.radio("업로드 방식", ["기존 데이터에 추가", "기존 데이터 덮어쓰기"], horizontal=True)

    if uploaded:
        try:
            if uploaded.name.endswith(".csv"):
                new_df = pd.read_csv(uploaded)
            else:
                new_df = pd.read_excel(uploaded)

            st.markdown("**미리보기 (처음 5행)**")
            st.dataframe(new_df.head(), use_container_width=True)
            st.caption(f"총 {len(new_df)}행 감지됨")

            if st.button("업로드 확정", type="primary"):
                k = key_map[target]
                new_records = new_df.fillna("").to_dict(orient="records")
                if mode == "기존 데이터에 추가":
                    existing = load(k)
                    existing.extend(new_records)
                    save(k, existing)
                else:
                    save(k, new_records)
                st.success(f"✅ {len(new_records)}건이 업로드되었습니다!")
        except Exception as e:
            st.error(f"파일 읽기 오류: {e}")

    st.divider()
    st.subheader("📤 현재 데이터 내보내기")
    export_target = st.selectbox("내보낼 데이터", list(key_map.keys()), key="export")
    export_data = load(key_map[export_target])
    if export_data:
        export_df = pd.DataFrame(export_data)
        csv_bytes = export_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
        st.download_button(
            label="CSV 다운로드",
            data=csv_bytes,
            file_name=f"{key_map[export_target]}_{date.today()}.csv",
            mime="text/csv",
        )
    else:
        st.info("내보낼 데이터가 없습니다.")

elif page == "🗓️ QOO10 K-pop 캘린더":
    import streamlit.components.v1 as components

    st.title("🗓️ QOO10 K-pop 캘린더")
    st.caption("QOO10 일본 K-pop 이벤트 캘린더를 실시간으로 확인합니다.")

    st.info(
        "💡 **활용 팁**: 아래 캘린더에서 확인한 일정을 '📅 일정 관리' 탭에 직접 추가해 대시보드와 연동하세요.",
        icon=None,
    )

    col_btn, col_open = st.columns([1, 3])
    col_btn.link_button(
        "🔗 QOO10에서 직접 열기",
        "https://www.qoo10.jp/gmkt.inc/Special/Special.aspx?sid=354625",
    )

    st.markdown("---")

    components.iframe(
        src="https://www.qoo10.jp/gmkt.inc/Special/Special.aspx?sid=354625",
        height=900,
        scrolling=True,
    )
