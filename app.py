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
    "on_sale":     os.path.join(DATA_DIR, "on_sale.json"),
    "kpop_idols":  os.path.join(DATA_DIR, "kpop_idols.json"),
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

def _render_ticket_card(ticket: dict, sold_out: bool = False):
    fname    = ticket.get("썸네일", "")
    b64      = img_to_b64(fname) if fname else None
    deadline = ticket.get("판매마감", "")
    dd_str   = dday(first_date_str(deadline)) if deadline else "-"
    dd_color = "#00c896" if not dd_str.startswith("D+") else "#888"

    link_btn = ""
    if not sold_out:
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
                f'text-decoration:none;font-size:0.82em;font-weight:600;margin-right:6px">🌐 공식 사이트</a>'
            )
        if ticket.get("응모현황링크"):
            link_btn += (
                f'<a href="{ticket["응모현황링크"]}" target="_blank" '
                f'style="background:#FF6B35;color:#fff;padding:5px 14px;border-radius:8px;'
                f'text-decoration:none;font-size:0.82em;font-weight:600">📊 응모/판매현황</a>'
            )

    if b64:
        ext        = fname.rsplit(".", 1)[-1]
        thumb_html = f'<img class="ticket-thumb" src="data:image/{ext};base64,{b64}" style="{"filter:grayscale(70%);opacity:0.6" if sold_out else ""}">'
    else:
        thumb_html = '<div class="ticket-thumb-placeholder">🎫</div>'

    공연일_표시 = ticket.get("공연일", "-")
    sold_banner = (
        '<div style="background:#555;color:#fff;text-align:center;padding:5px;'
        'font-size:0.82em;font-weight:700;letter-spacing:2px">🔒 판매 종료</div>'
    ) if sold_out else ""
    card_style = "opacity:0.7;" if sold_out else ""

    st.markdown(
        f'<div class="ticket-card" style="{card_style}">'
        f'{sold_banner}'
        f'{thumb_html}'
        f'<div class="ticket-body">'
        f'<div class="ticket-title">{ticket.get("공연명", "-")}</div>'
        f'<div class="ticket-sub">'
        f'🎤 {ticket.get("아티스트", "-")}<br>'
        f'📅 {공연일_표시}<br>'
        f'📍 {ticket.get("장소", "-")}'
        f'</div></div>'
        f'<div class="ticket-footer">'
        f'{badge("판매종료", "#666") if sold_out else badge(dd_str, dd_color)}'
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
        ["📊 대시보드 홈", "🛒 판매중 티켓", "📈 QOO10 실적", "🏟️ 공연장 정보", "🗓️ QOO10 K-pop 캘린더", "🎤 K-pop 아이돌 DB", "📅 팀 캘린더"],
        label_visibility="collapsed",
    )
    st.divider()
    st.caption("데이터는 로컬에 자동 저장됩니다")

