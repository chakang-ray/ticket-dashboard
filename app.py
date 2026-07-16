import streamlit as st
import pandas as pd
import json
import os
import base64
import uuid
from datetime import date, timedelta

# ── 페이지 설정 ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="티켓 마케팅 대시보드",
    page_icon="🎫",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 경로 ─────────────────────────────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
IMG_DIR  = os.path.join(DATA_DIR, "images")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(IMG_DIR,  exist_ok=True)

FILES = {
    "on_sale": os.path.join(DATA_DIR, "on_sale.json"),
}

# ── 헬퍼 ─────────────────────────────────────────────────────────────────────
def load(key: str) -> list[dict]:
    path = FILES[key]
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return []

def save(key: str, data: list[dict]):
    with open(FILES[key], "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)

def load_json(path: str) -> list[dict]:
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return []

def dday(d) -> str:
    try:
        target = pd.to_datetime(d)
        if pd.isna(target):
            return "-"
        diff = (target.date() - date.today()).days
        if diff == 0:  return "D-Day"
        elif diff > 0: return f"D-{diff}"
        else:          return f"D+{abs(diff)}"
    except Exception:
        return "-"

def badge(label: str, color: str) -> str:
    return (
        f'<span style="background:{color};color:#fff;padding:2px 10px;'
        f'border-radius:12px;font-size:0.8em;font-weight:600">{label}</span>'
    )

def save_image(uploaded_file) -> str:
    ext   = uploaded_file.name.rsplit(".", 1)[-1].lower()
    fname = f"{uuid.uuid4().hex}.{ext}"
    with open(os.path.join(IMG_DIR, fname), "wb") as f:
        f.write(uploaded_file.getbuffer())
    return fname

def img_to_b64(fname: str):
    path = os.path.join(IMG_DIR, fname)
    if fname and os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

def format_dates(date_range) -> str:
    """date_input 범위 결과 → 표시용 문자열"""
    if not date_range:
        return ""
    if isinstance(date_range, (list, tuple)):
        if len(date_range) == 2 and date_range[0] != date_range[1]:
            return f"{date_range[0].strftime('%Y.%m.%d')} ~ {date_range[1].strftime('%Y.%m.%d')}"
        return date_range[0].strftime("%Y.%m.%d")
    return str(date_range)

def store_dates(date_range) -> str:
    """date_input 범위 결과 → JSON 저장용 문자열"""
    if not date_range:
        return ""
    if isinstance(date_range, (list, tuple)):
        if len(date_range) == 2 and date_range[0] != date_range[1]:
            return f"{date_range[0]} ~ {date_range[1]}"
        return str(date_range[0])
    return str(date_range)

def first_date_str(date_str: str) -> str:
    """저장된 날짜 문자열에서 첫 번째 날짜만 추출 (D-Day 계산용)"""
    return date_str.split("~")[0].strip() if date_str else ""

def parse_date_range(date_str: str):
    """저장된 공연일 문자열 → date_input value 튜플"""
    try:
        if "~" in date_str:
            parts = date_str.split("~")
            s = pd.to_datetime(parts[0].strip()).date()
            e = pd.to_datetime(parts[1].strip()).date()
            return (s, e)
        d = pd.to_datetime(date_str.strip()).date()
        return (d, d)
    except Exception:
        return (date.today(), date.today())

def parse_single_date(date_str: str):
    """저장된 날짜 문자열 → date 객체"""
    try:
        return pd.to_datetime(date_str.strip()).date()
    except Exception:
        return date.today()

def _render_ticket_card(ticket: dict):
    fname    = ticket.get("썸네일", "")
    b64      = img_to_b64(fname) if fname else None
    deadline = ticket.get("판매마감", "")
    dd_str   = dday(first_date_str(deadline)) if deadline else "-"
    dd_color = "#00c896" if not dd_str.startswith("D+") else "#888"

    link_btn = ""
    if ticket.get("구매링크"):
        link_btn += (
            f'<a href="{ticket["구매링크"]}" target="_blank" '
            f'style="background:#6C63FF;color:#fff;padding:5px 14px;border-radius:8px;'
            f'text-decoration:none;font-size:0.82em;font-weight:600;margin-right:6px">🔗 구매 링크</a>'
        )
    if ticket.get("공식사이트"):
        link_btn += (
            f'<a href="{ticket["공식사이트"]}" target="_blank" '
            f'style="background:#00b894;color:#fff;padding:5px 14px;border-radius:8px;'
            f'text-decoration:none;font-size:0.82em;font-weight:600">🌐 공식 사이트</a>'
        )

    if b64:
        ext        = fname.rsplit(".", 1)[-1]
        thumb_html = f'<img class="ticket-thumb" src="data:image/{ext};base64,{b64}">'
    else:
        thumb_html = '<div class="ticket-thumb-placeholder">🎫</div>'

    공연일_표시 = ticket.get("공연일", "-")

    st.markdown(
        f'<div class="ticket-card">'
        f'{thumb_html}'
        f'<div class="ticket-body">'
        f'<div class="ticket-title">{ticket.get("공연명", "-")}</div>'
        f'<div class="ticket-sub">'
        f'🎤 {ticket.get("아티스트", "-")}<br>'
        f'📅 {공연일_표시}<br>'
        f'📍 {ticket.get("장소", "-")}'
        f'</div></div>'
        f'<div class="ticket-footer">'
        f'{badge(dd_str, dd_color)}'
        f'<span style="color:#aaa;font-size:0.8em">마감 {deadline or "-"}</span>'
        f'&nbsp;{link_btn}'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    if ticket.get("메모"):
        st.caption(f"📝 {ticket['메모']}")

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stSidebar"] {background: #0f0f1a;}
[data-testid="stSidebar"] * {color: #e0e0e0 !important;}
h1, h2, h3 {color: #6C63FF;}
.metric-box {
    background: #1a1a2e; border-radius: 10px;
    padding: 18px; text-align: center;
}
.metric-box .num {font-size: 2.2em; font-weight: 700; color: #6C63FF;}
.metric-box .lbl {font-size: 0.85em; color: #aaa; margin-top: 4px;}
.ticket-card {
    background: #1a1a2e; border-radius: 14px;
    overflow: hidden; margin-bottom: 20px;
    border: 1px solid #2a2a4a;
}
.ticket-card:hover {box-shadow: 0 4px 20px rgba(108,99,255,0.3);}
.ticket-thumb {
    width: 100%; aspect-ratio: 16/9;
    object-fit: cover; display: block;
}
.ticket-thumb-placeholder {
    width: 100%; aspect-ratio: 16/9;
    background: linear-gradient(135deg, #1a1a3e, #2a2a5e);
    display: flex; align-items: center; justify-content: center;
    font-size: 3em;
}
.ticket-body  {padding: 14px 16px;}
.ticket-title {font-size: 1.05em; font-weight: 700; color: #fff; margin-bottom: 4px;}
.ticket-sub   {font-size: 0.82em; color: #aaa; line-height: 1.7;}
.ticket-footer{
    padding: 10px 16px; border-top: 1px solid #2a2a4a;
    display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
}
</style>
""", unsafe_allow_html=True)

# ── 사이드바 ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎫 마케팅 대시보드")
    st.markdown(f"**{date.today().strftime('%Y년 %m월 %d일')}** 기준")
    st.divider()
    page = st.radio(
        "페이지",
        ["📊 대시보드 홈", "🛒 판매중 티켓", "📈 QOO10 실적", "🏟️ 공연장 정보", "🗓️ QOO10 K-pop 캘린더"],
        label_visibility="collapsed",
    )
    st.divider()
    st.caption("데이터는 로컬에 자동 저장됩니다")

# ════════════════════════════════════════════════════════════════════════════
# 1. 대시보드 홈
# ════════════════════════════════════════════════════════════════════════════
if page == "📊 대시보드 홈":
    st.title("📊 티켓 마케팅 대시보드")

    on_sale = load("on_sale")

    # ── 요약 지표 ─────────────────────────────────────────────────────────
    col_m, col_s = st.columns([1, 4])
    with col_m:
        st.markdown(
            f'<div class="metric-box"><div class="num">{len(on_sale)}</div>'
            f'<div class="lbl">현재 판매중 티켓</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.subheader("🛒 현재 판매중 티켓")

    if not on_sale:
        st.info("판매중인 티켓이 없습니다. '🛒 판매중 티켓' 탭에서 추가해 주세요.")
    else:
        # 판매마감 D-Day 순으로 정렬
        def sort_key(t):
            d = first_date_str(t.get("판매마감", ""))
            try:    return pd.to_datetime(d)
            except: return pd.Timestamp("2099-12-31")

        tickets_sorted = sorted(on_sale, key=sort_key)
        cols_per_row = 3
        for row_start in range(0, len(tickets_sorted), cols_per_row):
            cols = st.columns(cols_per_row)
            for ci, ti in enumerate(range(row_start, min(row_start + cols_per_row, len(tickets_sorted)))):
                with cols[ci]:
                    _render_ticket_card(tickets_sorted[ti])


# ════════════════════════════════════════════════════════════════════════════
# 2. 판매중 티켓
# ════════════════════════════════════════════════════════════════════════════
elif page == "🛒 판매중 티켓":
    st.title("🛒 현재 판매중 티켓")
    st.caption("우리 사이트에서 현재 판매 중인 티켓을 카드 형태로 관리합니다.")

    on_sale = load("on_sale")

    # ── 카드 그리드 ───────────────────────────────────────────────────────
    if not on_sale:
        st.info("판매중인 티켓이 없습니다. 아래 폼에서 추가해 주세요.")
    else:
        cols_per_row = 3
        for row_start in range(0, len(on_sale), cols_per_row):
            cols = st.columns(cols_per_row)
            for ci, ti in enumerate(range(row_start, min(row_start + cols_per_row, len(on_sale)))):
                with cols[ci]:
                    _render_ticket_card(on_sale[ti])

    st.divider()

    # ── 티켓 추가 폼 ──────────────────────────────────────────────────────
    with st.expander("➕ 판매 티켓 추가", expanded=False):
        with st.form("add_sale", clear_on_submit=True):
            s1, s2 = st.columns(2)
            title  = s1.text_input("공연명 *", placeholder="예: IVE Japan Tour 2025")
            artist = s2.text_input("아티스트 *", placeholder="예: IVE")

            # 공연 기간 (날짜 범위 선택)
            show_dates = st.date_input(
                "공연 기간 * (하루짜리면 같은 날짜 선택, 여러 날이면 시작일~종료일 선택)",
                value=(date.today(), date.today()),
            )

            t1, t2 = st.columns(2)
            deadline = t1.date_input("판매 마감일 *", value=date.today())
            venue    = t2.text_input("장소", placeholder="예: 마쿠하리멧세")

            lc, rc = st.columns(2)
            ticket_link   = lc.text_input("티켓 구매 링크", placeholder="https://...")
            official_link = rc.text_input("공식 사이트 링크", placeholder="https://...")
            thumb_file  = st.file_uploader(
                "썸네일 이미지 (JPG / PNG / GIF / WEBP)",
                type=["jpg", "jpeg", "png", "gif", "webp"],
            )
            note = st.text_area("메모/특이사항", height=70)

            if st.form_submit_button("추가", type="primary", use_container_width=True):
                if not title or not artist:
                    st.error("공연명과 아티스트는 필수입니다.")
                else:
                    fname = save_image(thumb_file) if thumb_file else ""
                    on_sale.append({
                        "공연명":   title,
                        "아티스트": artist,
                        "공연일":   store_dates(show_dates),
                        "판매마감": str(deadline),
                        "장소":     venue,
                        "구매링크":   ticket_link,
                        "공식사이트": official_link,
                        "썸네일":   fname,
                        "메모":     note,
                        "등록일":   str(date.today()),
                    })
                    save("on_sale", on_sale)
                    st.success("✅ 티켓이 추가되었습니다!")
                    st.rerun()

    # ── 티켓 수정 ─────────────────────────────────────────────────────────
    if on_sale:
        with st.expander("✏️ 티켓 수정", expanded=False):
            edit_opts = [
                f"{i}: {s.get('공연명','-')} | {s.get('아티스트','-')} | {s.get('공연일','-')}"
                for i, s in enumerate(on_sale)
            ]
            # 선택한 티켓 번호를 세션에 유지
            if "edit_sel" not in st.session_state:
                st.session_state["edit_sel"] = edit_opts[0]

            sel = st.selectbox(
                "수정할 티켓 선택",
                edit_opts,
                key="edit_sel",
            )
            edit_idx = int(sel.split(":")[0])
            t = on_sale[edit_idx]

            # 현재 값으로 폼 pre-fill
            cur_dates    = parse_date_range(t.get("공연일", ""))
            cur_deadline = parse_single_date(t.get("판매마감", ""))

            with st.form("edit_sale"):
                e1, e2 = st.columns(2)
                new_title  = e1.text_input("공연명 *",  value=t.get("공연명", ""))
                new_artist = e2.text_input("아티스트 *", value=t.get("아티스트", ""))

                new_dates = st.date_input(
                    "공연 기간 * (하루면 같은 날 두 번 / 여러 날이면 시작일~종료일)",
                    value=cur_dates,
                )

                f1, f2 = st.columns(2)
                new_deadline = f1.date_input("판매 마감일 *", value=cur_deadline)
                new_venue    = f2.text_input("장소", value=t.get("장소", ""))

                el, er = st.columns(2)
                new_link     = el.text_input("티켓 구매 링크", value=t.get("구매링크", ""))
                new_official = er.text_input("공식 사이트 링크", value=t.get("공식사이트", ""))

                # 현재 썸네일 미리보기
                cur_fname = t.get("썸네일", "")
                if cur_fname:
                    b64_cur = img_to_b64(cur_fname)
                    if b64_cur:
                        ext_cur = cur_fname.rsplit(".", 1)[-1]
                        st.markdown(
                            f'<img src="data:image/{ext_cur};base64,{b64_cur}" '
                            f'style="height:80px;border-radius:8px;margin-bottom:6px">',
                            unsafe_allow_html=True,
                        )
                        st.caption("현재 썸네일 — 새 이미지를 올리면 교체됩니다")

                new_thumb = st.file_uploader(
                    "썸네일 이미지 교체 (선택, JPG / PNG / GIF / WEBP)",
                    type=["jpg", "jpeg", "png", "gif", "webp"],
                    key="edit_thumb",
                )
                new_note = st.text_area("메모/특이사항", value=t.get("메모", ""), height=70)

                if st.form_submit_button("저장", type="primary", use_container_width=True):
                    if not new_title or not new_artist:
                        st.error("공연명과 아티스트는 필수입니다.")
                    else:
                        # 이미지: 새로 올리면 교체, 없으면 기존 유지
                        if new_thumb:
                            if cur_fname:
                                old_path = os.path.join(IMG_DIR, cur_fname)
                                if os.path.exists(old_path):
                                    os.remove(old_path)
                            new_fname = save_image(new_thumb)
                        else:
                            new_fname = cur_fname

                        on_sale[edit_idx] = {
                            **t,  # 등록일 등 기존 메타 유지
                            "공연명":   new_title,
                            "아티스트": new_artist,
                            "공연일":   store_dates(new_dates),
                            "판매마감": str(new_deadline),
                            "장소":     new_venue,
                            "구매링크":   new_link,
                            "공식사이트": new_official,
                            "썸네일":   new_fname,
                            "메모":     new_note,
                        }
                        save("on_sale", on_sale)
                        st.success("✅ 수정이 완료되었습니다!")
                        st.rerun()

    # ── 티켓 삭제 ─────────────────────────────────────────────────────────
    if on_sale:
        with st.expander("🗑️ 티켓 삭제"):
            opts = [
                f"{i}: {s.get('공연명','-')} | {s.get('아티스트','-')} | {s.get('공연일','-')}"
                for i, s in enumerate(on_sale)
            ]
            to_del = st.multiselect("삭제할 티켓 선택", opts)
            if st.button("선택 삭제", type="secondary"):
                indices = {int(o.split(":")[0]) for o in to_del}
                for i in indices:
                    fname = on_sale[i].get("썸네일", "")
                    if fname:
                        img_path = os.path.join(IMG_DIR, fname)
                        if os.path.exists(img_path):
                            os.remove(img_path)
                on_sale = [s for i, s in enumerate(on_sale) if i not in indices]
                save("on_sale", on_sale)
                st.success("삭제되었습니다.")
                st.rerun()

    # ── Excel / CSV 일괄 업로드 ───────────────────────────────────────────
    with st.expander("📥 Excel / CSV 파일로 일괄 등록"):
        st.caption("필요한 열: 공연명, 아티스트, 공연일, 판매마감, 장소, 구매링크, 메모")
        up   = st.file_uploader("파일 선택", type=["csv", "xlsx", "xls"], key="bulk_sale")
        mode = st.radio("업로드 방식", ["기존 데이터에 추가", "기존 데이터 덮어쓰기"], horizontal=True)
        if up:
            try:
                new_df = pd.read_csv(up) if up.name.endswith(".csv") else pd.read_excel(up)
                st.dataframe(new_df.head(), use_container_width=True)
                st.caption(f"총 {len(new_df)}행")
                if st.button("업로드 확정", type="primary"):
                    new_recs = new_df.fillna("").to_dict(orient="records")
                    base     = load("on_sale") if mode == "기존 데이터에 추가" else []
                    base.extend(new_recs)
                    save("on_sale", base)
                    st.success(f"✅ {len(new_recs)}건 업로드 완료!")
                    st.rerun()
            except Exception as e:
                st.error(f"파일 오류: {e}")

# ════════════════════════════════════════════════════════════════════════════
# 3. QOO10 실적
# ════════════════════════════════════════════════════════════════════════════
elif page == "📈 QOO10 실적":
    st.title("📈 QOO10 공연별 판매 실적")
    st.caption("Qoo10 TICKET.xlsx 데이터 기반 — 공연별 판매 건수·GMV·NB/RB 현황")

    q_path  = os.path.join(DATA_DIR, "qoo10_data.json")
    nb_path = os.path.join(DATA_DIR, "qoo10_nbrb.json")
    qdata   = load_json(q_path)
    nbdata  = load_json(nb_path)

    if not qdata:
        st.warning("데이터가 없습니다. 아래에서 파일을 업로드해 주세요.")
    else:
        df = pd.DataFrame(qdata)

        with st.expander("🔍 필터", expanded=True):
            f1, f2, f3 = st.columns(3)
            years     = sorted(df["연도"].dropna().unique().tolist())
            sel_years = f1.multiselect("연도", years, default=years)
            keyword   = f2.text_input("공연명 검색", placeholder="예: MAMA, KCON...")
            has_sales = f3.checkbox("판매 데이터 있는 것만", value=False)

        df_f = df[df["연도"].isin(sel_years)].copy()
        if keyword:
            df_f = df_f[df_f["공연타이틀"].str.contains(keyword, case=False, na=False)]
        if has_sales:
            df_f = df_f[df_f["판매건수"].notna() & (df_f["판매건수"] > 0)]

        def fmt_gmv(v):
            if v >= 1_000_000_000: return f"¥{v/1_000_000_000:.1f}B"
            elif v >= 1_000_000:   return f"¥{v/1_000_000:.0f}M"
            return f"¥{int(v):,}"

        m1, m2, m3, m4 = st.columns(4)
        for col, num, lbl in [
            (m1, f"{int(df_f['판매건수'].sum(skipna=True)):,}건",     "총 판매 건수"),
            (m2, fmt_gmv(df_f['총GMV'].sum(skipna=True)),             "총 판매 GMV"),
            (m3, f"{int(df_f['NB'].sum(skipna=True)):,}명",           "New Buyer"),
            (m4, f"{int(df_f['구매자유니크'].sum(skipna=True)):,}명", "구매자 유니크"),
        ]:
            col.markdown(
                f'<div class="metric-box"><div class="num" style="font-size:1.6em">{num}</div>'
                f'<div class="lbl">{lbl}</div></div>',
                unsafe_allow_html=True,
            )

        st.markdown("---")
        tab1, tab2 = st.tabs(["📋 공연별 데이터", "👥 NB/RB 분석"])

        with tab1:
            disp_cols = {
                "연도": "연도", "공연타이틀": "공연명", "공연장": "공연장", "판매기간": "판매기간",
                "판매건수": "판매건수", "판매매수": "판매매수",
                "구매자유니크": "구매자(유니크)",
                "총GMV": "총 GMV(¥)", "티켓GMV": "티켓 GMV(¥)",
                "NB": "NB", "RB": "RB", "NB_RB": "NB+RB", "스폰서십": "스폰서십(¥)",
            }
            df_show = df_f[[c for c in disp_cols if c in df_f.columns]].rename(columns=disp_cols).copy()
            for c in ["총 GMV(¥)", "티켓 GMV(¥)", "스폰서십(¥)"]:
                if c in df_show.columns:
                    df_show[c] = df_show[c].apply(
                        lambda x: f"¥{int(x):,}" if pd.notna(x) and x > 0 else ("-" if pd.isna(x) else str(int(x)))
                    )
            for c in ["판매건수", "판매매수", "구매자(유니크)", "NB", "RB", "NB+RB"]:
                if c in df_show.columns:
                    df_show[c] = df_show[c].apply(lambda x: f"{int(x):,}" if pd.notna(x) else "-")
            st.dataframe(df_show, use_container_width=True, hide_index=True, height=420)
            st.caption(f"총 {len(df_show)}건 표시 중")
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
                st.dataframe(
                    nb_df.rename(columns={
                        "이벤트기간": "이벤트 기간", "NB": "New Buyer",
                        "RB": "Reactive Buyer", "NB_RB": "NB+RB",
                        "기간중총NB": "기간중 총 NB", "NB비율%": "NB 비율",
                    }),
                    use_container_width=True, hide_index=True, height=450,
                )

    with st.expander("🔄 Qoo10 TICKET.xlsx 다시 업로드"):
        up = st.file_uploader("새 버전 파일 선택", type=["xlsx", "xls"], key="qoo10_upload")
        if up:
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
                tmp.write(up.read())
                tmp_path = tmp.name
            try:
                xl2    = pd.ExcelFile(tmp_path)
                df_new = xl2.parse("공연별 데이터", header=None)
                df_new.columns = [
                    "연도", "공연타이틀", "셀러ID", "판매기간",
                    "NB", "RB", "NB_RB", "기간중총NB",
                    "공연장",
                    "판매건수", "판매매수", "응모자유니크", "구매자유니크",
                    "총GMV", "티켓GMV", "티켓외GMV", "스폰서십", "탈퇴수",
                ]
                df_new = df_new.iloc[3:].reset_index(drop=True)
                df_new = df_new[df_new["공연타이틀"].notna() & (df_new["공연타이틀"].astype(str).str.strip() != "")].copy()
                def to_year2(x):
                    try:    return str(int(float(x)))
                    except: return str(x) if pd.notna(x) else ""
                df_new["연도"] = df_new["연도"].apply(to_year2)
                for c in ["NB","RB","NB_RB","기간중총NB","판매건수","판매매수","응모자유니크","구매자유니크","총GMV","티켓GMV","티켓외GMV","스폰서십","탈퇴수"]:
                    df_new[c] = pd.to_numeric(df_new[c].replace("-", None), errors="coerce")
                with open(q_path, "w", encoding="utf-8") as f:
                    json.dump(df_new.to_dict(orient="records"), f, ensure_ascii=False, indent=2, default=str)
                st.success(f"✅ {len(df_new)}건 업데이트 완료!")
                st.rerun()
            except Exception as e:
                st.error(f"파일 처리 오류: {e}")

# ════════════════════════════════════════════════════════════════════════════
# 4. 공연장 정보
# ════════════════════════════════════════════════════════════════════════════
elif page == "🏟️ 공연장 정보":
    VENUES_PATH = os.path.join(DATA_DIR, "venues.json")
    venues_all: list[dict] = load_json(VENUES_PATH)

    st.title("🏟️ 일본 주요 공연장 정보")
    st.caption("도쿄·오사카·나고야·후쿠오카·삿포로 등 수용 인원 1,000명 이상 주요 공연장 데이터")

    # ── 검색 & 필터 ────────────────────────────────────────────────────────
    col_s, col_c, col_t, col_cap = st.columns([3, 2, 2, 2])

    keyword = col_s.text_input("🔍 검색", placeholder="공연장명·주소·역명 등")

    cities = sorted({v.get("도시", "") for v in venues_all})
    city_opts = ["전체"] + cities
    sel_city = col_c.selectbox("도시", city_opts)

    types = sorted({v.get("시설구분", "") for v in venues_all})
    type_opts = ["전체"] + types
    sel_type = col_t.selectbox("시설 유형", type_opts)

    cap_opts = {"전체": 0, "1,000+": 1000, "5,000+": 5000, "10,000+": 10000, "30,000+": 30000}
    sel_cap_label = col_cap.selectbox("최소 수용 인원", list(cap_opts.keys()))
    sel_cap = cap_opts[sel_cap_label]

    # ── 필터 적용 ───────────────────────────────────────────────────────────
    filtered = venues_all
    if keyword:
        kw = keyword.lower()
        filtered = [
            v for v in filtered
            if kw in v.get("공연장명", "").lower()
            or kw in v.get("주소", "").lower()
            or kw in v.get("최가까운역", "").lower()
            or kw in v.get("비고", "").lower()
            or kw in v.get("도시", "").lower()
        ]
    if sel_city != "전체":
        filtered = [v for v in filtered if v.get("도시") == sel_city]
    if sel_type != "전체":
        filtered = [v for v in filtered if v.get("시설구분") == sel_type]
    if sel_cap > 0:
        filtered = [v for v in filtered if v.get("수용인원", 0) >= sel_cap]

    st.markdown(f"**{len(filtered)}개** 공연장 표시 중")
    st.divider()

    # ── 시설 유형 색상 ─────────────────────────────────────────────────────
    TYPE_COLOR = {
        "ドーム":    "#FF6B6B",
        "アリーナ":  "#6C63FF",
        "ホール":    "#00C896",
        "野外":      "#FF9F43",
        "ライブハウス": "#A29BFE",
        "スタジアム": "#E17055",
        "屋内広場":  "#74B9FF",
    }

    # ── 카드 그리드 ─────────────────────────────────────────────────────────
    COLS = 2
    for row_start in range(0, len(filtered), COLS):
        row_venues = filtered[row_start: row_start + COLS]
        cols = st.columns(COLS)
        for col, v in zip(cols, row_venues):
            vtype = v.get("시설구분", "")
            tcolor = TYPE_COLOR.get(vtype, "#888")
            cap_fmt = f"{v.get('수용인원', 0):,}"
            site_url = v.get("공식홈페이지", "")
            site_btn = (
                f'<a href="{site_url}" target="_blank" '
                f'style="background:#6C63FF;color:#fff;padding:4px 12px;border-radius:8px;'
                f'text-decoration:none;font-size:0.8em;font-weight:600">🌐 공식 홈페이지</a>'
            ) if site_url else ""

            col.markdown(
                f"""
<div style="background:#1e1e2e;border:1px solid #333;border-radius:12px;padding:18px 20px;margin-bottom:12px;height:100%">
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px">
    <span style="background:{tcolor};color:#fff;padding:2px 10px;border-radius:12px;font-size:0.75em;font-weight:700">{vtype}</span>
    <span style="color:#aaa;font-size:0.8em">{v.get('도시', '')}</span>
  </div>
  <div style="font-size:1.1em;font-weight:700;color:#fff;margin-bottom:6px">{v.get('공연장명', '')}</div>
  <div style="color:#6C63FF;font-size:1.4em;font-weight:800;margin-bottom:10px">👥 {cap_fmt}명</div>
  <table style="width:100%;font-size:0.83em;color:#ccc;border-collapse:collapse">
    <tr><td style="padding:3px 8px 3px 0;color:#888;white-space:nowrap">📮 우편번호</td><td>〒{v.get('우편번호','')}</td></tr>
    <tr><td style="padding:3px 8px 3px 0;color:#888;white-space:nowrap">📍 주소</td><td>{v.get('주소','')}</td></tr>
    <tr><td style="padding:3px 8px 3px 0;color:#888;white-space:nowrap">📞 전화</td><td>{v.get('전화번호','')}</td></tr>
    <tr><td style="padding:3px 8px 3px 0;color:#888;white-space:nowrap">🚉 가까운 역</td><td>{v.get('최가까운역','')}</td></tr>
    <tr><td style="padding:3px 8px 3px 0;color:#888;white-space:nowrap;vertical-align:top">💬 비고</td><td style="color:#aaa">{v.get('비고','')}</td></tr>
  </table>
  <div style="margin-top:12px">{site_btn}</div>
</div>
""",
                unsafe_allow_html=True,
            )

    if not filtered:
        st.info("검색 조건에 맞는 공연장이 없습니다.")

    # ── 엑셀 다운로드 ───────────────────────────────────────────────────────
    st.divider()
    if filtered:
        df_venues = pd.DataFrame(filtered).drop(columns=["id"], errors="ignore")
        rename_map = {
            "공연장명": "공연장명",
            "도시": "도시",
            "도도부현": "도도부현",
            "시설구분": "시설구분",
            "수용인원": "수용인원",
            "우편번호": "우편번호",
            "주소": "주소",
            "전화번호": "전화번호",
            "공식홈페이지": "공식홈페이지",
            "최가까운역": "최가까운역",
            "비고": "비고",
        }
        df_venues = df_venues.rename(columns=rename_map)

        import io
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            df_venues.to_excel(writer, index=False, sheet_name="공연장정보")
        buf.seek(0)
        st.download_button(
            "⬇️ 현재 목록 엑셀 다운로드",
            data=buf,
            file_name="일본_주요공연장_정보.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

# 5. QOO10 K-pop 캘린더
# ════════════════════════════════════════════════════════════════════════════
elif page == "🗓️ QOO10 K-pop 캘린더":
    import streamlit.components.v1 as components

    st.title("🗓️ QOO10 K-pop 캘린더")
    st.caption("QOO10 일본 K-pop 이벤트 캘린더를 실시간으로 확인합니다.")

    st.link_button("🔗 QOO10에서 직접 열기", "https://www.qoo10.jp/gmkt.inc/Special/Special.aspx?sid=354625")
    st.markdown("---")
    components.iframe(
        src="https://www.qoo10.jp/gmkt.inc/Special/Special.aspx?sid=354625",
        height=900, scrolling=True,
    )
