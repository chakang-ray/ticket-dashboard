import io
import re
import streamlit as st
import pandas as pd
import streamlit.components.v1 as components_v1
from openpyxl import Workbook as _Workbook

st.set_page_config(
    page_title="Qoo10 チケットページ ジェネレーター",
    page_icon="🎨",
    layout="wide",
)

# ── 인증 ──────────────────────────────────────────────────────────────────────
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
            '<div style="text-align:center;font-size:2em;font-weight:800;color:#6C63FF">🎨 チケットページ<br>ジェネレーター</div>',
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

if not _check_auth():
    st.stop()

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


def _extract_poster_palette(url, n=6):
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

    if perf_days:
        sched_html = ''.join(
            f'\n      <div class="info-row">'
            f'<div class="subtitle info-date">{d["date"]}</div>'
            f'<div class="description info-time">{d["time"]}</div>'
            f'</div>'
            for d in perf_days)
    else:
        sched_html = '<div class="info-row"><div class="description">—</div></div>'

    types_distinct = list(dict.fromkeys(t['type'] for t in tickets if t['type']))

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

    lineup_sec = ''
    if lineup_url:
        h = f'  <div class="title"><span class="titlecolor">{lineup_heading}</span></div>\n' if lineup_heading else ''
        lineup_sec = (
            f'\n<!-- lineup -->\n<div class="section-wrap" style="padding-bottom:0;">\n'
            f'{h}  <div class="lineup-section">'
            f'<img src="{esc(lineup_url)}" style="max-width:100%;height:auto;"></div>\n</div>\n'
        )

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

    style_block = (
        '<style>\n:root {\n'
        '  --btn-color:   ' + btn_color + ';\n'
        '  --point-color: ' + point_color + ';\n'
        '  --page-bg:     ' + page_bg + ';\n'
        '}\n'
        + ticket_css + '\n</style>'
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
        "2. 상충 문구: 논리적으로 모순되는 내용 (연령 제한 불일치, 매수 제한 불일치, 입장 조건 모순 등)\n"
        "3. 모호한 표현: 해석에 따라 의미가 달라질 수 있어 분쟁 소지가 있는 표현\n\n"
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
    import difflib
    results = []
    texts   = [txt for _, txt in items]
    sources = [src for src, _ in items]

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

    age_items = [(s, t, list(map(int, re.findall(r'(\d+)\s*(?:歳|才|세|살)', t))))
                 for s, t in items if re.search(r'\d+\s*(?:歳|才|세|살)', t)]
    if len(age_items) >= 2:
        all_ages = sorted({n for _, _, ns in age_items for n in ns})
        results.append(
            f"⚠️ **연령 관련 문구 {len(age_items)}개 감지** "
            f"(언급된 나이: {', '.join(str(a) for a in all_ages)}세) — 기준 일치 여부를 확인하세요.\n"
            + '\n'.join(f"  · [{s}] {t[:80]}" for s, t, _ in age_items)
        )

    qty_items = [(s, t, list(map(int, re.findall(r'(\d+)\s*枚', t))))
                 for s, t in items if re.search(r'\d+\s*枚', t)]
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


# ── UI ────────────────────────────────────────────────────────────────────────
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
    _fkey_btn  = f'cp_btn_{uploaded_tpl.name}'
    _fkey_pt   = f'cp_pt_{uploaded_tpl.name}'
    if _fkey_btn not in st.session_state:
        st.session_state[_fkey_btn] = _excel_btn
    if _fkey_pt not in st.session_state:
        st.session_state[_fkey_pt] = _excel_pt

    _pc1, _pc2, _pc3 = st.columns([2, 2, 1.4])
    with _pc1:
        st.color_picker("🎫 チケットボタン色", key=_fkey_btn)
    with _pc2:
        st.color_picker("✨ ポイントカラー", key=_fkey_pt)
    with _pc3:
        st.markdown("<br>", unsafe_allow_html=True)
        _poster_for_auto = tpl_data.get('ポスターURL', '')
        if _poster_for_auto:
            if st.button("🖼 ポスターから\n自動抽出", use_container_width=True, key="auto_color_btn"):
                with st.spinner("ポスターから色を抽出中..."):
                    _pal = _extract_poster_palette(_poster_for_auto)
                if _pal:
                    st.session_state[_fkey_btn] = _pal[0]
                    st.session_state[_fkey_pt]  = _pal[0]
                    st.rerun()
                else:
                    st.warning("色の抽出に失敗しました。URLを確認してください。")
        else:
            st.caption("ポスターURLを\n入力すると自動抽出\nできます")

    st.markdown("---")
    st.markdown("#### Step 3 · HTML 생성")
    if st.button("✦ HTML 생성하기", type="primary", use_container_width=True):
        _merged = dict(tpl_data)
        _merged['チケットボタン色'] = st.session_state.get(_fkey_btn, _excel_btn)
        _merged['ポイントカラー']   = st.session_state.get(_fkey_pt, _excel_pt)
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