# ════════════════════════════════════════════════════════════════════════════
# 1. 대시보드 홈
# ════════════════════════════════════════════════════════════════════════════
if page == "📊 대시보드 홈":
    st.title("📊 티켓 마케팅 대시보드")

    on_sale = [t for t in load("on_sale") if t.get("판매상태", "판매중") == "판매중"]

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

    on_sale_all = load("on_sale")
    active_tickets = [t for t in on_sale_all if t.get("판매상태", "판매중") == "판매중"]
    sold_tickets   = [t for t in on_sale_all if t.get("판매상태", "판매중") == "판매종료"]

    # ── 판매중 카드 그리드 ────────────────────────────────────────────────
    if not active_tickets:
        st.info("판매중인 티켓이 없습니다. 아래 폼에서 추가해 주세요.")
    else:
        cols_per_row = 3
        for row_start in range(0, len(active_tickets), cols_per_row):
            cols = st.columns(cols_per_row)
            for ci, ti in enumerate(range(row_start, min(row_start + cols_per_row, len(active_tickets)))):
                with cols[ci]:
                    _render_ticket_card(active_tickets[ti])

    # ── 판매완료 티켓 섹션 ────────────────────────────────────────────────
    if sold_tickets:
        st.divider()
        st.subheader(f"📦 판매완료 티켓 ({len(sold_tickets)}건)")
        cols_per_row = 3
        for row_start in range(0, len(sold_tickets), cols_per_row):
            cols = st.columns(cols_per_row)
            for ci, ti in enumerate(range(row_start, min(row_start + cols_per_row, len(sold_tickets)))):
                with cols[ci]:
                    _render_ticket_card(sold_tickets[ti], sold_out=True)

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

            lc, mc, rc = st.columns(3)
            ticket_link   = lc.text_input("티켓 구매 링크", placeholder="https://...")
            official_link = mc.text_input("공식 사이트 링크", placeholder="https://...")
            response_link = rc.text_input("응모/판매현황 링크", placeholder="https://docs.google.com/...")
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
                    on_sale_all.append({
                        "공연명":    title,
                        "아티스트":  artist,
                        "공연일":    store_dates(show_dates),
                        "판매마감":  str(deadline),
                        "장소":      venue,
                        "판매상태":  "판매중",
                        "구매링크":    ticket_link,
                        "공식사이트":  official_link,
                        "응모현황링크": response_link,
                        "썸네일":    fname,
                        "메모":      note,
                        "등록일":    str(date.today()),
                    })
                    save("on_sale", on_sale_all)
                    st.success("✅ 티켓이 추가되었습니다!")
                    st.rerun()

    # ── 티켓 수정 ─────────────────────────────────────────────────────────
    if on_sale_all:
        with st.expander("✏️ 티켓 수정", expanded=False):
            edit_opts = [
                f"{i}: {s.get('공연명','-')} | {s.get('아티스트','-')} | {s.get('공연일','-')}"
                for i, s in enumerate(on_sale_all)
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
            t = on_sale_all[edit_idx]

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

                f1, f2, f3 = st.columns(3)
                new_deadline = f1.date_input("판매 마감일 *", value=cur_deadline)
                new_venue    = f2.text_input("장소", value=t.get("장소", ""))
                cur_status   = t.get("판매상태", "판매중")
                new_status_edit = f3.selectbox(
                    "판매 상태",
                    ["판매중", "판매종료"],
                    index=0 if cur_status == "판매중" else 1,
                )

                el, em, er = st.columns(3)
                new_link     = el.text_input("티켓 구매 링크", value=t.get("구매링크", ""))
                new_official = em.text_input("공식 사이트 링크", value=t.get("공식사이트", ""))
                new_response = er.text_input("응모/판매현황 링크", value=t.get("응모현황링크", ""))

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

                        on_sale_all[edit_idx] = {
                            **t,
                            "공연명":    new_title,
                            "아티스트":  new_artist,
                            "공연일":    store_dates(new_dates),
                            "판매마감":  str(new_deadline),
                            "장소":      new_venue,
                            "판매상태":  new_status_edit,
                            "구매링크":    new_link,
                            "공식사이트":  new_official,
                            "응모현황링크": new_response,
                            "썸네일":    new_fname,
                            "메모":      new_note,
                        }
                        save("on_sale", on_sale_all)
                        st.success("✅ 수정이 완료되었습니다!")
                        st.rerun()

    # ── 판매 상태 변경 ────────────────────────────────────────────────────
    if on_sale_all:
        with st.expander("🔄 판매 상태 변경"):
            status_opts = [
                f"{i}: {s.get('공연명','-')} | {s.get('아티스트','-')} [{s.get('판매상태','판매중')}]"
                for i, s in enumerate(on_sale_all)
            ]
            to_change = st.multiselect("상태 변경할 티켓 선택", status_opts, key="status_change")
            new_status = st.radio("변경할 상태", ["판매종료", "판매중"], horizontal=True, key="new_status_radio")
            if st.button("상태 변경 적용", type="primary"):
                indices = {int(o.split(":")[0]) for o in to_change}
                for i in indices:
                    on_sale_all[i]["판매상태"] = new_status
                save("on_sale", on_sale_all)
                st.success(f"✅ {len(indices)}건 → [{new_status}] 처리 완료!")
                st.rerun()

    # ── 티켓 삭제 ─────────────────────────────────────────────────────────
    if on_sale_all:
        with st.expander("🗑️ 티켓 삭제"):
            opts = [
                f"{i}: {s.get('공연명','-')} | {s.get('아티스트','-')} | {s.get('공연일','-')}"
                for i, s in enumerate(on_sale_all)
            ]
            to_del = st.multiselect("삭제할 티켓 선택", opts)
            if st.button("선택 삭제", type="secondary"):
                indices = {int(o.split(":")[0]) for o in to_del}
                for i in indices:
                    fname = on_sale_all[i].get("썸네일", "")
                    if fname:
                        img_path = os.path.join(IMG_DIR, fname)
                        if os.path.exists(img_path):
                            os.remove(img_path)
                on_sale_all = [s for i, s in enumerate(on_sale_all) if i not in indices]
                save("on_sale", on_sale_all)
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

# ════════════════════════════════════════════════════════════════════════════
# 6. K-pop 아이돌 DB
# ════════════════════════════════════════════════════════════════════════════
elif page == "🎤 K-pop 아이돌 DB":
    IDOL_PATH = FILES["kpop_idols"]

    def load_idols() -> list[dict]:
        if os.path.exists(IDOL_PATH):
            with open(IDOL_PATH, encoding="utf-8") as f:
                return json.load(f)
        return []

    def save_idols(data: list[dict]):
        with open(IDOL_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

    idols = load_idols()

    st.title("🎤 K-pop 아이돌 DB")
    st.caption("일본에서 활동하거나 활동한 적이 있는 K-pop 아티스트 정보 데이터베이스")

    # ── 요약 지표 ─────────────────────────────────────────────────────────
    total      = len(idols)
    japan_act  = sum(1 for i in idols if i.get("일본활동") and i.get("활동상태") == "활동중")
    boy_cnt    = sum(1 for i in idols if i.get("구분") == "보이그룹" and i.get("활동상태") == "활동중")
    girl_cnt   = sum(1 for i in idols if i.get("구분") == "걸그룹" and i.get("활동상태") == "활동중")
    solo_cnt   = sum(1 for i in idols if i.get("구분") in ("솔로남", "솔로여") and i.get("활동상태") == "활동중")
    concert26  = sum(1 for i in idols if i.get("공연예정2026", "").strip())

    mc1, mc2, mc3, mc4, mc5 = st.columns(5)
    for col, num, lbl in [
        (mc1, total,     "전체 등록"),
        (mc2, japan_act, "일본 활동중"),
        (mc3, boy_cnt,   "보이그룹"),
        (mc4, girl_cnt,  "걸그룹"),
        (mc5, concert26, "2026 공연 예정"),
    ]:
        col.markdown(
            f'<div class="metric-box"><div class="num" style="font-size:1.8em">{num}</div>'
            f'<div class="lbl">{lbl}</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # ── 검색 & 필터 ──────────────────────────────────────────────────────
    fc1, fc2, fc3, fc4, fc5 = st.columns([3, 2, 2, 2, 2])
    search_kw  = fc1.text_input("🔍 검색", placeholder="그룹명·멤버·소속사·대표곡")
    구분_opts   = ["전체", "보이그룹", "걸그룹", "솔로남", "솔로여"]
    sel_구분    = fc2.selectbox("구분", 구분_opts)
    상태_opts   = ["전체", "활동중", "간헐적 활동", "활동 불투명", "활동종료"]
    sel_상태    = fc3.selectbox("활동상태", 상태_opts)
    japan_only  = fc4.checkbox("일본 활동만", value=False)
    concert_only = fc5.checkbox("2026 공연 예정만", value=False)

    # ── 필터 적용 ─────────────────────────────────────────────────────────
    filtered_idols = idols
    if search_kw:
        kw = search_kw.lower()
        filtered_idols = [
            i for i in filtered_idols
            if kw in i.get("그룹명", "").lower()
            or kw in i.get("일본명", "").lower()
            or kw in i.get("멤버", "").lower()
            or kw in i.get("소속사", "").lower()
            or kw in i.get("대표곡", "").lower()
            or kw in i.get("메모", "").lower()
        ]
    if sel_구분 != "전체":
        filtered_idols = [i for i in filtered_idols if i.get("구분") == sel_구분]
    if sel_상태 != "전체":
        filtered_idols = [i for i in filtered_idols if i.get("활동상태") == sel_상태]
    if japan_only:
        filtered_idols = [i for i in filtered_idols if i.get("일본활동")]
    if concert_only:
        filtered_idols = [i for i in filtered_idols if i.get("공연예정2026", "").strip()]

    st.markdown(f"**{len(filtered_idols)}개** 표시 중")
    st.divider()

    # ── 구분별 색상·이모지 ────────────────────────────────────────────────
    CATEGORY_STYLE = {
        "보이그룹": ("#6C63FF", "👦"),
        "걸그룹":   ("#FF6B9D", "👧"),
        "솔로남":   ("#00C896", "🎤"),
        "솔로여":   ("#FFB347", "🎤"),
    }
    STATUS_COLOR = {
        "활동중":       "#00c896",
        "간헐적 활동":  "#FFB347",
        "활동 불투명":  "#888",
        "활동종료":     "#FF6B6B",
    }

    # ── 카드 그리드 ──────────────────────────────────────────────────────
    COLS = 3
    for row_start in range(0, len(filtered_idols), COLS):
        row_idols = filtered_idols[row_start: row_start + COLS]
        cols = st.columns(COLS)
        for col, idol in zip(cols, row_idols):
            cat   = idol.get("구분", "")
            cat_color, cat_emoji = CATEGORY_STYLE.get(cat, ("#888", "🎵"))
            status      = idol.get("활동상태", "")
            status_color = STATUS_COLOR.get(status, "#888")
            japan_badge = (
                '<span style="background:#1890ff;color:#fff;padding:2px 8px;'
                'border-radius:10px;font-size:0.72em;font-weight:600;margin-left:4px">🇯🇵 일본</span>'
                if idol.get("일본활동") else ""
            )
            concert_badge = ""
            if idol.get("공연예정2026", "").strip():
                concert_badge = (
                    '<span style="background:#FF6B35;color:#fff;padding:2px 8px;'
                    'border-radius:10px;font-size:0.72em;font-weight:600;margin-left:4px">📅 2026공연</span>'
                )

            debut_year = str(idol.get("데뷔일", ""))[:4]
            fanclub    = idol.get("일본팬클럽", "")
            members_preview = idol.get("멤버", "")
            if len(members_preview) > 50:
                members_preview = members_preview[:47] + "…"

            col.markdown(
                f"""
<div class="ticket-card" style="border:1px solid {cat_color}33">
  <div style="background:linear-gradient(135deg,{cat_color}22,#1a1a2e);padding:14px 16px 10px">
    <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin-bottom:6px">
      <span style="background:{cat_color};color:#fff;padding:2px 10px;border-radius:12px;font-size:0.75em;font-weight:700">{cat_emoji} {cat}</span>
      <span style="background:{status_color};color:#fff;padding:2px 8px;border-radius:10px;font-size:0.72em;font-weight:600">{status}</span>
      {japan_badge}{concert_badge}
    </div>
    <div style="font-size:1.1em;font-weight:800;color:#fff;margin-bottom:2px">{idol.get('그룹명','-')}</div>
    <div style="font-size:0.82em;color:#aaa">{idol.get('일본명','')}</div>
  </div>
  <div class="ticket-body" style="padding:10px 16px">
    <div style="font-size:0.8em;color:#ccc;line-height:1.8">
      🏢 {idol.get('소속사','-')}<br>
      🗓 데뷔 {debut_year}년 · 멤버 {idol.get('멤버수','-')}인<br>
      👥 {members_preview}<br>
      {'🏟 팬클럽: ' + fanclub if fanclub else ''}
    </div>
  </div>
</div>
""",
                unsafe_allow_html=True,
            )

            # 상세 정보 확장
            with col.expander("🔍 상세 정보 보기"):
                d = idol
                st.markdown(f"**🎵 대표곡:** {d.get('대표곡','-')}")
                if d.get("공연예정2026"):
                    st.markdown(
                        f'<div style="background:#FF6B3520;border:1px solid #FF6B35;border-radius:8px;'
                        f'padding:8px 12px;margin:6px 0">'
                        f'<b>📅 2026 공연 예정</b><br>{d["공연예정2026"]}</div>',
                        unsafe_allow_html=True,
                    )
                if d.get("메모"):
                    st.caption(f"📝 {d['메모']}")
                link_html = ""
                if d.get("공식사이트"):
                    link_html += f'<a href="{d["공식사이트"]}" target="_blank" style="background:#6C63FF;color:#fff;padding:4px 10px;border-radius:8px;text-decoration:none;font-size:0.8em;margin-right:4px">🌐 공식</a>'
                if d.get("유튜브"):
                    link_html += f'<a href="{d["유튜브"]}" target="_blank" style="background:#FF0000;color:#fff;padding:4px 10px;border-radius:8px;text-decoration:none;font-size:0.8em;margin-right:4px">▶ YT</a>'
                if d.get("인스타그램"):
                    link_html += f'<a href="{d["인스타그램"]}" target="_blank" style="background:#E1306C;color:#fff;padding:4px 10px;border-radius:8px;text-decoration:none;font-size:0.8em">📸 IG</a>'
                if link_html:
                    st.markdown(link_html, unsafe_allow_html=True)

    if not filtered_idols:
        st.info("검색 조건에 맞는 아티스트가 없습니다.")

    st.divider()

    # ── 아이돌 추가 ──────────────────────────────────────────────────────
    with st.expander("➕ 아티스트 추가"):
        with st.form("add_idol", clear_on_submit=True):
            ai1, ai2 = st.columns(2)
            new_name    = ai1.text_input("그룹명 (한국어) *", placeholder="예: aespa")
            new_jpname  = ai2.text_input("일본명", placeholder="예: aespa")
            ai3, ai4 = st.columns(2)
            new_cat     = ai3.selectbox("구분", ["보이그룹", "걸그룹", "솔로남", "솔로여"])
            new_status  = ai4.selectbox("활동상태", ["활동중", "간헐적 활동", "활동 불투명", "활동종료"])
            ai5, ai6 = st.columns(2)
            new_agency  = ai5.text_input("소속사")
            new_debut   = ai6.text_input("데뷔일", placeholder="예: 2020-11-17")
            new_members = st.text_input("멤버 (쉼표 구분)", placeholder="예: 카리나, 지젤, 윈터, 닝닝")
            ai7, ai8 = st.columns(2)
            new_mcount  = ai7.number_input("멤버수", min_value=1, max_value=30, value=4)
            new_japan   = ai8.checkbox("일본 활동 있음", value=True)
            new_fanclub = st.text_input("일본 팬클럽명")
            ai9, ai10, ai11 = st.columns(3)
            new_site    = ai9.text_input("공식사이트", placeholder="https://")
            new_yt      = ai10.text_input("유튜브", placeholder="https://")
            new_ig      = ai11.text_input("인스타그램", placeholder="https://")
            new_songs   = st.text_input("대표곡 (쉼표 구분)", placeholder="예: Black Mamba, Next Level")
            new_concert = st.text_area("2026 공연 예정", height=60, placeholder="예: 2026.03 도쿄돔 공연 예정")
            new_memo    = st.text_area("메모", height=60)
            if st.form_submit_button("추가", type="primary", use_container_width=True):
                if not new_name:
                    st.error("그룹명은 필수입니다.")
                else:
                    idols.append({
                        "id":          new_name.lower().replace(" ", "_"),
                        "그룹명":       new_name,
                        "일본명":       new_jpname,
                        "구분":         new_cat,
                        "소속사":       new_agency,
                        "데뷔일":       new_debut,
                        "멤버":         new_members,
                        "멤버수":       int(new_mcount),
                        "일본활동":     new_japan,
                        "활동상태":     new_status,
                        "일본팬클럽":   new_fanclub,
                        "공식사이트":   new_site,
                        "유튜브":       new_yt,
                        "인스타그램":   new_ig,
                        "대표곡":       new_songs,
                        "공연예정2026": new_concert,
                        "메모":         new_memo,
                    })
                    save_idols(idols)
                    st.success(f"✅ '{new_name}' 추가 완료!")
                    st.rerun()

    # ── 아이돌 수정 ──────────────────────────────────────────────────────
    if idols:
        with st.expander("✏️ 아티스트 수정"):
            edit_opts = [f"{i}: {s.get('그룹명','-')} ({s.get('구분','-')})" for i, s in enumerate(idols)]
            sel_e = st.selectbox("수정할 아티스트 선택", edit_opts, key="idol_edit_sel")
            ei = int(sel_e.split(":")[0])
            t = idols[ei]
            with st.form("edit_idol"):
                ei1, ei2 = st.columns(2)
                en      = ei1.text_input("그룹명 *",  value=t.get("그룹명",""))
                ejn     = ei2.text_input("일본명",    value=t.get("일본명",""))
                ei3, ei4 = st.columns(2)
                ecat    = ei3.selectbox("구분", ["보이그룹","걸그룹","솔로남","솔로여"],
                                        index=["보이그룹","걸그룹","솔로남","솔로여"].index(t.get("구분","보이그룹")) if t.get("구분") in ["보이그룹","걸그룹","솔로남","솔로여"] else 0)
                estat   = ei4.selectbox("활동상태", ["활동중","간헐적 활동","활동 불투명","활동종료"],
                                        index=["활동중","간헐적 활동","활동 불투명","활동종료"].index(t.get("활동상태","활동중")) if t.get("활동상태") in ["활동중","간헐적 활동","활동 불투명","활동종료"] else 0)
                ei5, ei6 = st.columns(2)
                eagency = ei5.text_input("소속사",  value=t.get("소속사",""))
                edebut  = ei6.text_input("데뷔일",  value=t.get("데뷔일",""))
                emembers = st.text_input("멤버",     value=t.get("멤버",""))
                ei7, ei8 = st.columns(2)
                emcnt   = ei7.number_input("멤버수", min_value=1, max_value=30, value=int(t.get("멤버수",1)))
                ejapan  = ei8.checkbox("일본 활동",  value=bool(t.get("일본활동")))
                efanclub = st.text_input("일본 팬클럽명", value=t.get("일본팬클럽",""))
                ei9, ei10, ei11 = st.columns(3)
                esite   = ei9.text_input("공식사이트",  value=t.get("공식사이트",""))
                eyt     = ei10.text_input("유튜브",     value=t.get("유튜브",""))
                eig     = ei11.text_input("인스타그램", value=t.get("인스타그램",""))
                esongs  = st.text_input("대표곡",   value=t.get("대표곡",""))
                econcert = st.text_area("2026 공연 예정", value=t.get("공연예정2026",""), height=60)
                ememo   = st.text_area("메모",      value=t.get("메모",""), height=60)
                if st.form_submit_button("저장", type="primary", use_container_width=True):
                    idols[ei] = {
                        **t,
                        "그룹명":       en,
                        "일본명":       ejn,
                        "구분":         ecat,
                        "활동상태":     estat,
                        "소속사":       eagency,
                        "데뷔일":       edebut,
                        "멤버":         emembers,
                        "멤버수":       int(emcnt),
                        "일본활동":     ejapan,
                        "일본팬클럽":   efanclub,
                        "공식사이트":   esite,
                        "유튜브":       eyt,
                        "인스타그램":   eig,
                        "대표곡":       esongs,
                        "공연예정2026": econcert,
                        "메모":         ememo,
                    }
                    save_idols(idols)
                    st.success("✅ 수정 완료!")
                    st.rerun()

    # ── 아이돌 삭제 ──────────────────────────────────────────────────────
    if idols:
        with st.expander("🗑️ 아티스트 삭제"):
            del_opts = [f"{i}: {s.get('그룹명','-')} ({s.get('구분','-')})" for i, s in enumerate(idols)]
            to_del   = st.multiselect("삭제할 아티스트 선택", del_opts)
            if st.button("선택 삭제", type="secondary", key="del_idol"):
                indices = {int(o.split(":")[0]) for o in to_del}
                idols   = [s for i, s in enumerate(idols) if i not in indices]
                save_idols(idols)
                st.success("삭제 완료!")
                st.rerun()

    # ── CSV/Excel 다운로드 ───────────────────────────────────────────────
    if idols:
        st.divider()
        df_idol = pd.DataFrame(idols)
        csv_idol = df_idol.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
        st.download_button("📥 전체 목록 CSV 다운로드", csv_idol, "kpop_아이돌DB.csv", "text/csv")

# ════════════════════════════════════════════════════════════════════════════
# 7. 팀 캘린더
# ════════════════════════════════════════════════════════════════════════════
elif page == "📅 팀 캘린더":
    from streamlit_calendar import calendar as st_calendar

    # ── Supabase vs 로컬 JSON 자동 선택 ─────────────────────────────────
    def _use_supabase() -> bool:
        try:
            return bool(st.secrets.get("SUPABASE_URL") and st.secrets.get("SUPABASE_KEY"))
        except Exception:
            return False

    @st.cache_resource
    def _get_sb():
        from supabase import create_client
        return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

    CAL_PATH = os.path.join(DATA_DIR, "team_calendar.json")

    def load_cal() -> dict:
        if _use_supabase():
            sb = _get_sb()
            members = [r["name"] for r in sb.table("team_members").select("name").order("id").execute().data]
            events  = []
            for r in sb.table("team_events").select("*").order("start_date").execute().data:
                events.append({
                    "id":   r["id"],
                    "이름": r["name"],
                    "제목": r["title"],
                    "시작": r["start_date"],
                    "종료": r["end_date"],
                    "종류": r["kind"],
                    "메모": r.get("memo", ""),
                })
            return {"members": members, "events": events}
        if os.path.exists(CAL_PATH):
            with open(CAL_PATH, encoding="utf-8") as f:
                return json.load(f)
        return {"members": [], "events": []}

    def save_cal(data: dict):
        if not _use_supabase():
            with open(CAL_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)

    def add_member_db(name: str):
        if _use_supabase():
            _get_sb().table("team_members").insert({"name": name}).execute()
        else:
            data = load_cal()
            if name not in data["members"]:
                data["members"].append(name)
                save_cal(data)

    def remove_member_db(name: str):
        if _use_supabase():
            _get_sb().table("team_members").delete().eq("name", name).execute()
        else:
            data = load_cal()
            data["members"] = [m for m in data["members"] if m != name]
            save_cal(data)

    def add_event_db(ev: dict):
        if _use_supabase():
            _get_sb().table("team_events").insert({
                "id":         ev["id"],
                "name":       ev["이름"],
                "title":      ev["제목"],
                "start_date": ev["시작"],
                "end_date":   ev["종료"],
                "kind":       ev["종류"],
                "memo":       ev.get("메모", ""),
            }).execute()
        else:
            data = load_cal()
            data["events"].append(ev)
            save_cal(data)

    def delete_event_db(ev_id: str):
        if _use_supabase():
            _get_sb().table("team_events").delete().eq("id", ev_id).execute()
        else:
            data = load_cal()
            data["events"] = [e for e in data["events"] if e.get("id") != ev_id]
            save_cal(data)

    cal_data = load_cal()
    members  = cal_data.get("members", [])
    events   = cal_data.get("events", [])

    # ── 종류별 색상 ──────────────────────────────────────────────────────
    KIND_COLOR = {
        "공연·이벤트 참석": "#6C63FF",
        "업무 미팅·회의":   "#00C896",
        "휴가·반차":        "#FF9F43",
        "출장":             "#1890FF",
    }
    MEMBER_COLORS = [
        "#E74C3C", "#3498DB", "#2ECC71", "#F39C12",
        "#9B59B6", "#1ABC9C", "#E67E22", "#34495E",
    ]

    def member_color(name: str) -> str:
        if not members:
            return "#888"
        idx = members.index(name) if name in members else 0
        return MEMBER_COLORS[idx % len(MEMBER_COLORS)]

    st.title("📅 팀 캘린더")
    st.caption("팀원 모두가 자유롭게 일정을 등록·삭제할 수 있는 공유 캘린더")

    # ── 팀원 필터 ─────────────────────────────────────────────────────────
    col_f1, col_f2 = st.columns([4, 1])
    with col_f1:
        member_filter_opts = ["전체"] + members
        sel_member = st.radio(
            "팀원 필터",
            member_filter_opts,
            horizontal=True,
            label_visibility="collapsed",
        )
    with col_f2:
        if st.button("👥 팀원 관리", use_container_width=True):
            st.session_state["show_member_mgmt"] = not st.session_state.get("show_member_mgmt", False)

    # ── 팀원 관리 패널 ────────────────────────────────────────────────────
    if st.session_state.get("show_member_mgmt", False):
        with st.container():
            st.markdown(
                '<div style="background:#1a1a2e;border:1px solid #2a2a4a;border-radius:10px;padding:16px;margin-bottom:12px">',
                unsafe_allow_html=True,
            )
            st.markdown("**👥 팀원 목록 관리**")
            mc1, mc2 = st.columns([3, 1])
            new_member = mc1.text_input("새 팀원 이름", placeholder="예: 박마케팅", label_visibility="collapsed")
            if mc2.button("추가", use_container_width=True):
                if new_member and new_member not in members:
                    add_member_db(new_member)
                    st.success(f"'{new_member}' 추가 완료!")
                    st.rerun()
            if members:
                del_member = st.selectbox("삭제할 팀원", ["선택…"] + members, key="del_member_sel")
                if del_member != "선택…" and st.button("선택 팀원 삭제", type="secondary"):
                    remove_member_db(del_member)
                    st.warning(f"'{del_member}' 삭제 완료.")
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")

    # ── 캘린더 이벤트 빌드 ────────────────────────────────────────────────
    filtered_events = events if sel_member == "전체" else [e for e in events if e.get("이름") == sel_member]

    cal_events = []
    for ev in filtered_events:
        kind_color   = KIND_COLOR.get(ev.get("종류", ""), "#888")
        end_date_str = ev.get("종료", ev.get("시작", ""))
        # FullCalendar exclusive end: 종료일 다음날
        try:
            end_dt = pd.to_datetime(end_date_str).date() + timedelta(days=1)
            end_str = str(end_dt)
        except Exception:
            end_str = end_date_str

        title_display = f"[{ev.get('이름','')}] {ev.get('제목','')}"
        cal_events.append({
            "id":    ev.get("id", ""),
            "title": title_display,
            "start": ev.get("시작", ""),
            "end":   end_str,
            "color": kind_color,
            "extendedProps": {
                "이름": ev.get("이름", ""),
                "종류": ev.get("종류", ""),
                "메모": ev.get("메모", ""),
            },
        })

    # 판매중 티켓 공연일 자동 연동
    for tk in load("on_sale"):
        공연일 = tk.get("공연일", "")
        if not 공연일:
            continue
        try:
            공연일 = str(공연일)
            if "~" in 공연일:
                parts = 공연일.split("~")
                tk_start = parts[0].strip()
                tk_end   = str(pd.to_datetime(parts[1].strip()).date() + timedelta(days=1))
            else:
                tk_start = 공연일.strip()
                tk_end   = str(pd.to_datetime(tk_start).date() + timedelta(days=1))
            cal_events.append({
                "id":    f"ticket__{tk.get('공연명', '')}",
                "title": f"🎫 {tk.get('공연명', tk.get('아티스트', ''))}",
                "start": tk_start,
                "end":   tk_end,
                "color": "#FF6B35",
                "extendedProps": {
                    "이름": "티켓",
                    "종류": "🎫 판매중 티켓",
                    "메모": f"{tk.get('장소', '')}  |  판매마감: {tk.get('판매마감', '')}",
                },
            })
        except Exception:
            pass

    # ── 캘린더 렌더링 ─────────────────────────────────────────────────────
    cal_options = {
        "editable":    False,
        "selectable":  True,
        "locale":      "ko",
        "initialView": "dayGridMonth",
        "headerToolbar": {
            "left":   "today prev,next",
            "center": "title",
            "right":  "dayGridMonth,timeGridWeek,listMonth",
        },
        "height": 650,
        "eventDisplay": "block",
        "dayMaxEvents": 3,
    }

    cal_state = st_calendar(
        events=cal_events,
        options=cal_options,
        key="team_cal",
    )

    # ── 이벤트 클릭 → 상세·삭제 ─────────────────────────────────────────
    if cal_state.get("eventClick"):
        clicked = cal_state["eventClick"]["event"]
        ev_id   = clicked.get("id", "")
        props   = clicked.get("extendedProps", {})
        st.markdown("---")
        st.markdown(
            f'<div style="background:#1a1a2e;border:1px solid #6C63FF44;border-radius:10px;padding:16px">'
            f'<b style="font-size:1.05em">{clicked.get("title","")}</b><br>'
            f'<span style="color:#aaa;font-size:0.85em">'
            f'👤 {props.get("이름","-")} &nbsp;|&nbsp; 🏷 {props.get("종류","-")}</span><br>'
            f'{"📝 " + props["메모"] if props.get("메모") else ""}'
            f'</div>',
            unsafe_allow_html=True,
        )
        if ev_id and not ev_id.startswith("ticket__"):
            if st.button("🗑️ 이 일정 삭제", type="secondary"):
                delete_event_db(ev_id)
                st.success("삭제 완료!")
                st.rerun()

    # ── 날짜 범위 선택 → 일정 추가 ───────────────────────────────────────
    if cal_state.get("select"):
        sel_start = cal_state["select"].get("startStr", "")[:10]
        sel_end_raw = cal_state["select"].get("endStr", "")[:10]
        # FullCalendar exclusive end → 표시용 실제 종료일
        try:
            sel_end = str(pd.to_datetime(sel_end_raw).date() - timedelta(days=1))
        except Exception:
            sel_end = sel_start
        st.session_state["cal_sel_start"] = sel_start
        st.session_state["cal_sel_end"]   = sel_end

    st.markdown("---")

    # ── 일정 추가 폼 ──────────────────────────────────────────────────────
    with st.expander("➕ 일정 추가", expanded=bool(st.session_state.get("cal_sel_start"))):
        if not members:
            st.warning("먼저 '👥 팀원 관리'에서 팀원을 추가해 주세요.")
        else:
            with st.form("add_event", clear_on_submit=True):
                af1, af2 = st.columns(2)
                ev_name  = af1.selectbox("내 이름 *", members)
                ev_kind  = af2.selectbox("일정 종류 *", list(KIND_COLOR.keys()))
                ev_title = st.text_input("제목 *", placeholder="예: IVE 도쿄돔 현장 참석")

                default_start = st.session_state.get("cal_sel_start", str(date.today()))
                default_end   = st.session_state.get("cal_sel_end",   str(date.today()))
                try:
                    ds = pd.to_datetime(default_start).date()
                    de = pd.to_datetime(default_end).date()
                except Exception:
                    ds = de = date.today()

                af3, af4 = st.columns(2)
                ev_start = af3.date_input("시작일 *", value=ds)
                ev_end   = af4.date_input("종료일 *", value=de)
                ev_memo  = st.text_area("메모", height=60)

                if st.form_submit_button("등록", type="primary", use_container_width=True):
                    if not ev_title:
                        st.error("제목은 필수입니다.")
                    elif ev_end < ev_start:
                        st.error("종료일이 시작일보다 빠릅니다.")
                    else:
                        new_ev = {
                            "id":   uuid.uuid4().hex,
                            "이름": ev_name,
                            "제목": ev_title,
                            "시작": str(ev_start),
                            "종료": str(ev_end),
                            "종류": ev_kind,
                            "메모": ev_memo,
                        }
                        add_event_db(new_ev)
                        st.session_state.pop("cal_sel_start", None)
                        st.session_state.pop("cal_sel_end", None)
                        st.success(f"✅ '{ev_title}' 등록 완료!")
                        st.rerun()

    # ── 범례 ─────────────────────────────────────────────────────────────
    st.markdown("---")
    legend_items = {**KIND_COLOR, "🎫 판매중 티켓": "#FF6B35"}
    legend_html = "&nbsp;&nbsp;".join(
        f'<span style="background:{c};color:#fff;padding:3px 10px;border-radius:10px;font-size:0.8em">{k}</span>'
        for k, c in legend_items.items()
    )
    st.markdown(legend_html, unsafe_allow_html=True)
