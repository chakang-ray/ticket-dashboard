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


st.title("🎨 Qoo10 チケットページ ジェネレーター")
st.caption("엑셀 템플릿에 공연 정보를 입력하고 업로드하면 HTML을 자동 생성합니다. / ExcelテンプレートをアップロードするとHTMLを自動生成します。")
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
    '.ev-section{padding:56px 16px 48px;text-align:center;}\n'
    '.ev-inner{max-width:750px;margin:0 auto;}\n'
    '.ev-kicker{font-size:11px;font-weight:800;letter-spacing:.22em;color:var(--point-color);text-transform:uppercase;margin:0 0 10px;}\n'
    '.ev-heading{font-family:"Montserrat",sans-serif;font-weight:900;font-size:60px;margin:0 0 40px;padding:0;line-height:1;}\n'
    '.ev-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:20px;}\n'
    '.ev-card{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.1);border-radius:20px;padding:28px 20px;text-align:center;}\n'
    '.ev-label{font-size:10px;font-weight:800;letter-spacing:.22em;color:var(--point-color);text-transform:uppercase;margin:0 0 14px;}\n'
    '.ev-main{font-size:20px;font-weight:800;color:#fff;line-height:1.35;margin:0 0 8px;}\n'
    '.ev-sub{font-size:14px;color:rgba(255,255,255,.62);font-weight:500;line-height:1.6;margin:0;}\n'
    '.ev-addr{font-size:12px;color:rgba(255,255,255,.48);font-weight:400;line-height:1.55;margin:6px 0 16px;}\n'
    '.ev-addr:empty{display:none;}\n'
    '.ev-map-btn{display:inline-flex;align-items:center;gap:6px;padding:8px 18px;border-radius:8px;border:1px solid rgba(255,255,255,.22);background:rgba(255,255,255,.07);color:rgba(255,255,255,.8);font-size:12px;font-weight:700;letter-spacing:.06em;text-decoration:none;transition:background .18s,border-color .18s;}\n'
    '.ev-map-btn:hover{background:rgba(255,255,255,.14);border-color:rgba(255,255,255,.4);color:#fff;}\n'
    '.ev-map-btn[data-hidden]{display:none;}\n'
    '@media(max-width:768px){.ev-heading{font-size:45px;}.ev-section{padding:40px 16px 36px;}}\n'
    '@media(max-width:480px){.ev-card{padding:22px 16px;}.ev-main{font-size:17px;}.ev-heading{font-size:38px;margin-bottom:28px;}}\n'
    '#sticky-nav{position:sticky;top:0;z-index:100;display:flex;justify-content:center;background:rgba(0,0,0,0.62);backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);}\n'
    '.snav-tab{display:inline-flex;align-items:center;padding:14px 36px;color:rgba(255,255,255,0.48);font-family:"Montserrat",sans-serif;font-weight:800;font-size:12px;letter-spacing:.2em;text-decoration:none;border-bottom:3px solid transparent;transition:color .2s,border-color .2s;-webkit-tap-highlight-color:transparent;}\n'
    '.snav-tab.is-active{color:#fff;border-bottom-color:var(--point-color);}\n'
)


