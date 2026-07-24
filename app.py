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

# ── Supabase 헬퍼 (전역) ─────────────────────────────────────────────────────
def _use_supabase() -> bool:
    try:
        return bool(st.secrets.get("SUPABASE_URL") and st.secrets.get("SUPABASE_KEY"))
    except Exception:
        return False

@st.cache_resource
def _get_sb():
    from supabase import create_client
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

# ── 인증 ─────────────────────────────────────────────────────────────────────
def _check_auth() -> bool:
    try:
        correct_pw = st.secrets.get("APP_PASSWORD", "")
    except Exception:
        correct_pw = ""
    if not correct_pw or st.session_state.get("authenticated"):
        return True
    _, col, _ = st.columns([1, 1.5, 1])
    with col:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown(
            '<div style="text-align:center;font-size:2em;font-weight:800;color:#6C63FF">🎫 티켓 마케팅 대시보드</div>',
            unsafe_allow_html=True,
        )
        st.markdown("<br>", unsafe_allow_html=True)
        pw = st.text_input("비밀번호", type="password", placeholder="비밀번호를 입력하세요")
        if st.button("입장하기", type="primary", use_container_width=True):
            if pw == correct_pw:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("❌ 비밀번호가 올바르지 않습니다.")
    return False

# ── 헬퍼 ─────────────────────────────────────────────────────────────────────
def load(key: str) -> list[dict]:
    if key == "on_sale" and _use_supabase():
        try:
            sb   = _get_sb()
            rows = sb.table("on_sale").select("data").order("id").execute().data
            if rows:
                return [r["data"] for r in rows]
            # 테이블이 비어있으면 JSON에서 자동 시드
            json_data = _load_json(FILES[key])
            if json_data:
                sb.table("on_sale").insert([{"data": t} for t in json_data]).execute()
            return json_data
        except Exception:
            pass
    return _load_json(FILES[key])

def _load_json(path: str) -> list[dict]:
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return []