def _make_template(lottery=False):
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
        ['会場_住所', '', '例: 東京都港区北青山2丁目8-35（空白でGoogleMapボタン非表示）'],
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
        *([
            ['申込期間', '2026年○月○日(○) ○○:00 ～ ○月○日(○) 23:59まで', '応募受付期間'],
            ['当落発表日', '2026年○月○日(○) 予定', ''],
            ['入金期限', '2026年○月○日(○) ○○:59まで', ''],
        ] if lottery else [
            ['販売期間', '2026年○月○日(○) ○○:00 ～ 各公演の2日前 23:59まで', ''],
            ['販売期間注記', '※予定枚数に達し次第受付終了', '赤字。なければ空白'],
        ]),
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
            'チケット1枚につき1名様のみご入場可能となります。1枚のチケットを複数のお客様で使用することは出来ません。',
            'チケットは数量限定で販売され、売り切れ次第終了する場合がございます。',
            'チケットは券面に記載の公演日・会場でのみ有効となります。',
            'チケットの譲渡・転売が発覚した場合は、チケットの没収の上退場していただきます。',
            '本公演のチケットご購入には、Qoo10 会員登録（無料）が必要になります。',
            'お申込みの際のQoo10会員登録情報が購入者本人としてチケットに登録されます。当日はご本人様確認を行う可能性がございますので、お申し込み前に会員登録情報を今一度ご確認ください。',
            'ご登録情報に不備があった場合のトラブルに関して弊社は責任を負いかねます。',
            '本公演のチケットは全て電子チケット引取となり、チケット引取にはQoo10アプリが必要となります。',
            '電子チケットはQoo10で発券されます。',
            'チケットの発券（座席番号情報の共有）は、公演前日13時頃を予定しております。',
            '一般販売でチケットをご購入された場合は、公演当日13時より発券（座席番号の表示）が可能となる予定です。',
            'ご購入いただいたチケットはMy＞チケット一覧よりご確認いただけます。',
            'ドメイン・指定受信アドレス指定受信を設定されている場合は、【@qoo10.jp】からのメールが受信出来るよう設定してください。',
            'チケット料金とは別に、下記の手数料が発生致します。',
            '1) システム利用料：ご購入のチケット1枚につき 000円',
            '2) 特別販売利用料：ご購入のチケット1枚につき 000円',
            '3) 発券手数料：ご購入のチケット1枚につき 000円',
            '営利を目的として、チケットの予約・購入を行い、転売する行為を禁止いたします。',
            '主催者側等の都合により、受付方式・日時、会場等が変更になる場合もございますのでご了承ください。',
            'インターネットの途中経路の障害やお客様のご利用されているメールサーバ、端末の設定の問題等による遅配・未配につきましては、弊社はその責任を一切負いません。',
            '同伴者の方に電子チケットをお渡しする「分配機能」がございます。',
            '分配先の情報（お名前、電話番号、メールアドレス）は購入時の「購入情報入力」画面でご記入いただく必要がございます。',
            '分配が可能となるのはチケットの発券以降です。',
            '分配先情報の修正はできません。',
            '購入者様ご本人のチケットは分配できません。',
            '分配先の同伴者様は、分配時にQoo10アプリの会員登録が必要となります。',
            '分配せずに入場することも可能です。その場合は、購入者様のアプリ上で複数枚の電子チケットを表示し、同伴者様とご一緒にご入場ください。',
            '海外銀行口座からの送金・国際送金（SWIFT等）はご利用いただけません。',
            '（Transfers from overseas bank accounts and international wire transfers (including SWIFT) are not supported.）',
        ]),
        ('入場のご案内', '●', [
            '公演は全席指定、先着順入場となります。詳細な入場手続きは今後、SNS チャンネルおよびウェブサイトを通じて案内されます。',
            'ご購入されたチケットの変更、キャンセル、払い戻しはお受けできません。',
            '公演当日は、ご本人様確認をさせていただく場合がございますので、身分証明書をご持参ください。',
            '例：運転免許証、旅券(パスポート)、個人番号(マイナンバー)カード、学生証 (写真付きのものに限る)、在留カードなど',
            '開場・開演時間は変更となる場合がございます。',
            'ご入場の際は電子チケットをご提示ください。',
            'ご入場前に電子チケットを表示した状態でお待ちください。',
            'チケットをお持ちでない方はご入場いただけません。',
            '再入場はできません。',
        ]),
        ('公演に関する注意事項', '●', [
            '本公演はお座席によって一部演出が見えづらい場合がございます。予めご了承ください。',
            '出演者、開場・開演時間は変更となる場合がございます。詳しくはオフィシャルSNSをご確認ください。',
            'お申込み・ご購入されたチケットの変更、キャンセル、払い戻しはお受けできません。',
            '出演アーティストは都合によりキャンセル・変更となる場合があります。その際のチケットの払い戻しはいたしませんので予めご了承ください。 再入場は不可となります。',
            '入場時全てのお客様を対象にご本人様確認と、手荷物検査を実施予定です。 ご本人様確認と手荷物検査の実施をご確認・ご理解・ご了承の上、チケットをお申し込み・ご購入ください。',
            '本公演にて手荷物をお預かりすることはできません。 持ち込み禁止物につきましては、必ず入場前にお預けになってからご来場をお願いいたします。',
            'ご本人様確認の方法、ご手荷物検査の詳細や持ち込み禁止物につきましては随時オフィシャルSNSにて告知いたしますので、ご来場前に必ずご確認をお願いいたします。',
            'ご本人様確認の際、お申込み・購入時にご入力いただく来場者様情報が有効となります。 ご購入者様の情報は変更できませんので、購入の前に必ずご確認ください。',
            'チケットの譲渡・転売が発覚した場合は、チケット没収の上退場していただきます。',
            '各アーティストへのプレゼント、アレンジフラワー(祝い花)、楽屋花の受け取りは行っておりません。 企業様においてもお受け取りできませんのでご了承ください。',
            '入待ち、出待ち行為は出演者だけでなく、会場や周辺施設・住民のご迷惑となりますので、絶対におやめください。',
            '公演中会場内の撮影、録音、録画、ストリーミング行為は禁止となります。 禁止行為が発覚した場合、チケット没収の上退場となりますのであらかじめご了承ください。',
            'チケットの紛失、破棄、盗難、破損、持ち忘れにおいて、いかなる場合もチケットの再発行はいたしません。 また持ち忘れの場合、当日はご入場いただけませんのでかならずお持ちください。',
            'その他主催者側が要請するルールやマナーを遵守できない場合は入場をお断りもしくは、ご退場いただく場合もございます。',
            '政府・自治体などの方針に則り、公演の内容やお客様へのご案内および注意事項が変更になる場合がございます。 変更が生じた場合でも、チケットの払戻しはできかねますのであらかじめご了承ください。',
            '年齢に関わらず、チケット1枚につき、1名様のみご入場いただけます。ご入場時は、有効なチケットが必要となります。3歳未満のお子様は、ご入場いただけません。',
            '安全のため、3歳未満のお子様は、指定席エリアにご入場いただけません。',
            '一度のお申し込み・ご購入につき、最大4枚までお申し込み・ご購入いただけます。',
            'お申し込み・ご購入いただいたチケットは、譲渡不可、払い戻し不可、交換不可となります。原則として、チケットの再発行はいたしかねます。',
            '一部ゾーン・座席は、会場内の構造物（柱、壁、支柱など）や演出機材、他の座席などにより、視界が制限されることがあります。',
            '上記を理由に、キャンセルや座席変更、払い戻しはできません。視界が制限される度合いは、座席位置や個人差により異なる場合があります。',
            '公演当日、制限された視界によるキャンセルや座席変更、払い戻しはお受付いたしかねますので、チケットをご購入いただく前に、チケットプラットフォームの約款を必ずご確認ください。',
        ]),
        ('電子チケット・お問い合わせのご案内', '●', [
            '電子チケット使用方法はコチラのURLをご参考ください。',
            '▶https://www.qoo10.jp/gmkt.inc/Special/Special.aspx?sid=354258',
            'チケットのご購入に関するお問い合わせ',
            '▶ お問い合わせフォーム',
            '※カテゴリは「イベント／クーポン ＞ 公演・チケット」をご選択ください。',
            '※お問い合わせの際にはタイトルに【公演名】、本文にお客様のID/注文番号(チケット購入済みの場合のみ)をご記載ください。',
            '公演に関するお問い合わせ',
            '000-000-0000',
            '（月･水･金･土 10:00〜18:00)',
        ]),
        ('', '●', []),
        ('', '●', []),
    ]
    for ti, (name, style, contents) in enumerate(tab_defs, 1):
        rows.append([f'── タブ{ti} ──', '', ''])
        rows.append([f'タブ{ti}_名称',   name,  'タブボタンに表示される名前'])
        rows.append([f'タブ{ti}_スタイル', style, '箇条書きの種類: ●（丸）/ ＊（星）/ ※（重要）/ なし'])
        for ci in range(1, 31):
            note = '자유롭게 수정·삭제 가능 / 自由に編集・削除できます' if ci == 1 else ''
            rows.append([f'タブ{ti}_内容{ci}', contents[ci - 1] if ci <= len(contents) else '', note])
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


def _extract_palette_from_bytes(img_bytes, n=6):
    try:
        import colorsys
        from io import BytesIO
        from PIL import Image
        img = Image.open(BytesIO(img_bytes)).convert('RGB')
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

    title         = g('タイトル').replace('\\n', '<br>')
    poster        = g('ポスターURL')
    venue         = g('会場')
    venue_address = g('会場_住所')
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
    _is_lottery_type = bool(g('申込期間'))
    sale_period       = g('申込期間') if _is_lottery_type else g('販売期間')
    sale_period_label = '申込期間' if _is_lottery_type else '販売期間'
    sale_note        = '' if _is_lottery_type else g('販売期間注記')
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
        tabs.append({'name': name, 'cls': bullet_cls(g(f'タブ{t}_スタイル')), 'items': collect(f'タブ{t}_内容', 30)})

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
        _day_label = lbl['perf_datetime']
        _date_cards = ''
        for _idx, _d in enumerate(perf_days):
            _card_label = f'Day {_idx + 1}' if len(perf_days) > 1 else _day_label
            _sub = f'<p class="ev-sub">{_d["time"]}</p>' if _d["time"] else ''
            _date_cards += (
                f'\n      <article class="ev-card">'
                f'<p class="ev-label">{_card_label}</p>'
                f'<p class="ev-main">{_d["date"]}</p>'
                f'{_sub}'
                f'</article>'
            )
    else:
        _date_cards = (
            f'\n      <article class="ev-card">'
            f'<p class="ev-label">{lbl["perf_datetime"]}</p>'
            f'<p class="ev-main">—</p>'
            f'</article>'
        )
    _map_url = ('https://www.google.com/maps/search/?api=1&query='
                + venue_address.replace(' ', '+')) if venue_address else ''
    _map_hidden = '' if venue_address else ' data-hidden="1"'
    _venue_card = (
        f'\n      <article class="ev-card">'
        f'<p class="ev-label">{lbl["venue"]}</p>'
        f'<p class="ev-main">{venue}</p>'
        f'<p class="ev-addr">{venue_address}</p>'
        f'<a class="ev-map-btn" href="{_map_url}" target="_blank" rel="noopener"{_map_hidden}>Google Map &nbsp;→</a>'
        f'</article>'
    ) if venue else ''
    sched_sec = (
        '<!-- schedule -->\n'
        '<section class="ev-section">\n'
        '  <div class="ev-inner">\n'
        '    <p class="ev-kicker">ABOUT THE EVENT</p>\n'
        '    <h2 class="ev-heading"><span class="titlecolor">SCHEDULE</span></h2>\n'
        '    <div class="ev-grid">\n'
        + _date_cards
        + _venue_card
        + '\n    </div>\n'
        '  </div>\n'
        '</section>\n\n'
    )

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
    sp_html       = f'      <p class="ticket-note" style="color:BLACK;">{sale_period_label}<BR>{sale_period}</p>\n' if sale_period else ''
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
    _sticky_nav = (
        '<nav id="sticky-nav">\n'
        '  <a class="snav-tab is-active" href="#section-ticket" data-target="section-ticket">TICKET</a>\n'
        '  <a class="snav-tab" href="#section-notice" data-target="section-notice">NOTICE</a>\n'
        '</nav>\n'
    )
    _scrollspy_js = (
        '<script>\n'
        '(function(){\n'
        '  var tabs=document.querySelectorAll(".snav-tab");\n'
        '  var ids=["section-ticket","section-notice"];\n'
        '  var sections=ids.map(function(id){return document.getElementById(id);}).filter(Boolean);\n'
        '  tabs.forEach(function(tab){\n'
        '    tab.addEventListener("click",function(e){\n'
        '      e.preventDefault();\n'
        '      var target=document.getElementById(tab.dataset.target);\n'
        '      if(target){\n'
        '        var navH=document.getElementById("sticky-nav").offsetHeight;\n'
        '        var top=target.getBoundingClientRect().top+window.scrollY-navH-8;\n'
        '        window.scrollTo({top:top,behavior:"smooth"});\n'
        '      }\n'
        '    });\n'
        '  });\n'
        '  function updateActive(){\n'
        '    var navH=document.getElementById("sticky-nav").offsetHeight;\n'
        '    var scrollY=window.scrollY+navH+60;\n'
        '    var current=sections[0]?sections[0].id:"";\n'
        '    sections.forEach(function(s){\n'
        '      if(s.getBoundingClientRect().top+window.scrollY<=scrollY) current=s.id;\n'
        '    });\n'
        '    tabs.forEach(function(tab){\n'
        '      tab.classList.toggle("is-active",tab.dataset.target===current);\n'
        '    });\n'
        '  }\n'
        '  window.addEventListener("scroll",updateActive,{passive:true});\n'
        '  updateActive();\n'
        '})();\n'
        '</script>\n'
    )
    _body_content = (
        '<!-- title -->\n'
        f'<div class="toptitle">{title}</div>\n\n'
        + poster_sec
        + sched_sec
        + '<!-- ticket -->\n'
        '<div id="section-ticket" class="section-wrap">\n'
        '  <div class="title"><span class="titlecolor">TICKETS</span></div>\n'
        '  <div class="ticket-box">\n'
        '    <div class="ticket-info">\n'
        + f'      <h2 class="ticket-title">{section_title}</h2>\n'
        + sp_html
        + lottery_html
        + deadline_html
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
        '<div id="section-notice" class="section-wrap">\n'
        '  <div class="title"><p class="ev-kicker" style="margin:0 0 8px;">NOTICE</p><span class="titlecolor">注意事項</span></div>\n'
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
        + _sticky_nav
        + _body_content
        + '</div>\n'
        + _scrollspy_js
        + '</body>\n</html>\n'
    )
    return html_out, []


def _block_links(html: str) -> str:
    """미리보기에서 모든 <a> 링크 이동을 차단한다."""
    script = (
        '<script>'
        'document.addEventListener("click",function(e){'
        'var a=e.target.closest("a");if(a){e.preventDefault();e.stopPropagation();}'
        '},true);'
        '</script>'
    )
    return html.replace('</body>', script + '</body>') if '</body>' in html else html + script