def save(key: str, data: list[dict]):
    if key == "on_sale" and _use_supabase():
        try:
            sb = _get_sb()
            sb.table("on_sale").delete().gte("id", 0).execute()
            if data:
                sb.table("on_sale").insert([{"data": t} for t in data]).execute()
            return
        except Exception:
            pass
    with open(FILES[key], "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)

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

if not _check_auth():
    st.stop()

# ── 사이드바 ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎫 마케팅 대시보드")
    st.markdown(f"**{date.today().strftime('%Y년 %m월 %d일')}** 기준")
    st.divider()
    page = st.radio(
        "페이지",
        ["📊 대시보드 홈", "🛒 판매중 티켓", "🏟️ 공연장 정보", "🗓️ QOO10 K-pop 캘린더", "🎤 K-pop 아이돌 DB", "📅 팀 캘린더", "🎨 티켓 페이지 생성기"],
        label_visibility="collapsed",
    )
    st.divider()
    st.caption("데이터는 로컬에 자동 저장됩니다")
    if st.button("🔓 로그아웃", use_container_width=True):
        st.session_state.pop("authenticated", None)
        st.rerun()

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
# 3. 공연장 정보
# ════════════════════════════════════════════════════════════════════════════
elif page == "🏟️ 공연장 정보":
    VENUES_PATH = os.path.join(DATA_DIR, "venues.json")
    if _use_supabase():
        try:
            _sb = _get_sb()
            _rows = _sb.table("venues").select("data").order("id").execute().data
            if _rows:
                venues_all = [r["data"] for r in _rows]
            else:
                venues_all = _load_json(VENUES_PATH)
                if venues_all:
                    _sb.table("venues").insert([{"data": v} for v in venues_all]).execute()
        except Exception:
            venues_all = _load_json(VENUES_PATH)
    else:
        venues_all = _load_json(VENUES_PATH)

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
        if _use_supabase():
            try:
                sb   = _get_sb()
                rows = sb.table("kpop_idols").select("data").order("kid").execute().data
                if rows:
                    return [r["data"] for r in rows]
                # 테이블이 비어있으면 JSON에서 자동 시드
                json_data = _load_json(IDOL_PATH)
                if json_data:
                    sb.table("kpop_idols").insert([
                        {"kid": i.get("id", i.get("그룹명","").lower().replace(" ","_")), "data": i}
                        for i in json_data
                    ]).execute()
                return json_data
            except Exception:
                pass
        return _load_json(IDOL_PATH)

    def save_idols(data: list[dict]):
        if _use_supabase():
            try:
                sb = _get_sb()
                sb.table("kpop_idols").delete().neq("kid", "").execute()
                if data:
                    sb.table("kpop_idols").insert([
                        {"kid": i.get("id", i.get("그룹명","").lower().replace(" ","_")), "data": i}
                        for i in data
                    ]).execute()
                return
            except Exception:
                pass
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

# ════════════════════════════════════════════════════════════════════════════
# 8. 티켓 페이지 생성기
# ════════════════════════════════════════════════════════════════════════════
elif page == "🎨 티켓 페이지 생성기":
    import io, re
    import streamlit.components.v1 as components_v1
    from openpyxl import Workbook as _Workbook

    st.title("🎨 Qoo10 チケットページ ジェネレーター")
    st.caption("엑셀 템플릿에 공연 정보를 입력하고 업로드하면 Qoo10 Japan 티켓 페이지 HTML을 자동 생성합니다.")
    st.divider()

    _TICKET_CSS = (
        'html,body,#special{-webkit-text-size-adjust:100%;text-size-adjust:100%;}\n'
        '#tc,#tc *{font-family:"Murecho",sans-serif;}\n'
        '#_special_top{font-family:"Murecho",sans-serif;font-optical-sizing:auto;font-style:normal;}\n'
        '#special{background-color:var(--page-bg);}\n'
        '.item_wrap{border-bottom:1px solid transparent;}\n'
        '.bd_glr_spc:after{background:transparent;}\n'
        '.item_wrap .prc{line-height:inherit;}\n'
        '.item_wrap .prc strong{margin:0 5px;font-size:25px;}\n'
        '.no-mark::before{content:none !important;}\n'
        '@media screen and (min-width:768px){\n'
        '  #content,#wrap{background-color:#fff;}\n'
        '  .Pstyle{display:none;position:relative;padding:60px;}\n'
        '  #FULLContents{width:100% !important;background-size:cover !important;text-align:center;position:relative;z-index:999;}\n'
        '  .fixed{position:fixed;top:0;left:0;z-index:999;width:100%;opacity:0.98;}\n'
        '}\n'
        '@media screen and (max-width:767px){#content,#wrap{background-color:var(--page-bg);}}\n'
        '.toptitle{color:#fff;text-align:center;font-family:"Montserrat",sans-serif;font-weight:900;font-size:42px;line-height:1.35;letter-spacing:0.02em;padding:40px 16px 30px;}\n'
        '@media(max-width:768px){.toptitle{font-size:26px;padding:30px 16px 20px;}}\n'
        '.title{font-family:"Montserrat",sans-serif;font-weight:900;font-style:normal;text-align:center;font-size:60px;padding-bottom:30px;}\n'
        '.titlecolor{background:linear-gradient(90deg,var(--point-color) 0%,#fff 100%);color:transparent;-webkit-background-clip:text;background-clip:text;}\n'
        '.subtitle{font-weight:700;font-size:35px;line-height:1.25;margin:0;text-align:center;color:#fff;}\n'
        '.description{font-weight:500;font-size:30px;line-height:1.4;margin:0;text-align:center;color:#fff;}\n'
        '#tc dl,#tc dt,#tc dd{margin:0;}\n'
        '.info-block{padding:40px 16px 60px;text-align:center;}\n'
        '.info-row{padding:18px 0;}\n'
        '.info-row+.info-row{padding-top:26px;}\n'
        '.info-list{margin:0;}\n'
        '.info-label{display:block;color:var(--point-color);}\n'
        '.info-label--mt{padding-top:40px;}\n'
        '.info-body{margin:0;}\n'
        '.info-date{position:relative;display:inline-block;padding-bottom:14px;}\n'
        '.info-date::after{content:"";position:absolute;left:0;bottom:0;width:100%;height:1px;background:#ccc;}\n'
        '.info-time{margin-top:12px;}\n'
        '.info-venue{margin-top:12px;font-weight:700;}\n'
        '@media(max-width:768px){.title{font-size:45px;}.info-time,.info-location{font-size:20px;}.info-block .subtitle.label{font-size:34px;}.info-block .subtitle.date,.info-block .description.time{font-size:38px;}}\n'
        '@media(max-width:420px){.info-block .subtitle.label{font-size:30px !important;}.info-block .subtitle{font-size:30px !important;}.info-block .description{font-size:20px !important;font-weight:500;}}\n'
        '.section-wrap,.section-wrap *{box-sizing:border-box;}\n'
        '.section-wrap{overflow-x:hidden;padding:48px 16px;}\n'
        '.ticket-box,.tabwrapper{max-width:750px;width:100%;margin:0 auto;background:#fff;border-radius:28px;}\n'
        '.ticket-box{padding:40px 30px;text-align:center;}\n'
        '.tabwrapper{padding:40px 50px;}\n'
        '.tabwrap-outer{padding:0;}\n'
        '@media(max-width:768px){.ticket-box,.tabwrapper{border-radius:22px;padding:40px 20px;}}\n'
        '@media(max-width:480px){.ticket-box,.tabwrapper{border-radius:18px;padding:40px 20px;}}\n'
        '.ticket-info{text-align:center;margin-bottom:36px;padding-bottom:30px;font-size:15px;}\n'
        '.ticket-title{font-size:40px;font-weight:900;margin-bottom:18px;letter-spacing:.02em;}\n'
        '.ticket-note{font-size:16px;color:#555;margin-bottom:24px;}\n'
        '.ticket-info p:not(.ticket-title):not(.ticket-note){font-size:18px;color:#666;line-height:1.6;font-weight:600;}\n'
        '@media(max-width:768px){.ticket-title{font-size:30px;}.ticket-info{padding-bottom:12px;margin-bottom:20px;}}\n'
        '.ticketList{list-style:none;margin:0 auto;padding:0;display:flex;flex-direction:column;gap:14px;max-width:540px;}\n'
        '@media(max-width:768px){.ticketList{gap:10px;}}\n'
        '.ticket-type-label{list-style:none;display:flex;align-items:center;gap:12px;padding:18px 0 8px;font-size:12px;font-weight:800;color:var(--point-color);letter-spacing:.16em;}\n'
        '.ticket-type-label::after{content:"";flex:1;height:1px;background:linear-gradient(90deg,var(--point-color) 0%,transparent 100%);opacity:0.35;}\n'
        '.ticket-type-label:first-child{padding-top:0;}\n'
        '.ticketBtn{position:relative;display:grid;grid-template-columns:1fr auto 18px;grid-template-rows:auto auto auto;column-gap:16px;row-gap:0;align-items:center;padding:18px 42px;border-radius:999px;background:linear-gradient(135deg,rgba(255,255,255,0.15) 0%,rgba(0,0,0,0.18) 100%) var(--btn-color);color:#fff;text-decoration:none;font-weight:700;line-height:1.2;overflow:hidden;-webkit-tap-highlight-color:rgba(0,0,0,0);-webkit-appearance:none;appearance:none;outline:none !important;user-select:none;-webkit-user-select:none;}\n'
        '.ticketType{grid-column:1/span 2;grid-row:1;text-align:left;font-size:10px;font-weight:800;letter-spacing:.18em;opacity:0.72;padding-bottom:7px;border-bottom:1px solid rgba(255,255,255,0.22);}\n'
        '.ticketDay{grid-column:1;grid-row:2;text-align:left;letter-spacing:.5px;font-size:18px;font-weight:800;padding-top:8px;}\n'
        '.ticketDate{grid-column:1;grid-row:3;text-align:left;font-size:14px;font-weight:600;opacity:.95;}\n'
        '.ticketPrice{grid-column:2;grid-row:2/span 2;justify-self:end;align-self:center;font-size:22px;white-space:nowrap;}\n'
        '.ticketBtn::after{content:"";grid-column:3;grid-row:2/span 2;justify-self:end;align-self:center;width:10px;height:10px;border-top:2px solid #fff;border-right:2px solid #fff;transform:rotate(45deg);transition:transform .18s ease;z-index:1;}\n'
        '.ticketBtn:hover::after{transform:translateX(6px) rotate(45deg);}\n'
        '@media(max-width:768px){.ticketBtn{grid-template-columns:1fr 18px;grid-template-rows:auto auto auto auto;padding:16px 22px;border-radius:20px;}.ticketType{grid-column:1/span 2;grid-row:1;padding-bottom:6px;font-size:10px;}.ticketDay{grid-column:1;grid-row:2;font-size:16px;white-space:normal;word-break:keep-all;padding-top:6px;}.ticketDate{grid-column:1;grid-row:3;font-size:13px;white-space:normal;}.ticketPrice{grid-column:1;grid-row:4;justify-self:start;font-size:25px;margin-top:10px;}.ticketBtn::after{grid-column:2;grid-row:2/span 3;align-self:center;justify-self:end;}}\n'
        '.ticketBtn.is-disabled{pointer-events:none;cursor:default;filter:saturate(.6) brightness(.95);}\n'
        '.ticketBtn.is-disabled .ticketDay,.ticketBtn.is-disabled .ticketDate,.ticketBtn.is-disabled .ticketPrice{opacity:.35;}\n'
        '.ticketBtn.is-disabled::before{content:"";position:absolute;inset:0;z-index:3;display:grid;place-items:center;background:rgba(0,0,0,.55);color:#fff;font-weight:900;letter-spacing:.14em;font-size:18px;text-shadow:0 2px 8px rgba(0,0,0,.6);}\n'
        '.ticketBtn.st-uketsuke-yotei::before{content:"受付予定";}\n'
        '.ticketBtn.st-hanbai-shuryo::before{content:"販売終了";}\n'
        '.ticketBtn.st-soldout::before{content:"SOLD OUT";}\n'
        '.ticketBtn.is-disabled:hover::after{transform:rotate(45deg);}\n'
        '.ticket-notice{list-style:none;padding:0;margin:24px auto;max-width:540px;font-size:14px;text-align:left;font-weight:500;}\n'
        '.ticket-notice li{position:relative;padding-left:1.2em;line-height:1.6;margin-bottom:6px;}\n'
        '.ticket-notice li::before{content:"※";position:absolute;left:0;top:0;}\n'
        '@media(max-width:480px){.ticket-title{font-size:35px;}.ticket-notice{max-width:100%;}}\n'
        '.lineup-section{text-align:center;padding:0 16px 20px;}\n'
        '.lineup-section img{max-width:100%;height:auto;}\n'
        '.tabwrapper,.tabwrapper *{box-sizing:border-box;}\n'
        '.infotabs{position:relative;}\n'
        '.infotab__input{position:absolute;opacity:0;pointer-events:none;}\n'
        '.infotab__nav{display:flex;flex-wrap:wrap;gap:10px;justify-content:flex-start;margin-bottom:28px;}\n'
        '.infotab__label{display:inline-flex;align-items:center;justify-content:center;padding:12px 22px;border-radius:999px;border:2px solid var(--point-color);color:var(--point-color);font-size:20px;font-weight:700;white-space:nowrap;cursor:pointer;line-height:1;-webkit-tap-highlight-color:transparent;touch-action:manipulation;}\n'
        '#tab1:checked ~ .infotab__nav label[for="tab1"],\n'
        '#tab2:checked ~ .infotab__nav label[for="tab2"],\n'
        '#tab3:checked ~ .infotab__nav label[for="tab3"],\n'
        '#tab4:checked ~ .infotab__nav label[for="tab4"],\n'
        '#tab5:checked ~ .infotab__nav label[for="tab5"],\n'
        '#tab6:checked ~ .infotab__nav label[for="tab6"]{background:var(--point-color);color:#121113;}\n'
        '.infotab__content{display:none;font-size:15px;line-height:1.7;}\n'
        '#tab1:checked ~ .infotab__panels .panel1{display:block;}\n'
        '#tab2:checked ~ .infotab__panels .panel2{display:block;}\n'
        '#tab3:checked ~ .infotab__panels .panel3{display:block;}\n'
        '#tab4:checked ~ .infotab__panels .panel4{display:block;}\n'
        '#tab5:checked ~ .infotab__panels .panel5{display:block;}\n'
        '#tab6:checked ~ .infotab__panels .panel6{display:block;}\n'
        '.oshirase{font-size:14px;text-align:left;word-break:break-word;padding-top:30px;font-weight:450;}\n'
        '.oshirase dl{margin:0;}\n'
        '.oshirase dd{margin:0;padding:8px 0;}\n'
        '.oshirase dt{position:relative;padding-top:30px;padding-left:18px;font-weight:700;}\n'
        '.oshirase dt::before{content:"■";position:absolute;left:0;top:30px;color:var(--point-color);}\n'
        '.oshirase .list{text-indent:-14px;padding-left:14px;}\n'
        '.oshirase .list::before{content:"●";font-size:5px;margin-right:7px;color:var(--point-color);vertical-align:middle;}\n'
        '.oshirase .list_star{text-indent:-14px;padding-left:14px;}\n'
        '.oshirase .list_star::before{content:"＊";font-size:13px;margin-right:7px;color:var(--point-color);vertical-align:middle;}\n'
        '.oshirase .list_important{text-indent:-14px;padding-left:14px;}\n'
        '.oshirase .list_important::before{content:"※";font-size:14px;margin-right:7px;color:var(--point-color);vertical-align:middle;}\n'
        '@media(max-width:768px){.tabwrapper{padding:32px 18px;}.infotab__label{font-size:14px;padding:10px 16px;}.infotab__content{font-size:14px;}}\n'
        '@media(max-width:480px){.tabwrapper{padding:40px 25px;}.infotab__nav{gap:8px;}.infotab__label{font-size:13px;padding:10px 14px;}.infotab__content{font-size:13px;line-height:1.75;}.oshirase{padding-top:10px;}.oshirase .list,.oshirase .list_star,.oshirase .list_important{text-indent:-12px;padding-left:12px;}}\n'
    )

    def _make_template():
        wb = _Workbook()
        ws = wb.active
        ws.title = "入力フォーム"
        rows = [
            ['항목', '내용', '설명 (수정 불필요 / 참고용)'],
            ['', '', ''],
            ['【① 基本情報 & デザイン】', '', ''],
            ['タイトル', '2026 ○○ WORLD TOUR [○○] IN TOKYO', '改行したい場合は \\n を入力'],
            ['ポスターURL', '', '画像URLがあれば入力（なければ空白）'],
            ['ポスター幅',  '100%', '例: 100% / 60% / 400px　デフォルト100%'],
            ['会場', '○○アリーナ', ''],
            ['背景色', '#191919', '例: #191919（黒） / #0a0a1e / #1a0a00'],
            ['チケットボタン色', '#8da0a7', '例: #8da0a7（デフォルト） / #c2185b / #2e5fa3'],
            ['ポイントカラー',   '',        '例: #FF6B6B / #6C63FF　空白でチケットボタン色と同じ'],
            ['', '', ''],
            ['【② 公演概要 — SCHEDULE セクション】', '', '最大5日'],
            ['公演日1_日付', '2026年○月○日(○)', ''],
            ['公演日1_時間', '○○:○○開場・○○:○○開演', ''],
            ['公演日2_日付', '', '2日目がなければ空白'],
            ['公演日2_時間', '', ''],
            ['公演日3_日付', '', ''],
            ['公演日3_時間', '', ''],
            ['公演日4_日付', '', ''],
            ['公演日4_時間', '', ''],
            ['公演日5_日付', '', ''],
            ['公演日5_時間', '', ''],
            ['', '', ''],
            ['【③ チケット一覧 — TICKETS セクション】', '', '最大10件'],
            ['チケットセクション見出し', 'チケット', 'チケットボックスのH2見出し'],
            ['販売期間', '2026年○月○日(○) ○○:00 ～ 各公演の2日前 23:59まで', ''],
            ['販売期間注記', '※予定枚数に達し次第受付終了', '赤字。なければ空白'],
            ['当落発表日', '', '抽選の場合のみ記入。なければ空白'],
            ['入金期限',  '', '抽選の場合のみ記入。なければ空白'],
            ['', '', ''],
        ]
        defaults = [
            ('VIP席', '¥20,000', '販売中'),
            ('S席',   '¥15,000', '販売中'),
        ]
        for n in range(1, 11):
            d = defaults[n - 1] if n <= len(defaults) else ('', '', '')
            rows += [
                [f'── チケット{n} ──', '', ''],
                [f'チケット{n}_公演日付', '2026年○月○日(○)' if n <= 2 else '', ''],
                [f'チケット{n}_公演時間', '○○:○○開場・○○:○○開演' if n <= 2 else '', ''],
                [f'チケット{n}_権種名',   d[0], '例: VIP席 / S席 / 一般指定席'],
                [f'チケット{n}_価格',     d[1], ''],
                [f'チケット{n}_URL',      'https://www.qoo10.jp/...' if n <= 2 else '', '購入URL'],
                [f'チケット{n}_状態',     d[2], '受付中 / 受付予定 / 販売中 / 販売終了 / SOLDOUT'],
                [f'チケット{n}_色',       '',   '例: #FF6B6B / #6C63FF / #00C896　空白でデフォルト色'],
                ['', '', ''],
            ]
        rows += [
            ['【④ チケット注意事項】', '', '※が付く注意事項'],
            ['チケット注意1', 'お一人様４枚まで', ''],
            ['チケット注意2', '未就学児入場不可', ''],
            ['チケット注意3', '録音・録画機材（携帯電話）使用禁止', ''],
            ['チケット注意4', '', ''],
            ['チケット注意5', '', ''],
            ['', '', ''],
            ['【⑤ ラインアップ（チケットとNOTICEの間）】', '', ''],
            ['ラインアップ見出し', 'LINEUP', '空白の場合は見出しなし'],
            ['ラインアップ画像URL', '', '画像URLがあれば入力（なければセクション非表示）'],
            ['', '', ''],
            ['【⑥ NOTICE タブ（最大6個）】', '', 'タブ名が空白のタブは非表示'],
            ['', '', ''],
        ]
        tab_defs = [
            ('前売りのご案内', '●', [
                '本チケットは1名様4枚までご購入いただけます。',
                'チケット1枚につき1名様のみご入場可能となります。',
                'チケットは数量限定で販売され、売り切れ次第終了する場合がございます。',
                'チケットは券面に記載の公演日・会場でのみ有効となります。',
                'チケットの譲渡・転売が発覚した場合は、チケットの没収の上退場していただきます。',
            ]),
            ('チケットのお申し込みに際して', '●', [
                'チケットのお申し込みをする前に、下記リンクより本公演に関する注意事項を必ずご確認ください。',
            ]),
            ('公演当日の注意事項', '＊', [
                'スタッフの指示に従っていただきますよう、ご理解とご協力をお願いいたします。',
            ]),
            ('', '●', []),
            ('', '●', []),
            ('', '●', []),
        ]
        for ti, (name, style, contents) in enumerate(tab_defs, 1):
            rows.append([f'── タブ{ti} ──', '', ''])
            rows.append([f'タブ{ti}_名称',   name,  'タブボタンに表示される名前'])
            rows.append([f'タブ{ti}_スタイル', style, '箇条書きの種類: ●（丸）/ ＊（星）/ ※（重要）/ なし'])
            for ci in range(1, 16):
                rows.append([f'タブ{ti}_内容{ci}', contents[ci - 1] if ci <= len(contents) else '', ''])
            rows.append(['', '', ''])
        rows += [
            ['【⑦ お問い合わせ（タブ1末尾に自動挿入）】', '', ''],
            ['問合せ_チケットURL',    'https://www.qoo10.jp/gmkt.inc/CS/NHelpContactUs.aspx', ''],
            ['問合せ_電子チケットURL', 'https://www.qoo10.jp/gmkt.inc/Special/Special.aspx?sid=354258', 'なければ空白'],
            ['問合せ_公演会社名',     '（株）○○', ''],
            ['問合せ_公演電話',       '○○-○○○○-○○○○（平日11:00～15:00）', ''],
            ['問合せ_公演タイトル',   '', '空白の場合はタイトル欄を使用'],
        ]
        for r in rows:
            ws.append(r)
        ws.column_dimensions['A'].width = 26
        ws.column_dimensions['B'].width = 68
        ws.column_dimensions['C'].width = 42
        buf = io.BytesIO()
        wb.save(buf)
        return buf.getvalue()

    # ── 언어별 고정 라벨 ──────────────────────────────────────────────
    _LANG_LABELS = {
        'ja': {
            'perf_datetime':    '公演日時',
            'venue':            '会場',
            'sold_out':         '受付終了',
            'lottery_date':     '当落発表日',
            'payment_deadline': '入金期限',
            'l_eticket':        '「電子チケットについて」',
            'l_purchase':       '「チケットのご購入に関するお問い合わせ」',
            'l_form':           'お問い合わせフォーム',
            'l_category':       'カテゴリは「イベント／クーポン ＞ 公演・チケット」をご選択ください。',
            'l_id_note':        'お問い合わせの際にはタイトルに【{title}】、本文にお客様のID/注文番号（チケット購入済みの場合のみ）をご記載ください。',
            'l_event':          '「公演に関するお問い合わせ」',
        },
        'en': {
            'perf_datetime':    'Date & Time',
            'venue':            'Venue',
            'sold_out':         'Sold Out',
            'lottery_date':     'Lottery Result Date',
            'payment_deadline': 'Payment Deadline',
            'l_eticket':        '"Electronic Ticket Inquiries"',
            'l_purchase':       '"Ticket Purchase Inquiries"',
            'l_form':           'Contact Form',
            'l_category':       'Please select "Events/Coupons > Concerts & Tickets" as the category.',
            'l_id_note':        'When contacting us, please include [{title}] in the subject and your customer ID / order number (only if already purchased) in the body.',
            'l_event':          '"Performance Inquiries"',
        },
        'ko': {
            'perf_datetime':    '공연일시',
            'venue':            '공연장',
            'sold_out':         '판매종료',
            'lottery_date':     '당락발표일',
            'payment_deadline': '입금기한',
            'l_eticket':        '「전자티켓 관련 문의」',
            'l_purchase':       '「티켓 구매 관련 문의」',
            'l_form':           '문의 양식',
            'l_category':       '카테고리는 「이벤트/쿠폰 ＞ 공연・티켓」을 선택해 주세요.',
            'l_id_note':        '문의 시 제목에 【{title}】, 본문에 고객 ID/주문번호（티켓 구매 완료 시에만）를 기재해 주세요.',
            'l_event':          '「공연 관련 문의」',
        },
    }

    # ── 번역 함수 ─────────────────────────────────────────────────────
    def _translate_data(data, target_lang):
        if target_lang == 'ja':
            return dict(data)
        try:
            from deep_translator import GoogleTranslator
        except ImportError:
            st.warning("deep-translator 패키지가 없습니다. requirements.txt를 확인하세요.")
            return dict(data)

        lang_code = {'en': 'en', 'ko': 'ko'}[target_lang]

        def should_skip(key, val):
            if not val or not val.strip(): return True
            if 'URL' in key or '色' in key: return True
            if key.endswith('_状態'): return True
            if val.startswith('#') or val.startswith('http'): return True
            return False

        to_translate = {k: v for k, v in data.items() if not should_skip(k, v)}
        if not to_translate:
            return dict(data)

        result = dict(data)
        translator = GoogleTranslator(source='auto', target=lang_code)
        keys = list(to_translate.keys())
        vals = list(to_translate.values())
        try:
            translated = translator.translate_batch(vals)
            for k, v in zip(keys, translated):
                if v:
                    result[k] = v
        except Exception:
            for k, v in zip(keys, vals):
                try:
                    t = translator.translate(v)
                    if t: result[k] = t
                except Exception:
                    pass
        return result

    # ── HTML 생성 함수 ────────────────────────────────────────────────
    def _generate_html(data, orig_data, ticket_css, lang='ja'):
        lbl = _LANG_LABELS[lang]
        def g(k): return str(data.get(k, '') or '').strip()
        def og(k): return str(orig_data.get(k, '') or '').strip()
        def esc(s): return str(s).replace('&', '&amp;').replace('"', '&quot;')
        def linkify(text):
            return re.sub(r'(https?://[^\s<>"]+)',
                          lambda m: f'<a href="{esc(m.group(1))}" target="_blank">{m.group(1)}</a>',
                          str(text))
        def bullet_cls(style):
            s = str(style or '').strip()
            if s in ('＊', '*'): return 'list_star'
            if s == '※':         return 'list_important'
            if s == 'なし':       return 'list_none'
            return 'list'
        def collect(prefix, max_n):
            return [g(f'{prefix}{i}') for i in range(1, max_n + 1) if g(f'{prefix}{i}')]

        title     = g('タイトル').replace('\\n', '<br>')
        poster    = g('ポスターURL')
        venue     = g('会場')
        page_bg     = og('背景色') or '#191919'
        btn_color   = og('チケットボタン色') or '#8da0a7'
        point_color = og('ポイントカラー') or btn_color

        # 色未指定 + ポスターあり → 自動抽出
        _auto_palette = []
        if poster and (not og('チケットボタン色') or not og('ポイントカラー')):
            _auto_palette = _extract_poster_palette(poster)
        if _auto_palette:
            if not og('チケットボタン色'):
                btn_color = _auto_palette[0]
            if not og('ポイントカラー'):
                point_color = _auto_palette[0]

        perf_days = []
        for i in range(1, 6):
            d = g(f'公演日{i}_日付')
            if not d: break
            perf_days.append({'date': d, 'time': g(f'公演日{i}_時間')})

        section_title    = g('チケットセクション見出し') or 'チケット'
        sale_period      = g('販売期間')
        sale_note        = g('販売期間注記')
        lottery_date     = g('当落発表日')
        payment_deadline = g('入金期限')
        tickets = []
        for i in range(1, 11):
            d  = g(f'チケット{i}_公演日付')
            tp = g(f'チケット{i}_権種名')
            pr = g(f'チケット{i}_価格')
            if not d and not tp and not pr: break
            if not d and not tp: continue
            tickets.append({
                'date': d, 'time': g(f'チケット{i}_公演時間'),
                'type': tp, 'price': pr,
                'url': og(f'チケット{i}_URL') or '#',
                'status': og(f'チケット{i}_状態'),
                'color': og(f'チケット{i}_色'),
            })

        ticket_notices = collect('チケット注意', 5)
        lineup_heading = g('ラインアップ見出し')
        lineup_url     = og('ラインアップ画像URL')

        tabs = []
        for t in range(1, 7):
            name = g(f'タブ{t}_名称')
            if not name: break
            tabs.append({'name': name, 'cls': bullet_cls(g(f'タブ{t}_スタイル')), 'items': collect(f'タブ{t}_内容', 15)})

        c_ticket  = og('問合せ_チケットURL')
        c_eticket = og('問合せ_電子チケットURL')
        c_name    = g('問合せ_公演会社名')
        c_phone   = g('問合せ_公演電話')
        c_title   = g('問合せ_公演タイトル') or g('タイトル').replace('\\n', ' ')

        errors = []
        if not title:   errors.append('タイトルが入力されていません。')
        if not tickets: errors.append('チケット情報が入力されていません。')
        if not tabs:    errors.append('タブ1_名称 が入力されていません。')
        if errors:      return None, errors

        # SCHEDULE
        if perf_days:
            sched_html = ''.join(
                f'\n      <div class="info-row">'
                f'<div class="subtitle info-date">{d["date"]}</div>'
                f'<div class="description info-time">{d["time"]}</div>'
                f'</div>'
                for d in perf_days)
        else:
            sched_html = '<div class="info-row"><div class="description">—</div></div>'

        # Ticket buttons (soldout uses original status; CSS text uses lang label)
        types_distinct = list(dict.fromkeys(t['type'] for t in tickets if t['type']))
        has_multi = len(types_distinct) > 1

        # 権種名ごとに自動カラー（ボタン色未指定 + ポスター自動抽出 + 2種以上）
        type_color_map = {}
        if not og('チケットボタン色') and _auto_palette and len(types_distinct) > 1:
            type_color_map = dict(zip(types_distinct, _make_ticket_palette(point_color, len(types_distinct))))

        btns = ''
        for t in tickets:
            _DISABLED = {'受付予定': 'st-uketsuke-yotei', '販売終了': 'st-hanbai-shuryo', 'SOLDOUT': 'st-soldout'}
            status_cls = _DISABLED.get(t['status'], '')
            cls = f'is-disabled {status_cls}'.strip() if status_cls else ''
            btn_c = t.get('color') or type_color_map.get(t['type'], '')
            color_style = (
                f'style="background:linear-gradient(135deg,rgba(255,255,255,0.15) 0%,rgba(0,0,0,0.18) 100%) {esc(btn_c)}"'
                if btn_c else ''
            )
            btns += (
                f'\n      <li class="ticketItem">'
                f'<a class="ticketBtn {cls}" {color_style} href="{esc(t["url"])}">'
                f'<span class="ticketType">{t["type"]}</span>'
                f'<span class="ticketDay">{t["date"]}</span>'
                f'<span class="ticketDate">{t["time"]}</span>'
                f'<span class="ticketPrice">{t["price"]}</span>'
                f'</a></li>'
            )

        notice_html = ''
        if ticket_notices:
            items_li = '\n'.join(f'      <li>{n}</li>' for n in ticket_notices)
            notice_html = f'    <ul class="ticket-notice">\n{items_li}\n    </ul>'

        # Lineup
        lineup_sec = ''
        if lineup_url:
            h = f'  <div class="title"><span class="titlecolor">{lineup_heading}</span></div>\n' if lineup_heading else ''
            lineup_sec = (
                f'\n<!-- lineup -->\n<div class="section-wrap" style="padding-bottom:0;">\n'
                f'{h}  <div class="lineup-section">'
                f'<img src="{esc(lineup_url)}" style="max-width:100%;height:auto;"></div>\n</div>\n'
            )

        # Contact block (language-aware fixed strings)
        contact = ''
        if c_eticket:
            contact += (
                f'\n                <dd class="list_none"><span style="background-color:#fff59d;">{lbl["l_eticket"]}</span></dd>'
                f'\n                <dd class="list_none">▶<a href="{esc(c_eticket)}" target="_blank">{c_eticket}</a></dd>'
            )
        if c_ticket:
            id_note = lbl['l_id_note'].replace('{title}', c_title)
            contact += (
                f'\n                <dd class="list_none"><span style="background-color:#fff59d;">{lbl["l_purchase"]}</span></dd>'
                f'\n                <dd class="list_none">{lbl["l_form"]}<br><a href="{esc(c_ticket)}" target="_blank">▶{c_ticket}</a></dd>'
                f'\n                <dd class="list_none">{lbl["l_category"]}</dd>'
                f'\n                <dd class="list_none">{id_note}</dd>'
            )
        if c_name or c_phone:
            ph = f'<br>▶{c_phone}' if c_phone else ''
            contact += (
                f'\n                <dd class="list_none"><span style="background-color:#fff59d;">{lbl["l_event"]}</span></dd>'
                f'\n                <dd class="list_none">▶{c_name}{ph}</dd>'
            )

        # Tab HTML
        tab_inputs = '\n        '.join(
            f'<input type="radio" id="tab{i+1}" name="tab" class="infotab__input"{" checked" if i == 0 else ""}>'
            for i in range(len(tabs)))
        tab_nav = '\n          '.join(
            f'<label for="tab{i+1}" class="infotab__label">{tab["name"]}</label>'
            for i, tab in enumerate(tabs))
        tab_panels = ''
        for i, tab in enumerate(tabs):
            body = '\n'.join(f'                <dd class="{tab["cls"]}">{linkify(item)}</dd>' for item in tab['items'])
            extra = contact if i == 0 else ''
            tab_panels += (
                f'\n          <div class="infotab__content panel{i+1}">'
                f'\n            <div class="oshirase"><dl>\n{body}{extra}\n              </dl></div>'
                f'\n          </div>'
            )

        # Optional fragments
        poster_width = og('ポスター幅') or '100%'
        poster_sec = (
            f'<div style="text-align:center;">'
            f'<img src="{esc(poster)}" style="width:{esc(poster_width)};max-width:100%;height:auto;display:block;margin:0 auto;">'
            f'</div>\n\n'
        ) if poster else ''
        sp_html       = f'      <p class="ticket-note" style="color:BLACK;">販売期間<BR>{sale_period}</p>\n' if sale_period else ''
        spn_html      = f'      <p class="ticket-note" style="color:red;">{sale_note}</p>\n' if sale_note else ''
        lottery_html  = (f'      <p class="ticket-note" style="color:BLACK;">{lbl["lottery_date"]}<BR>{lottery_date}</p>\n'
                         if lottery_date else '')
        deadline_html = (f'      <p class="ticket-note" style="color:BLACK;">{lbl["payment_deadline"]}<BR>{payment_deadline}</p>\n'
                         if payment_deadline else '')

        # CSS: swap soldout overlay text for current language
        css_for_lang = ticket_css

        style_block = (
            '<style>\n:root {\n'
            '  --btn-color:   ' + btn_color + ';\n'
            '  --point-color: ' + point_color + ';\n'
            '  --page-bg:     ' + page_bg + ';\n'
            '}\n'
            + css_for_lang + '\n</style>'
        )

        title_plain = title.replace('<br>', ' ')
        _body_content = (
            '<!-- title -->\n'
            f'<div class="toptitle">{title}</div>\n\n'
            + poster_sec
            + '<!-- schedule -->\n'
            '<section class="info-block">\n'
            '  <div class="title"><span class="titlecolor">SCHEDULE</span></div>\n'
            '  <dl class="info-list">\n'
            f'    <dt class="subtitle info-label">{lbl["perf_datetime"]}</dt>\n'
            f'    <dd class="info-body">{sched_html}\n    </dd>\n'
            f'    <dt class="subtitle info-label info-label--mt">{lbl["venue"]}</dt>\n'
            f'    <dd class="description info-venue">{venue}</dd>\n'
            '  </dl>\n'
            '</section>\n\n'
            '<!-- ticket -->\n'
            '<div class="section-wrap">\n'
            '  <div class="title"><span class="titlecolor">TICKETS</span></div>\n'
            '  <div class="ticket-box">\n'
            '    <div class="ticket-info">\n'
            + sp_html
            + lottery_html
            + deadline_html
            + f'      <h2 class="ticket-title">{section_title}</h2>\n'
            + spn_html
            + '    </div>\n'
            '    <ul class="ticketList" aria-label="Ticket options">\n'
            + btns + '\n'
            '    </ul>\n'
            + notice_html + '\n'
            '  </div>\n'
            '</div>\n'
            + lineup_sec
            + '<!-- notice -->\n'
            '<div class="section-wrap">\n'
            '  <div class="title"><span class="titlecolor">NOTICE</span></div>\n'
            '  <div class="tabwrap-outer"><div class="tabwrapper"><div class="infotabs">\n'
            '        ' + tab_inputs + '\n'
            '        <div class="infotab__nav">\n'
            '          ' + tab_nav + '\n'
            '        </div>\n'
            '        <div class="infotab__panels">\n'
            + tab_panels + '\n'
            '        </div>\n'
            '  </div></div></div>\n'
            '</div>\n'
        )
        html_out = (
            '<!DOCTYPE html>\n'
            '<html lang="' + lang + '">\n'
            '<head>\n'
            '<meta charset="UTF-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
            '<title>' + title_plain + '</title>\n'
            '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
            '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
            '<link href="https://fonts.googleapis.com/css2?family=Murecho:wght@100..900&display=swap" rel="stylesheet">\n'
            '<link href="https://fonts.googleapis.com/css2?family=Montserrat:ital,wght@0,100..900;1,100..900&display=swap" rel="stylesheet">\n'
            '<link rel="stylesheet" href="https://dp.image-qoo10.jp/dp2016/JP/design/JPPM/fullEvent.css">\n'
            + style_block + '\n'
            '</head>\n'
            '<body style="margin:0;padding:0;background:' + page_bg + ';">\n'
            '<div id="tc">\n'
            + _body_content
            + '</div>\n'
            + '</body>\n</html>\n'
        )
        return html_out, []

    # ── 검증 헬퍼 ─────────────────────────────────────────────────────
    def _collect_notices(data):
        items = []
        for i in range(1, 6):
            v = str(data.get(f'チケット注意{i}', '') or '').strip()
            if v:
                items.append(('チケット注意事項', v))
        for t in range(1, 7):
            tab_name = str(data.get(f'タブ{t}_名称', '') or '').strip()
            if not tab_name: break
            for c in range(1, 16):
                v = str(data.get(f'タブ{t}_内容{c}', '') or '').strip()
                if v:
                    items.append((f'タブ{t}「{tab_name}」', v))
        return items

    def _validate_ai(items, api_key):
        import anthropic as _ant
        client = _ant.Anthropic(api_key=api_key)
        lines = '\n'.join(f'[{src}] {txt}' for src, txt in items)
        prompt = (
            "당신은 이벤트 티켓 규약 전문 심사원입니다.\n"
            "아래의 티켓 주의사항 및 NOTICE 문구들을 분석하여 문제를 한국어로 보고해주세요.\n\n"
            "【검사 항목】\n"
            "1. 중복/유사 문구: 동일하거나 매우 유사한 내용이 반복되는 항목\n"
            "2. 상충 문구: 논리적으로 모순되는 내용 (연령 제한 불일치 등)\n"
            "3. 모호한 표현: 해석에 따라 의미가 달라질 수 있어 분쟁 소지가 있는 표현\n\n"
            "【판정 제외 — 이것은 문제가 아닙니다】\n"
            "- 「お一人様○枚まで」「1名様○枚まで購入」 등 구매 매수 제한(1인이 살 수 있는 장 수)과\n"
            "  「チケット1枚につき1名様のみ入場」 등 입장 조건(1장당 입장 가능 인원)은\n"
            "  완전히 다른 규칙입니다. 숫자가 달라도 상충·불일치가 아니므로 절대 지적하지 마세요.\n"
            "- 같은 내용이 チケット注意事項(짧은 요약)와 NOTICE 탭(상세 설명)에 나뉘어 기재된 경우도\n"
            "  중복 문구로 지적하지 마세요.\n\n"
            "【문구 목록】\n"
            f"{lines}\n\n"
            "【출력 규칙】\n"
            "- 문제가 있는 경우: 각 항목을 번호로 구분하고, 해당 문구를 직접 인용한 뒤 왜 문제인지 + 수정 제안을 작성하세요.\n"
            "- 전혀 문제가 없는 경우: '✅ 이상 없음' 한 줄만 출력하세요.\n"
            "- 한국어로만 출력하세요. 마크다운 볼드(**) 사용 가능."
        )
        msg = client.messages.create(
            model='claude-haiku-4-5-20251001',
            max_tokens=1800,
            messages=[{'role': 'user', 'content': prompt}],
        )
        return msg.content[0].text

    def _validate_local(items):
        import difflib, re
        results = []
        texts   = [txt for _, txt in items]
        sources = [src for src, _ in items]

        # ① 완전 중복
        seen = {}
        for i, txt in enumerate(texts):
            key = txt.strip()
            if key in seen:
                j = seen[key]
                results.append(
                    f"🔴 **중복 문구**\n"
                    f"  · [{sources[j]}] {txt[:80]}\n"
                    f"  · [{sources[i]}] (동일 내용)"
                )
            else:
                seen[key] = i

        # ② 유사 문구 (85% 이상)
        checked = set()
        for i in range(len(texts)):
            for j in range(i + 1, len(texts)):
                if (i, j) in checked: continue
                ratio = difflib.SequenceMatcher(None, texts[i], texts[j]).ratio()
                if 0.85 <= ratio < 1.0:
                    checked.add((i, j))
                    results.append(
                        f"🟡 **유사 문구** (유사도 {ratio:.0%})\n"
                        f"  · [{sources[i]}] {texts[i][:70]}\n"
                        f"  · [{sources[j]}] {texts[j][:70]}"
                    )

        # ③ 연령 제한 패턴
        age_items = [(s, t, list(map(int, re.findall(r'(\d+)\s*(?:歳|才|세|살)', t))))
                     for s, t in items if re.search(r'\d+\s*(?:歳|才|세|살)', t)]
        if len(age_items) >= 2:
            all_ages = sorted({n for _, _, ns in age_items for n in ns})
            results.append(
                f"⚠️ **연령 관련 문구 {len(age_items)}개 감지** "
                f"(언급된 나이: {', '.join(str(a) for a in all_ages)}세) — 기준 일치 여부를 확인하세요.\n"
                + '\n'.join(f"  · [{s}] {t[:80]}" for s, t, _ in age_items)
            )

        # ④ 매수 제한 패턴 (서로 다른 숫자)
        def _purchase_qtys(text):
            # "X枚につき"(1장당 입장 조건) 패턴은 구매 매수 제한이 아니므로 제거
            cleaned = re.sub(r'\d+\s*枚\s*(?:に\s*つき|ごと|当たり|あたり|複数)', '', text)
            return list(map(int, re.findall(r'(\d+)\s*枚', cleaned)))
        qty_items = [(s, t, _purchase_qtys(t)) for s, t in items if _purchase_qtys(t)]
        if len(qty_items) >= 2:
            nums = {n for _, _, ns in qty_items for n in ns}
            if len(nums) > 1:
                results.append(
                    f"⚠️ **매수 제한 숫자 불일치** ({', '.join(str(n) for n in sorted(nums))}매) — 통일 필요\n"
                    + '\n'.join(f"  · [{s}] {t[:80]}" for s, t, _ in qty_items)
                )

        if not results:
            return "✅ 자동 검사에서 이상 없음"
        return '\n\n'.join(results)

    def _extract_poster_palette(url, n=6):
        """포스터 URL에서 채도 높은 색상 n개 추출. 실패 시 []."""
        if not url:
            return []
        try:
            import urllib.request, colorsys
            from io import BytesIO
            from PIL import Image
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=8) as r:
                img = Image.open(BytesIO(r.read())).convert('RGB')
            img.thumbnail((150, 150))
            raw = img.quantize(colors=16).getpalette()[:48]
            candidates = []
            for i in range(0, len(raw), 3):
                rv, gv, bv = raw[i]/255, raw[i+1]/255, raw[i+2]/255
                h, s, v = colorsys.rgb_to_hsv(rv, gv, bv)
                if s > 0.28 and 0.22 < v < 0.92:
                    candidates.append((s, rv, gv, bv))
            candidates.sort(reverse=True)
            return ['#{:02x}{:02x}{:02x}'.format(int(rv*255), int(gv*255), int(bv*255))
                    for _, rv, gv, bv in candidates[:n]]
        except Exception:
            return []

    def _make_ticket_palette(base_hex, n):
        """황금각 회전으로 base_hex와 어울리는 n가지 색상 생성."""
        import colorsys
        try:
            r = int(base_hex[1:3], 16) / 255
            g = int(base_hex[3:5], 16) / 255
            b = int(base_hex[5:7], 16) / 255
        except Exception:
            return [base_hex] * n
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        s, v = max(s, 0.55), min(max(v, 0.50), 0.80)
        golden = 0.618033988749895
        out = []
        for i in range(n):
            nh = (h + i * golden) % 1.0
            nr, ng, nb = colorsys.hsv_to_rgb(nh, s, v)
            out.append('#{:02x}{:02x}{:02x}'.format(int(nr*255), int(ng*255), int(nb*255)))
        return out

    # ── UI ────────────────────────────────────────────────────────────
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("#### Step 1 · 엑셀 템플릿 다운로드")
        st.caption("B열(내용)에만 입력하시면 됩니다. ① 기본정보·디자인 ② 공연개요 ③ 티켓목록 ④ 라인업 ⑤ NOTICE 탭 ⑥ 문의처")
        st.download_button(
            "↓ 템플릿 다운로드 (.xlsx)",
            _make_template(),
            "ticket_template.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    with col_r:
        st.markdown("#### Step 2 · 작성한 엑셀 업로드")
        uploaded_tpl = st.file_uploader("", type=["xlsx", "xls"], label_visibility="collapsed", key="tpl_upload")

    tpl_data = {}
    if uploaded_tpl:
        try:
            df_raw = pd.read_excel(uploaded_tpl, header=None, sheet_name=0, dtype=str)
            for _, row in df_raw.iterrows():
                key = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) and str(row.iloc[0]) != 'nan' else ''
                val = str(row.iloc[1]).strip() if len(row) > 1 and pd.notna(row.iloc[1]) and str(row.iloc[1]) != 'nan' else ''
                if key and key != '항목' and not key.startswith('【') and not key.startswith('──'):
                    tpl_data[key] = val
            st.success(f"✅ {uploaded_tpl.name} 로드 완료 ({len(tpl_data)}개 항목)")
        except Exception as e:
            st.error(f"파일 읽기 오류: {e}")

    if tpl_data:
        # ── 주의사항 검증 ──────────────────────────────────────────────
        notices = _collect_notices(tpl_data)
        if notices:
            st.markdown("#### 🔍 주의사항 자동 검증")
            st.caption(f"티켓 주의사항 및 NOTICE 탭 내용 총 **{len(notices)}개** 항목에서 중복·상충 문구를 검출합니다.")
            if st.button("검증하기", type="secondary", key="validate_btn"):
                with st.spinner("검증 중..."):
                    try:
                        _api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
                    except Exception:
                        _api_key = ""
                    if _api_key:
                        try:
                            val_result = _validate_ai(notices, _api_key)
                        except Exception as _ve:
                            val_result = f"AI 검증 오류: {_ve}\n\n" + _validate_local(notices)
                    else:
                        val_result = _validate_local(notices)
                    st.session_state['ticket_validation'] = val_result
            if st.session_state.get('ticket_validation'):
                st.markdown(st.session_state['ticket_validation'])
                try:
                    _has_key = bool(st.secrets.get("ANTHROPIC_API_KEY", ""))
                except Exception:
                    _has_key = False
                if not _has_key:
                    st.caption("💡 Streamlit Cloud 앱 설정에서 `ANTHROPIC_API_KEY`를 추가하면 AI 기반 정밀 검증을 사용할 수 있습니다.")

        st.markdown("---")
        st.markdown("#### 🎨 カラー設定")
        st.caption("엑셀에서 색상을 지정했어도 여기서 덮어씌울 수 있어요.")

        _excel_btn = tpl_data.get('チケットボタン色', '') or '#8da0a7'
        _excel_pt  = tpl_data.get('ポイントカラー', '') or _excel_btn
        _fbase     = uploaded_tpl.name.replace('.', '_')
        _cnt_key   = f'cp_cnt_{_fbase}'
        if _cnt_key not in st.session_state:
            st.session_state[_cnt_key] = 0
        _fkey_btn  = f'cp_btn_{_fbase}_{st.session_state[_cnt_key]}'
        _fkey_pt   = f'cp_pt_{_fbase}_{st.session_state[_cnt_key]}'
        if _fkey_btn not in st.session_state:
            st.session_state[_fkey_btn] = _excel_btn
        if _fkey_pt not in st.session_state:
            st.session_state[_fkey_pt] = _excel_pt

        _pc1, _pc2, _pc3 = st.columns([2, 2, 1.4])
        with _pc1:
            picked_btn = st.color_picker("🎫 チケットボタン色", key=_fkey_btn)
        with _pc2:
            picked_pt = st.color_picker("✨ ポイントカラー", key=_fkey_pt)
        with _pc3:
            st.markdown("<br>", unsafe_allow_html=True)
            _poster_for_auto = tpl_data.get('ポスターURL', '')
            if _poster_for_auto:
                if st.button("🖼 ポスターから\n自動抽出", use_container_width=True, key=f"auto_color_btn_{st.session_state[_cnt_key]}"):
                    with st.spinner("ポスターから色を抽出中..."):
                        _pal = _extract_poster_palette(_poster_for_auto)
                    if _pal:
                        # 카운터를 올려 color_picker 위젯을 새로 만들어 강제 갱신
                        st.session_state[_cnt_key] += 1
                        _new_btn = f'cp_btn_{_fbase}_{st.session_state[_cnt_key]}'
                        _new_pt  = f'cp_pt_{_fbase}_{st.session_state[_cnt_key]}'
                        st.session_state[_new_btn] = _pal[0]
                        st.session_state[_new_pt]  = _pal[0]
                        st.rerun()
                    else:
                        st.warning("色の抽出に失敗しました。ポスターURLに直接アクセスできるか確認してください。")
            else:
                st.caption("ポスターURLを\n入力すると自動抽出\nできます")

        st.markdown("---")
        st.markdown("#### Step 3 · HTML 생성")
        if st.button("✦ HTML 생성하기", type="primary", use_container_width=True):
            _merged = dict(tpl_data)
            _merged['チケットボタン色'] = picked_btn
            _merged['ポイントカラー']   = picked_pt
            result_html, errs = _generate_html(_merged, _merged, _TICKET_CSS, 'ja')
            if errs:
                for err in errs:
                    st.error(f"⚠ {err}")
            else:
                st.session_state['ticket_gen_html'] = result_html
                st.session_state['ticket_gen_bg']   = _merged.get('背景色', '') or '#191919'
                st.session_state['ticket_gen_data'] = _merged
                st.session_state['ticket_gen_lang'] = 'ja'

    if st.session_state.get('ticket_gen_html'):
        gen_html = st.session_state['ticket_gen_html']
        gen_bg   = st.session_state.get('ticket_gen_bg', '#191919')
        cur_lang = st.session_state.get('ticket_gen_lang', 'ja')
        orig_data = st.session_state.get('ticket_gen_data', {})

        st.divider()

        # ── 언어 전환 버튼 ────────────────────────────────────────────
        lang_label_map = {'ja': '🇯🇵 日本語', 'en': '🇺🇸 English', 'ko': '🇰🇷 한국어'}
        st.markdown(
            f"**언어 / Language** &nbsp;&nbsp;"
            f'<span style="background:#6C63FF;color:#fff;padding:3px 12px;border-radius:12px;font-size:0.82em;font-weight:700">'
            f'{lang_label_map[cur_lang]}</span>',
            unsafe_allow_html=True,
        )
        lc1, lc2, lc3 = st.columns(3)
        for col, code, label in [(lc1, 'ja', '🇯🇵 日本語'), (lc2, 'en', '🇺🇸 English'), (lc3, 'ko', '🇰🇷 한국어')]:
            with col:
                if st.button(label, disabled=(code == cur_lang), use_container_width=True, key=f'lang_{code}'):
                    spinner_msg = {'ja': '원문 복원 중...', 'en': 'Translating to English...', 'ko': '한국어로 번역 중...'}[code]
                    with st.spinner(spinner_msg):
                        translated = _translate_data(orig_data, code)
                        new_html, errs = _generate_html(translated, orig_data, _TICKET_CSS, code)
                    if errs:
                        for e in errs: st.error(e)
                    else:
                        st.session_state['ticket_gen_html'] = new_html
                        st.session_state['ticket_gen_lang'] = code
                        st.rerun()

        st.divider()
        st.markdown("#### 미리보기")
        components_v1.html(gen_html, height=720, scrolling=True)
        st.divider()
        col_d, col_c = st.columns(2)
        with col_d:
            fname = f"ticket_page_{cur_lang}.html"
            st.download_button(
                "↓ HTML 다운로드",
                gen_html.encode('utf-8'),
                fname,
                "text/html;charset=utf-8",
                use_container_width=True,
            )
        with col_c:
            st.text_area("HTML 소스 (복사용)", gen_html, height=200, key="gen_src")