def _inject_editable(html: str, ok_label: str = '✅ 편집완료/다운로드', rs_label: str = '↩ 되돌리기', hint_label: str = '✏️ 클릭하여 편집') -> str:
    """미리보기 HTML에 contenteditable 툴바를 주입한다."""
    _js = r"""(function(){
var S=['.toptitle','.subtitle.info-date','.description.info-time',
  '.description.info-venue','.subtitle.info-label',
  '.ticket-title','.ticket-note',
  '.ticketType','.ticketDay','.ticketDate','.ticketPrice',
  '.ticket-notice li','.oshirase dd','.oshirase dt','.title .titlecolor',
  '.ev-card .ev-main','.ev-card .ev-sub','.ev-card .ev-addr'];
var O=new Map();
function _setupDdEnter(dd){
  dd.addEventListener('keydown',function(ev){
    if(ev.key==='Enter'&&!ev.shiftKey){
      ev.preventDefault();
      var dl=dd.parentNode;
      var nd=document.createElement('dd');nd.className=dd.className||'list';
      nd.setAttribute('contenteditable','true');nd.setAttribute('spellcheck','false');
      nd.addEventListener('click',function(e){e.stopPropagation();});
      _setupDdEnter(nd);
      dl.insertBefore(nd,dd.nextSibling);
      nd.focus();
    }
  });
}
function mk(){S.forEach(function(s){document.querySelectorAll(s).forEach(function(el){
  if(!O.has(el))O.set(el,el.innerHTML);
  el.setAttribute('contenteditable','true');el.setAttribute('spellcheck','false');
  el.addEventListener('click',function(e){e.stopPropagation();});
  if(el.matches('.oshirase dd'))_setupDdEnter(el);
});});}
function rm(){document.querySelectorAll('[contenteditable]').forEach(function(el){
  el.removeAttribute('contenteditable');el.removeAttribute('spellcheck');});}
document.addEventListener('click',function(e){var a=e.target.closest('a');if(a){e.preventDefault();e.stopPropagation();}},true);

var _initTL='',_initNL='',_initTabs='';
(function(){
  var tl=document.querySelector('.ticketList');
  var nl=document.querySelector('.ticket-notice');
  var tw=document.querySelector('.infotabs');
  if(tl)_initTL=tl.outerHTML;
  if(nl)_initNL=nl.outerHTML;
  if(tw)_initTabs=tw.outerHTML;
})();

function _dBtn(cls){
  var b=document.createElement('button');
  b.className=cls+' __ied_ctrl';b.textContent='✕';
  return b;
}
function _aBtn(id,txt){
  var b=document.createElement('button');
  b.id=id;b.className='__ied_add __ied_ctrl';b.textContent=txt;
  return b;
}
function setupTickets(){
  var tl=document.querySelector('.ticketList');if(!tl)return;
  tl.querySelectorAll('.__del_t').forEach(function(b){b.remove();});
  tl.querySelectorAll('.ticketItem').forEach(function(li){
    var b=_dBtn('__del_t');
    b.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();li.remove();});
    li.appendChild(b);
  });
  var ea=document.getElementById('__add_t');if(ea)ea.remove();
  var ab=_aBtn('__add_t','＋ チケット追加 / 티켓 추가');
  ab.addEventListener('click',function(e){
    e.preventDefault();e.stopPropagation();
    var tl2=document.querySelector('.ticketList');
    var items=tl2.querySelectorAll('.ticketItem');
    var last=items[items.length-1];if(!last)return;
    var clone=last.cloneNode(true);
    clone.querySelectorAll('.__ied_ctrl').forEach(function(b){b.remove();});
    var a=clone.querySelector('.ticketBtn');
    if(a){a.classList.remove('is-disabled','st-uketsuke-yotei','st-hanbai-shuryo','st-soldout');a.href='#';}
    clone.querySelectorAll('span').forEach(function(s){
      if(s.classList.contains('ticketType'))s.textContent='チケット種別';
      else if(s.classList.contains('ticketDay'))s.textContent='0/00(月)';
      else if(s.classList.contains('ticketDate'))s.textContent='00:00開演';
      else if(s.classList.contains('ticketPrice'))s.textContent='¥0,000';
    });
    var db=_dBtn('__del_t');
    db.addEventListener('click',function(ev){ev.preventDefault();ev.stopPropagation();clone.remove();});
    clone.appendChild(db);
    tl2.appendChild(clone);mk();
  });
  tl.parentNode.insertBefore(ab,tl.nextSibling);
}
function setupNotices(){
  var nl=document.querySelector('.ticket-notice');if(!nl)return;
  nl.querySelectorAll('.__del_n').forEach(function(b){b.remove();});
  nl.querySelectorAll('li').forEach(function(li){
    var b=_dBtn('__del_n');
    b.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();li.remove();});
    li.appendChild(b);
  });
  var ea=document.getElementById('__add_n');if(ea)ea.remove();
  var ab=_aBtn('__add_n','＋ 注意事項追加 / 주의사항 추가');
  ab.addEventListener('click',function(e){
    e.preventDefault();e.stopPropagation();
    var nl2=document.querySelector('.ticket-notice');
    var li=document.createElement('li');
    li.textContent='注意事項を入力してください';
    li.setAttribute('contenteditable','true');li.setAttribute('spellcheck','false');
    li.addEventListener('click',function(ev){ev.stopPropagation();});
    var b=_dBtn('__del_n');
    b.addEventListener('click',function(ev){ev.preventDefault();ev.stopPropagation();li.remove();});
    li.appendChild(b);
    nl2.appendChild(li);
  });
  nl.parentNode.insertBefore(ab,nl.nextSibling);
}
function _ensureTabCSS(n){
  var id='__tab_ext_css';
  var el=document.getElementById(id);
  if(!el){el=document.createElement('style');el.id=id;document.head.appendChild(el);}
  el.textContent+='#tab'+n+':checked ~ .infotab__nav label[for="tab'+n+'"]{background:var(--point-color);color:#121113;}'+
    '#tab'+n+':checked ~ .infotab__panels .panel'+n+'{display:block;}';
}
function setupTabs(){
  var infotabs=document.querySelector('.infotabs');if(!infotabs)return;
  var nav=infotabs.querySelector('.infotab__nav');if(!nav)return;
  var panels=infotabs.querySelector('.infotab__panels');if(!panels)return;
  nav.querySelectorAll('.__tab_edit').forEach(function(b){b.remove();});
  nav.querySelectorAll('.infotab__label').forEach(function(lbl){
    var eb=document.createElement('button');
    eb.textContent='✏';eb.className='__tab_edit __ied_ctrl';eb.title='탭 이름 수정';
    eb.addEventListener('click',function(e){
      e.preventDefault();e.stopPropagation();
      var cur='';
      lbl.childNodes.forEach(function(n){if(n.nodeType===3)cur+=n.textContent;});
      cur=cur.trim();
      var newName=window.prompt('탭 이름 수정 / タブ名を編集:',cur);
      if(newName!==null&&newName.trim()){
        while(lbl.firstChild){lbl.removeChild(lbl.firstChild);}
        lbl.appendChild(document.createTextNode(newName.trim()));
        lbl.appendChild(eb);
      }
    });
    lbl.appendChild(eb);
  });
  var ea=document.getElementById('__add_tab');if(ea)ea.remove();
  var ab=_aBtn('__add_tab','＋ タブ追加 / 탭 추가');
  ab.addEventListener('click',function(e){
    e.preventDefault();e.stopPropagation();
    var inputs=infotabs.querySelectorAll('.infotab__input');
    var n=inputs.length+1;
    _ensureTabCSS(n);
    var inp=document.createElement('input');
    inp.type='radio';inp.name='tab';inp.id='tab'+n;inp.className='infotab__input';
    infotabs.insertBefore(inp,nav);
    var tname=window.prompt('새 탭 이름 / 新しいタブ名:','タブ'+n);
    if(tname===null||!tname.trim())tname='タブ'+n;
    var lbl=document.createElement('label');
    lbl.setAttribute('for','tab'+n);lbl.className='infotab__label';
    lbl.textContent=tname.trim();
    nav.appendChild(lbl);
    var panel=document.createElement('div');
    panel.className='infotab__content panel'+n;
    var inner=document.createElement('div');inner.className='oshirase';
    var dl=document.createElement('dl');
    var dd=document.createElement('dd');dd.className='list';
    dd.textContent='内容を入力してください / 내용을 입력하세요';
    dd.setAttribute('contenteditable','true');dd.setAttribute('spellcheck','false');
    dd.addEventListener('click',function(ev){ev.stopPropagation();});
    _setupDdEnter(dd);
    dl.appendChild(dd);inner.appendChild(dl);panel.appendChild(inner);
    panels.appendChild(panel);
    setupTabs();mk();
  });
  nav.parentNode.insertBefore(ab,panels.nextSibling);
}
function setupCtrls(){setupTickets();setupNotices();setupTabs();}
function removeCtrls(){document.querySelectorAll('.__ied_ctrl').forEach(function(b){b.remove();});}

function showSavedMsg(){
  var msg=document.createElement('div');
  msg.style.cssText='position:fixed;bottom:28px;left:50%;transform:translateX(-50%);'+
    'background:#22c55e;color:#fff;padding:12px 28px;border-radius:999px;font-family:sans-serif;'+
    'font-size:13px;font-weight:700;z-index:999999;box-shadow:0 4px 16px rgba(0,0,0,.4);white-space:nowrap;';
  msg.textContent='✅ 저장완료！ 아래 [편집본 다운로드] 버튼을 클릭하세요';
  document.body.appendChild(msg);
  setTimeout(function(){
    msg.style.transition='opacity .5s';msg.style.opacity='0';
    setTimeout(function(){if(msg.parentNode)msg.parentNode.removeChild(msg);},500);
  },4000);
}

mk();setupCtrls();
(function(){
  document.querySelectorAll('.ev-card .ev-addr').forEach(function(addr){
    addr.addEventListener('input',function(){
      var btn=this.nextElementSibling;
      if(btn&&btn.classList.contains('ev-map-btn')){
        var q=encodeURIComponent(this.textContent.trim());
        if(q){btn.href='https://www.google.com/maps/search/?api=1&query='+q;btn.removeAttribute('data-hidden');}
        else{btn.href='';btn.setAttribute('data-hidden','1');}
      }
    });
  });
})();

document.getElementById('__ied_ok').addEventListener('click',function(){
  removeCtrls();rm();
  var bar=document.getElementById('__ied_bar');
  var sty=document.getElementById('__ied_s');
  var scr=document.getElementById('__ied_j');
  bar.remove();sty.remove();scr.remove();
  var out='<!DOCTYPE html>\n'+document.documentElement.outerHTML;
  try{localStorage.setItem('ticket_edited_html',out);}catch(e){}
  document.body.appendChild(bar);document.head.appendChild(sty);document.body.appendChild(scr);
  showSavedMsg();
  mk();setupCtrls();
});
document.getElementById('__ied_rs').addEventListener('click',function(){
  O.forEach(function(v,el){if(document.contains(el))el.innerHTML=v;});
  var tl=document.querySelector('.ticketList');
  if(tl&&_initTL){var d=document.createElement('div');d.innerHTML=_initTL;tl.parentNode.replaceChild(d.firstChild,tl);}
  var nl=document.querySelector('.ticket-notice');
  if(nl&&_initNL){var d2=document.createElement('div');d2.innerHTML=_initNL;nl.parentNode.replaceChild(d2.firstChild,nl);}
  var tw=document.querySelector('.infotabs');
  if(tw&&_initTabs){var d3=document.createElement('div');d3.innerHTML=_initTabs;tw.parentNode.replaceChild(d3.firstChild,tw);}
  removeCtrls();mk();setupCtrls();
});
})();"""
    _css = (
        '#__ied_bar{position:fixed;top:10px;right:10px;z-index:99999;'
        'background:rgba(18,18,20,.95);backdrop-filter:blur(8px);border-radius:10px;'
        'padding:8px 14px;display:flex;align-items:center;gap:8px;font-family:sans-serif;'
        'box-shadow:0 4px 20px rgba(0,0,0,.5);}'
        '.ied-h{color:rgba(255,255,255,.45);font-size:11px;}'
        '.ied-b{border:none;border-radius:6px;padding:6px 12px;cursor:pointer;'
        'font-weight:700;font-size:11px;transition:all .15s;white-space:nowrap;}'
        '#__ied_ok{background:#6C63FF;color:#fff;}'
        '#__ied_ok:hover{background:#5a51e8;}'
        '#__ied_rs{background:transparent;color:rgba(255,255,255,.5);'
        'border:1px solid rgba(255,255,255,.2);}'
        '#__ied_rs:hover{background:rgba(255,255,255,.08);color:#fff;}'
        '[contenteditable]{cursor:text;border-radius:2px;}'
        '[contenteditable]:hover{outline:1px dashed rgba(108,99,255,.65);outline-offset:3px;}'
        '[contenteditable]:focus{outline:2px solid #6C63FF!important;outline-offset:3px;}'
        '.ev-addr:empty{display:block!important;min-height:1.4em;}'
        '.ev-addr[contenteditable]:empty::before{content:"住所を入力… (例: 東京都港区北青山2丁目8-35)";color:rgba(255,255,255,.25);pointer-events:none;}'
        '.ev-map-btn[data-hidden]{display:inline-flex!important;opacity:.35;}'
        '.ticketItem{position:relative!important;}'
        '.__del_t{position:absolute;top:-8px;right:-8px;z-index:10;width:22px;height:22px;'
        'border-radius:50%;border:none;background:#ff4444;color:#fff;font-size:11px;'
        'cursor:pointer;font-weight:700;line-height:22px;text-align:center;'
        'box-shadow:0 2px 6px rgba(0,0,0,.3);padding:0;}'
        '.__del_n{display:inline-block;margin-left:6px;width:18px;height:18px;'
        'border-radius:50%;border:none;background:#ff4444;color:#fff;font-size:10px;'
        'cursor:pointer;font-weight:700;line-height:18px;text-align:center;'
        'vertical-align:middle;padding:0;}'
        '.__ied_add{display:block;margin:10px auto 0;padding:8px 0;max-width:540px;width:100%;'
        'border:2px dashed #6C63FF;border-radius:8px;background:transparent;'
        'color:#6C63FF;font-size:13px;font-weight:700;cursor:pointer;}'
        '.__ied_add:hover{background:rgba(108,99,255,.08);}'
        '.__tab_edit{display:inline-block;margin-left:4px;width:16px;height:16px;'
        'border-radius:50%;border:none;background:rgba(108,99,255,.7);color:#fff;font-size:9px;'
        'cursor:pointer;font-weight:700;line-height:16px;text-align:center;vertical-align:middle;padding:0;}'
        '.__tab_edit:hover{background:#6C63FF;}'
    )
    _inject = (
        f'<style id="__ied_s">{_css}</style>\n'
        '<div id="__ied_bar">'
        f'<span class="ied-h">{hint_label}</span>'
        f'<button class="ied-b" id="__ied_rs">{rs_label}</button>'
        f'<button class="ied-b" id="__ied_ok">{ok_label}</button>'
        '</div>\n'
        f'<script id="__ied_j">{_js}</script>'
    )
    return html.replace('</body>', _inject + '\n</body>', 1)


def _collect_notices(data):
    items = []
    for i in range(1, 6):
        v = str(data.get(f'チケット注意{i}', '') or '').strip()
        if v:
            items.append(('チケット注意事項', v))
    for t in range(1, 7):
        tab_name = str(data.get(f'タブ{t}_名称', '') or '').strip()
        if not tab_name: break
        for c in range(1, 31):
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

    if not results:
        return "✅ 자동 검사에서 이상 없음"
    return '\n\n'.join(results)


# ── UI 텍스트 (한국어 / 日本語) ────────────────────────────────────────────────
_UI_TEXT = {
    'ko': {
        's1':        'Step 1 · 엑셀 템플릿 다운로드',
        's1_cap':    'B열(내용)에만 입력하시면 됩니다. ① 기본정보·디자인 ② 공연개요 ③ 티켓목록 ④ 라인업 ⑤ NOTICE 탭 ⑥ 문의처',
        'type_label':   '티켓 판매 방식',
        'type_instant': '즉시구매 (선착순)',
        'type_lottery': '응모형 (추첨)',
        's2':        'Step 2 · 작성한 엑셀 업로드',
        'dl_tpl':    '↓ 템플릿 다운로드 (.xlsx)',
        'load_ok':   '로드 완료',
        'load_err':  '파일 읽기 오류',
        'v_head':    '🔍 주의사항 자동 검증',
        'v_items':   '개',
        'v_suffix':  '항목에서 중복·상충 문구를 검출합니다.',
        'v_btn':     '검증하기',
        'v_spin':    '검증 중...',
        'v_hint':    '💡 Streamlit Cloud 앱 설정에서 `ANTHROPIC_API_KEY`를 추가하면 AI 기반 정밀 검증을 사용할 수 있습니다.',
        'c_head':    '🎨 カラー設定',
        'c_cap':     '엑셀에서 색상을 지정했어도 여기서 덮어씌울 수 있어요.',
        'c_btn':     '🎫 チケットボタン色',
        'c_pt':      '✨ ポイントカラー',
        'c_extract': '🖼 ポスターから\n自動抽出',
        'c_poster':  'ポスターURLを\n入力すると自動抽出\nできます',
        'c_spin':    'ポスターから色を抽出中...',
        'c_fail':    '색 추출 실패. 포스터 URL이 직접 접근 가능한지 확인해 주세요.',
        's3':        'Step 3 · HTML 생성',
        'gen_btn':   '✦ HTML 생성하기',
        'preview':   '미리보기',
        'dl_html':   '↓ HTML 다운로드',
        'src':       'HTML 소스 (복사용)',
        'send_btn':  '📨 담당자에게 전송하기',
        'send_spin': '이메일 전송 중...',
        'send_ok':   '✅ chakang@ebay.com 으로 전송 완료!',
        'send_err':  '❌ 전송 실패: {}',
        'send_none': 'HTML을 먼저 생성해 주세요.',
        'no_smtp':   '⚠ Streamlit Cloud Secrets에 SMTP_USER / SMTP_PASS가 설정되지 않았습니다. 관리자에게 문의하세요.',
        'draft_save': '💾 초안 저장 (.json)',
        'draft_load': '📂 초안 불러오기 (.json)',
        'draft_ok':   '✅ 초안 로드 완료! (색상 포함)',
        'c_upload':      '🖼 포스터 이미지 업로드',
        'c_upload_desc': '이미지를 업로드하면 HTML 포스터로 삽입되고 포인트 컬러가 자동 추출됩니다.',
        'poster_uploaded': '✅ 포스터 업로드됨 — HTML에 포함돼요',
        'poster_remove': '🗑 포스터 제거',
        'prev_desktop':  '🖥 데스크탑',
        'prev_mobile':   '📱 모바일',
        'edit_mode_btn':  '✏️ 인라인 편집 모드',
        'edit_mode_hint': '미리보기의 텍스트를 클릭하면 그 자리에서 바로 수정할 수 있어요. 수정 후 "편집 완료" 버튼을 눌러 적용하세요.',
        'edit_applied':   '✅ 편집 내용이 적용됐어요. 아래에서 HTML을 다운로드하세요.',
        'edit_ok_btn':    '✅ 편집완료/다운로드',
        'edit_rs_btn':    '↩ 되돌리기',
        'edit_hint':      '✏️ 클릭하여 편집',
        'edit_dl_btn':    '📥 편집본 다운로드',
        'edit_dl_hint':   '위 툴바의 "편집완료/다운로드" 버튼을 먼저 눌러 저장하세요.',
    },
    'ja': {
        's1':        'Step 1 · Excelテンプレートのダウンロード',
        's1_cap':    'B列（内容）のみ入力してください。① 基本情報・デザイン ② 公演概要 ③ チケット一覧 ④ ラインアップ ⑤ NOTICEタブ ⑥ お問い合わせ',
        'type_label':   'チケット販売方式',
        'type_instant': '即時購入（先着順）',
        'type_lottery': '応募型（抽選）',
        's2':        'Step 2 · 作成したExcelをアップロード',
        'dl_tpl':    '↓ テンプレートをダウンロード (.xlsx)',
        'load_ok':   '読み込み完了',
        'load_err':  'ファイル読み込みエラー',
        'v_head':    '🔍 注意事項の自動チェック',
        'v_items':   '件',
        'v_suffix':  'の項目から重複・矛盾する文言を検出します。',
        'v_btn':     'チェックする',
        'v_spin':    'チェック中...',
        'v_hint':    '💡 Streamlit Cloud の Secrets に ANTHROPIC_API_KEY を追加するとAI精密チェックが利用できます。',
        'c_head':    '🎨 カラー設定',
        'c_cap':     'Excelで色を指定していてもここで上書きできます。',
        'c_btn':     '🎫 チケットボタン色',
        'c_pt':      '✨ ポイントカラー',
        'c_extract': '🖼 ポスターから\n自動抽出',
        'c_poster':  'ポスターURLを\n入力すると自動抽出\nできます',
        'c_spin':    'ポスターから色を抽出中...',
        'c_fail':    '色の抽出に失敗しました。ポスターURLに直接アクセスできるか確認してください。',
        's3':        'Step 3 · HTML生成',
        'gen_btn':   '✦ HTMLを生成する',
        'preview':   'プレビュー',
        'dl_html':   '↓ HTMLをダウンロード',
        'src':       'HTMLソース（コピー用）',
        'send_btn':  '📨 担当者に送る',
        'send_spin': 'メールを送信中...',
        'send_ok':   '✅ chakang@ebay.com に送信しました！',
        'send_err':  '❌ 送信失敗: {}',
        'send_none': 'HTMLを先に生成してください。',
        'no_smtp':   '⚠ Streamlit Cloud の Secrets に SMTP_USER / SMTP_PASS を設定してください。',
        'draft_save': '💾 ドラフトを保存 (.json)',
        'draft_load': '📂 ドラフトを読み込む (.json)',
        'draft_ok':   '✅ ドラフトを読み込みました！（色設定含む）',
        'c_upload':      '🖼 ポスター画像をアップロード',
        'c_upload_desc': 'アップロードするとHTMLのポスターに埋め込まれ、ポイントカラーが自動抽出されます。',
        'poster_uploaded': '✅ ポスターをアップロード済み — HTMLに埋め込まれます',
        'poster_remove': '🗑 ポスターを削除',
        'prev_desktop':  '🖥 デスクトップ',
        'prev_mobile':   '📱 モバイル',
        'edit_mode_btn':  '✏️ インライン編集モード',
        'edit_mode_hint': 'プレビュー内のテキストをクリックして直接編集できます。完了後「編集完了」ボタンをクリックしてください。',
        'edit_applied':   '✅ 編集内容が反映されました。HTMLをダウンロードしてください。',
        'edit_ok_btn':    '✅ 修正完了・ダウンロード',
        'edit_rs_btn':    '↩ 元に戻す',
        'edit_hint':      '✏️ クリックして編集',
        'edit_dl_btn':    '📥 編集版をダウンロード',
        'edit_dl_hint':   'ツールバーの「修正完了・ダウンロード」を先にクリックして保存してください。',
    },
}


def _send_html_by_email(html_content, title):
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.base import MIMEBase
    from email.mime.text import MIMEText
    from email import encoders as _enc

    try:
        smtp_host = st.secrets.get('SMTP_HOST', 'smtp.gmail.com')
        smtp_port = int(st.secrets.get('SMTP_PORT', '587'))
        smtp_user = st.secrets.get('SMTP_USER', '')
        smtp_pass = st.secrets.get('SMTP_PASS', '')
    except Exception:
        return False, 'no_smtp'

    if not smtp_user or not smtp_pass:
        return False, 'no_smtp'

    to_addr = 'chakang@ebay.com'
    msg = MIMEMultipart()
    msg['From']    = smtp_user
    msg['To']      = to_addr
    msg['Subject'] = f'[Qoo10] {title}'

    body = (f'Qoo10チケットページのHTMLファイルを送付します。\n件名：{title}\n\n'
            f'Qoo10 티켓 페이지 HTML 파일을 전송합니다.\n제목: {title}')
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    # utf-8-sig = UTF-8 BOM → Windows/Outlook에서 일본어 깨짐 방지
    html_bytes = html_content.encode('utf-8-sig')
    safe_title = re.sub(r'[<>:"/\\|?*\s]', '_', title)[:40]
    fname = f'ticket_{safe_title}.html'

    part = MIMEBase('application', 'octet-stream')
    part.set_payload(html_bytes)
    _enc.encode_base64(part)
    part.add_header('Content-Disposition', 'attachment', filename=('utf-8', '', fname))
    msg.attach(part)

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as srv:
            srv.ehlo()
            srv.starttls()
            srv.login(smtp_user, smtp_pass)
            srv.send_message(msg)
        return True, ''
    except Exception as exc:
        return False, str(exc)


# ── UI ────────────────────────────────────────────────────────────────────────
# 인터페이스 언어 선택 / 言語選択
if 'ui_lang' not in st.session_state:
    st.session_state['ui_lang'] = 'ko'
t = _UI_TEXT[st.session_state['ui_lang']]

_ul1, _ul2, _ = st.columns([1.2, 1.2, 5])
with _ul1:
    if st.button(
        '🇰🇷 한국어',
        use_container_width=True,
        type='primary' if st.session_state['ui_lang'] == 'ko' else 'secondary',
        key='uilang_ko',
    ):
        st.session_state['ui_lang'] = 'ko'
        st.rerun()
with _ul2:
    if st.button(
        '🇯🇵 日本語',
        use_container_width=True,
        type='primary' if st.session_state['ui_lang'] == 'ja' else 'secondary',
        key='uilang_ja',
    ):
        st.session_state['ui_lang'] = 'ja'
        st.rerun()

st.divider()

col_l, col_r = st.columns(2)
with col_l:
    st.markdown(f"#### {t['s1']}")
    st.caption(t['s1_cap'])
    _type_sel = st.radio(
        t['type_label'],
        [t['type_instant'], t['type_lottery']],
        horizontal=True,
        key='ticket_type_sel',
    )
    _is_lottery_tpl = _type_sel == t['type_lottery']
    st.download_button(
        t['dl_tpl'],
        _make_template(lottery=_is_lottery_tpl),
        "ticket_template.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
with col_r:
    st.markdown(f"#### {t['s2']}")
    uploaded_tpl   = st.file_uploader("", type=["xlsx", "xls"], label_visibility="collapsed", key="tpl_upload")
    uploaded_draft = st.file_uploader(t['draft_load'], type=["json"], key="draft_upload")

tpl_data = {}
if uploaded_tpl:
    try:
        df_raw = pd.read_excel(uploaded_tpl, header=None, sheet_name=0, dtype=str)
        for _, row in df_raw.iterrows():
            key = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) and str(row.iloc[0]) != 'nan' else ''
            val = str(row.iloc[1]).strip() if len(row) > 1 and pd.notna(row.iloc[1]) and str(row.iloc[1]) != 'nan' else ''
            if key and key != '항목' and not key.startswith('【') and not key.startswith('──'):
                tpl_data[key] = val
        st.success(f"✅ {uploaded_tpl.name} {t['load_ok']} ({len(tpl_data)}{t['v_items']})")
        st.session_state.pop('draft_data', None)
    except Exception as e:
        st.error(f"{t['load_err']}: {e}")

if not tpl_data and uploaded_draft:
    try:
        import json as _json
        _draft = _json.loads(uploaded_draft.read().decode('utf-8'))
        st.session_state['draft_data'] = _draft
        tpl_data = _draft
        st.info(t['draft_ok'])
    except Exception as e:
        st.error(f"Draft load error: {e}")

if not tpl_data and st.session_state.get('draft_data'):
    tpl_data = st.session_state['draft_data']
    st.info(t['draft_ok'])

if tpl_data:
    notices = _collect_notices(tpl_data)
    if notices:
        st.markdown(f"#### {t['v_head']}")
        st.caption(f"**{len(notices)}{t['v_items']}** {t['v_suffix']}")
        if st.button(t['v_btn'], type="secondary", key="validate_btn"):
            with st.spinner(t['v_spin']):
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
                st.caption(t['v_hint'])

    st.markdown("---")
    st.markdown(f"#### {t['c_head']}")
    st.caption(t['c_cap'])

    _excel_btn = tpl_data.get('チケットボタン色', '') or '#8da0a7'
    _excel_pt  = tpl_data.get('ポイントカラー', '') or _excel_btn
    _fbase     = uploaded_tpl.name.replace('.', '_') if uploaded_tpl else 'draft'
    _cnt_key   = f'cp_cnt_{_fbase}'
    if _cnt_key not in st.session_state:
        st.session_state[_cnt_key] = 0
    _fkey_btn  = f'cp_btn_{_fbase}_{st.session_state[_cnt_key]}'
    _fkey_pt   = f'cp_pt_{_fbase}_{st.session_state[_cnt_key]}'
    if _fkey_btn not in st.session_state:
        st.session_state[_fkey_btn] = _excel_btn
    if _fkey_pt not in st.session_state:
        st.session_state[_fkey_pt] = _excel_pt

    _pc1, _pc2 = st.columns(2)
    with _pc1:
        picked_btn = st.color_picker(t['c_btn'], key=_fkey_btn)
    with _pc2:
        picked_pt = st.color_picker(t['c_pt'], key=_fkey_pt)

    _ex1, _ex2 = st.columns(2)
    with _ex1:
        _poster_for_auto = tpl_data.get('ポスターURL', '')
        if _poster_for_auto:
            if st.button(t['c_extract'], use_container_width=True, key=f"auto_color_btn_{st.session_state[_cnt_key]}"):
                with st.spinner(t['c_spin']):
                    _pal = _extract_poster_palette(_poster_for_auto)
                if _pal:
                    st.session_state[_cnt_key] += 1
                    _new_btn = f'cp_btn_{_fbase}_{st.session_state[_cnt_key]}'
                    _new_pt  = f'cp_pt_{_fbase}_{st.session_state[_cnt_key]}'
                    st.session_state[_new_btn] = _pal[0]
                    st.session_state[_new_pt]  = _pal[0]
                    st.rerun()
                else:
                    st.warning(t['c_fail'])
        else:
            st.caption(t['c_poster'])
    with _ex2:
        st.caption(t['c_upload_desc'])
        _poster_key = f'poster_bytes_{_fbase}'
        _img_file = st.file_uploader(
            t['c_upload'],
            type=['jpg', 'jpeg', 'png', 'webp'],
            key=f"poster_img_{_fbase}_{st.session_state[_cnt_key]}",
        )
        if _img_file:
            _img_bytes = _img_file.read()
            with st.spinner(t['c_spin']):
                _pal = _extract_palette_from_bytes(_img_bytes)
            st.session_state[_poster_key] = (_img_bytes, _img_file.type or 'image/jpeg')
            if _pal:
                st.session_state[_cnt_key] += 1
                _new_btn = f'cp_btn_{_fbase}_{st.session_state[_cnt_key]}'
                _new_pt  = f'cp_pt_{_fbase}_{st.session_state[_cnt_key]}'
                st.session_state[_new_btn] = _pal[0]
                st.session_state[_new_pt]  = _pal[0]
                st.rerun()
            else:
                st.warning(t['c_fail'])
        if st.session_state.get(_poster_key):
            st.success(t['poster_uploaded'])
            if st.button(t['poster_remove'], key=f'poster_rm_{_fbase}', use_container_width=True):
                del st.session_state[_poster_key]
                st.rerun()

    st.markdown("---")
    st.markdown(f"#### {t['s3']}")
    if st.button(t['gen_btn'], type="primary", use_container_width=True):
        _merged = dict(tpl_data)
        _merged['チケットボタン色'] = picked_btn
        _merged['ポイントカラー']   = picked_pt
        _poster_key = f'poster_bytes_{_fbase}'
        if st.session_state.get(_poster_key):
            import base64 as _b64mod
            _pb, _pmime = st.session_state[_poster_key]
            _b64str = _b64mod.b64encode(_pb).decode('ascii')
            _merged['ポスターURL'] = f'data:{_pmime};base64,{_b64str}'
        result_html, errs = _generate_html(_merged, _merged, _TICKET_CSS, 'ja')
        if errs:
            for err in errs:
                st.error(f"⚠ {err}")
        else:
            st.session_state['ticket_gen_html'] = result_html
            st.session_state['ticket_gen_bg']   = _merged.get('背景色', '') or '#191919'
            st.session_state['ticket_gen_data'] = _merged

if st.session_state.get('ticket_gen_html'):
    gen_html  = st.session_state['ticket_gen_html']
    orig_data = st.session_state.get('ticket_gen_data', {})

    st.divider()
    st.markdown(f"#### {t['preview']}")

    _edit_mode = st.toggle(t['edit_mode_btn'], key='inline_edit_mode', value=False)

    _prev_mode = st.radio(
        "preview_mode_label",
        [t['prev_desktop'], t['prev_mobile']],
        horizontal=True,
        label_visibility="collapsed",
        key="preview_mode",
    )

    _render_html = _inject_editable(gen_html, t['edit_ok_btn'], t['edit_rs_btn'], t['edit_hint']) if _edit_mode else _block_links(gen_html)

    import html as _html
    if _prev_mode == t['prev_mobile']:
        _esc = _html.escape(_render_html, quote=True)
        _phone_tpl = (
            '<!DOCTYPE html><html><head><meta charset="UTF-8"><style>'
            '* { box-sizing: border-box; margin: 0; padding: 0; }'
            'body { background: #111; display: flex; justify-content: center; padding: 20px 0 28px; }'
            '.phone { width: 375px; border-radius: 48px; border: 10px solid #2c2c2e;'
            ' box-shadow: 0 0 0 1px #444, 0 24px 64px rgba(0,0,0,.7); overflow: hidden; background: #000; }'
            '.phone-top { background: #1c1c1e; height: 40px; position: relative; }'
            '.pill { width: 120px; height: 34px; background: #000; border-radius: 0 0 22px 22px;'
            ' position: absolute; top: 0; left: 50%; transform: translateX(-50%); }'
            '.cam { width: 10px; height: 10px; background: #1c2333; border-radius: 50%;'
            ' position: absolute; top: 13px; left: calc(50% + 28px); transform: translateX(-50%);'
            ' box-shadow: 0 0 0 2px #2a2a2e; }'
            '.screen { width: 100%; height: 750px; border: none; display: block; }'
            '.phone-bottom { background: #1c1c1e; height: 32px; display: flex; align-items: center; justify-content: center; }'
            '.bar { width: 134px; height: 5px; background: #555; border-radius: 3px; }'
            '</style></head><body><div class="phone">'
            '<div class="phone-top"><div class="pill"></div><div class="cam"></div></div>'
            '<iframe class="screen" srcdoc="SRCDOC_PLACEHOLDER" scrolling="yes"></iframe>'
            '<div class="phone-bottom"><div class="bar"></div></div>'
            '</div></body></html>'
        )
        components_v1.html(_phone_tpl.replace('SRCDOC_PLACEHOLDER', _esc), height=870, scrolling=False)
    else:
        _h = 900 if _edit_mode else 720
        components_v1.html(_render_html, height=_h, scrolling=True)
    st.divider()

    col_d, col_e, col_f = st.columns(3)
    with col_d:
        st.download_button(
            t['dl_html'],
            gen_html.encode('utf-8'),
            "ticket_page.html",
            "text/html;charset=utf-8",
            use_container_width=True,
        )
        if _edit_mode:
            if st.button(t['edit_dl_btn'], use_container_width=True, type='primary', key='btn_dl_edited'):
                st.session_state['edit_dl_count'] = st.session_state.get('edit_dl_count', 0) + 1
                st.session_state['awaiting_edited'] = True
            st.caption(t['edit_dl_hint'])
    with col_e:
        import urllib.parse as _up
        _title = (orig_data.get('公演タイトル', '')
                  or orig_data.get('タイトル', '')
                  or 'Ticket Page').replace('\\n', ' ')
        _subject = _up.quote(f'[Qoo10] {_title}')
        _body = _up.quote('HTML을 다운로드받으셔서 첨부 하시고 메일을 보내주세요.\nHTMLをダウンロードして添付の上、メールをお送りください。')
        _mailto = f"mailto:chakang@ebay.com?subject={_subject}&body={_body}"
        st.link_button(t['send_btn'], url=_mailto, use_container_width=True, type="secondary")
        st.caption("※ HTML을 다운받아 메일에 첨부해 주세요" if st.session_state.get('ui_lang') == 'ko' else "※ HTMLをダウンロードしてメールに添付してください")
    with col_f:
        import json as _json
        _draft_bytes = _json.dumps(orig_data, ensure_ascii=False, indent=2).encode('utf-8')
        st.download_button(
            t['draft_save'],
            _draft_bytes,
            "ticket_draft.json",
            "application/json",
            use_container_width=True,
        )

    if _edit_mode and st.session_state.get('awaiting_edited'):
        try:
            from streamlit_js_eval import streamlit_js_eval as _jseval
            _fetch_key = f"edited_html_{st.session_state.get('edit_dl_count', 0)}"
            _edited_val = _jseval(js_expressions='localStorage.getItem("ticket_edited_html")', key=_fetch_key)
            if _edited_val is not None:
                if _edited_val:
                    st.session_state['edited_html_ready'] = _edited_val
                else:
                    st.warning('⚠️ 편집완료 버튼을 먼저 눌러주세요.' if st.session_state.get('ui_lang') == 'ko' else '⚠️ まず編集完了ボタンを押してください。')
                st.session_state['awaiting_edited'] = False
        except Exception:
            st.error('streamlit-js-eval 패키지 오류. 잠시 후 다시 시도해 주세요.')
            st.session_state['awaiting_edited'] = False

    if _edit_mode and st.session_state.get('edited_html_ready'):
        st.download_button(
            '📥 편집본 다운로드 (클릭!)' if st.session_state.get('ui_lang') == 'ko' else '📥 編集版ダウンロード（クリック！）',
            st.session_state['edited_html_ready'].encode('utf-8'),
            'ticket_edited.html',
            'text/html;charset=utf-8',
            use_container_width=True,
            key='dl_edited_final',
            type='primary',
        )
        st.session_state['edited_html_ready'] = None

    st.text_area(t['src'], gen_html, height=200, key="gen_src")
