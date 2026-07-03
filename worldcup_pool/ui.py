from __future__ import annotations

import base64
import re
import unicodedata
import zipfile
from pathlib import Path

import streamlit as st


ROOT = Path(__file__).resolve().parent
FLAGS_DIR = ROOT / "scripts" / "assets" / "flags"

FLAG_ALIASES = {
    "alemania": "alemania",
    "arabia saudita": "arabia_saudita",
    "argelia": "argelia",
    "argentina": "argentina",
    "australia": "australia",
    "austria": "austria",
    "belgica": "belgica",
    "bosnia y herzegovina": "bosnia",
    "brasil": "brasil",
    "cabo verde": "cabo_verde",
    "canada": "canada",
    "chequia": "chequia",
    "chile": "chile",
    "republica checa": "chequia",
    "colombia": "colombia",
    "corea del sur": "corea_sur",
    "costa de marfil": "costa_marfil",
    "croacia": "croacia",
    "curazao": "curazao",
    "ecuador": "ecuador",
    "egipto": "egipto",
    "escocia": "escocia",
    "espana": "espana",
    "estados unidos": "estados_unidos",
    "francia": "francia",
    "ghana": "ghana",
    "haiti": "haiti",
    "inglaterra": "inglaterra",
    "irak": "irak",
    "iran": "iran",
    "japon": "japon",
    "jordania": "jordania",
    "marruecos": "marruecos",
    "mexico": "mexico",
    "noruega": "noruega",
    "nueva zelanda": "nueva_zelanda",
    "paises bajos": "paises_bajos",
    "panama": "panama",
    "paraguay": "paraguay",
    "portugal": "portugal",
    "qatar": "qatar",
    "congo": "rd_congo",
    "rd congo": "rd_congo",
    "rd de congo": "rd_congo",
    "dr congo": "rd_congo",
    "democratic republic of congo": "rd_congo",
    "republica del congo": "rd_congo",
    "republica democratica del congo": "rd_congo",
    "scotland": "escocia",
    "senegal": "senegal",
    "sudafrica": "sudafrica",
    "suecia": "suecia",
    "sweden": "suecia",
    "suiza": "suiza",
    "tunez": "tunez",
    "turquia": "turquia",
    "uruguay": "uruguay",
    "uzbekistan": "uzbekistan",
}


def normalize_name(value: str) -> str:
    text = unicodedata.normalize("NFKD", value or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower().strip()
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


@st.cache_data(show_spinner=False)
def flag_data_uri(team: str) -> str | None:
    key = FLAG_ALIASES.get(normalize_name(team))
    if not key:
        return None
    path = FLAGS_DIR / f"{key}.png"
    if not path.exists() and (FLAGS_DIR.parent / "flags.zip").exists():
        with zipfile.ZipFile(FLAGS_DIR.parent / "flags.zip") as archive:
            archive.extractall(FLAGS_DIR.parent)
    if not path.exists():
        return None
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{data}"


def inject_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
            --wc-bg: #050a19;
            --wc-panel: rgba(7, 20, 48, 0.82);
            --wc-panel-2: rgba(8, 27, 67, 0.72);
            --wc-line: rgba(84, 144, 255, 0.28);
            --wc-green: #39f27b;
            --wc-text: #f8fbff;
            --wc-muted: #a9b7d4;
        }
        .stApp {
            color: var(--wc-text);
            background:
                radial-gradient(circle at 75% 0%, rgba(17, 85, 185, 0.32), transparent 34rem),
                radial-gradient(circle at 5% 35%, rgba(34, 242, 123, 0.12), transparent 30rem),
                linear-gradient(135deg, #030612 0%, #07183a 48%, #020611 100%);
        }
        .main .block-container {
            max-width: 1440px;
            padding-top: 1.4rem;
        }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, rgba(3, 8, 25, 0.97), rgba(5, 17, 42, 0.94));
            border-right: 1px solid rgba(84, 144, 255, 0.22);
        }
        [data-testid="stSidebar"] * {
            color: var(--wc-text);
        }
        [data-testid="stSidebar"] input,
        [data-testid="stSidebar"] textarea,
        [data-testid="stSidebar"] input *,
        [data-testid="stSidebar"] textarea * {
            color: #0f172a !important;
            caret-color: #0f172a !important;
        }
        [data-testid="stSidebar"] input::placeholder,
        [data-testid="stSidebar"] textarea::placeholder {
            color: #64748b !important;
            opacity: 1;
        }
        [data-testid="stTextInput"] label,
        [data-testid="stNumberInput"] label,
        [data-testid="stSelectbox"] label,
        [data-testid="stTextArea"] label,
        [data-testid="stDateInput"] label,
        [data-testid="stTimeInput"] label,
        [data-testid="stTextInput"] label *,
        [data-testid="stNumberInput"] label *,
        [data-testid="stSelectbox"] label *,
        [data-testid="stTextArea"] label *,
        [data-testid="stDateInput"] label *,
        [data-testid="stTimeInput"] label * {
            color: #e5edff !important;
            font-weight: 800 !important;
        }
        [data-testid="stTextInput"] input,
        [data-testid="stNumberInput"] input,
        [data-testid="stTextArea"] textarea,
        [data-testid="stDateInput"] input,
        [data-testid="stTimeInput"] input,
        [data-testid="stSelectbox"] div[data-baseweb="select"] > div {
            background: #f8fafc !important;
            color: #0f172a !important;
            border-color: rgba(148, 163, 184, 0.65) !important;
        }
        [data-testid="stTextInput"] input::placeholder,
        [data-testid="stTextArea"] textarea::placeholder {
            color: #64748b !important;
            opacity: 1;
        }
        [data-testid="stSelectbox"] div[data-baseweb="select"] *,
        [data-baseweb="popover"] li,
        [data-baseweb="popover"] li * {
            color: #0f172a !important;
        }
        [data-testid="stSidebar"] button:disabled,
        [data-testid="stSidebar"] button:disabled * {
            color: #64748b !important;
        }
        .stButton > button,
        .stDownloadButton > button,
        button[kind],
        button[data-testid="baseButton-secondary"],
        button[data-testid="baseButton-primary"] {
            background: linear-gradient(180deg, #10264f 0%, #071733 100%) !important;
            color: #ffffff !important;
            border: 1px solid rgba(84, 144, 255, 0.55) !important;
            border-radius: 8px !important;
            box-shadow: 0 10px 22px rgba(0, 0, 0, 0.22) !important;
            font-weight: 800 !important;
        }
        .stButton > button *,
        .stDownloadButton > button *,
        button[kind] *,
        button[data-testid="baseButton-secondary"] *,
        button[data-testid="baseButton-primary"] * {
            color: #ffffff !important;
        }
        .stButton > button:hover,
        .stDownloadButton > button:hover,
        button[kind]:hover,
        button[data-testid="baseButton-secondary"]:hover,
        button[data-testid="baseButton-primary"]:hover {
            background: linear-gradient(180deg, #17366e 0%, #0b1e42 100%) !important;
            border-color: rgba(57, 242, 123, 0.8) !important;
            color: #ffffff !important;
        }
        .stButton > button:disabled,
        .stDownloadButton > button:disabled,
        button[kind]:disabled,
        button[data-testid="baseButton-secondary"]:disabled,
        button[data-testid="baseButton-primary"]:disabled {
            background: #1e293b !important;
            color: #cbd5e1 !important;
            border-color: rgba(148, 163, 184, 0.35) !important;
            opacity: 0.78 !important;
            box-shadow: none !important;
        }
        .stButton > button:disabled *,
        .stDownloadButton > button:disabled *,
        button[kind]:disabled *,
        button[data-testid="baseButton-secondary"]:disabled *,
        button[data-testid="baseButton-primary"]:disabled * {
            color: #cbd5e1 !important;
        }
        [data-testid="stRadio"] label,
        [data-testid="stRadio"] label *,
        [data-testid="stRadio"] p,
        [data-testid="stRadio"] span {
            color: #e5edff !important;
        }
        [data-testid="stRadio"] [role="radiogroup"] {
            gap: 18px;
        }
        [data-testid="stRadio"] [role="radio"] {
            background: rgba(7, 20, 48, 0.62);
            border: 1px solid rgba(84, 144, 255, 0.32);
            border-radius: 999px;
            padding: 6px 10px;
        }
        [data-testid="stRadio"] [role="radio"][aria-checked="true"] {
            border-color: rgba(57, 242, 123, 0.85);
            background: rgba(57, 242, 123, 0.14);
        }
        [data-testid="stRadio"] [role="radio"][aria-checked="true"] * {
            color: #ffffff !important;
            font-weight: 800;
        }
        .wc-shell {
            border: 1px solid var(--wc-line);
            border-radius: 22px;
            padding: 24px;
            background: linear-gradient(145deg, rgba(4, 14, 39, 0.94), rgba(8, 28, 72, 0.72));
            box-shadow: 0 24px 60px rgba(0, 0, 0, 0.34);
        }
        .wc-kicker {
            color: var(--wc-green);
            font-size: 0.82rem;
            letter-spacing: 0.16rem;
            text-transform: uppercase;
            font-weight: 800;
        }
        .wc-hero {
            min-height: 440px;
            border: 1px solid rgba(116, 160, 255, 0.48);
            border-radius: 22px;
            overflow: hidden;
            padding: 28px;
            background:
                linear-gradient(180deg, rgba(2, 10, 30, 0.22), rgba(2, 10, 22, 0.72)),
                radial-gradient(circle at 50% 18%, rgba(91, 131, 255, 0.4), transparent 22rem),
                linear-gradient(180deg, #0c2f83 0%, #051737 56%, #06230f 100%);
            position: relative;
        }
        .wc-hero:after {
            content: "";
            position: absolute;
            inset: auto 0 0;
            height: 36%;
            background:
                repeating-linear-gradient(90deg, rgba(117, 186, 102, 0.18) 0 2px, transparent 2px 76px),
                linear-gradient(180deg, rgba(20, 115, 55, 0.15), rgba(30, 126, 54, 0.58));
        }
        .wc-match {
            position: relative;
            z-index: 1;
            display: grid;
            grid-template-columns: 1fr auto 1fr;
            gap: 30px;
            align-items: center;
            min-height: 280px;
        }
        .wc-team {
            text-align: center;
            min-width: 0;
        }
        .wc-team img {
            width: min(290px, 100%);
            aspect-ratio: 4 / 2.45;
            object-fit: cover;
            border-radius: 20px;
            border: 1px solid rgba(255, 255, 255, 0.78);
            box-shadow: 0 14px 32px rgba(0, 0, 0, 0.35);
        }
        .wc-team-name {
            margin-top: 16px;
            font-size: clamp(1.35rem, 3vw, 2.4rem);
            line-height: 1.05;
            font-weight: 900;
            text-transform: uppercase;
        }
        .wc-vs {
            font-size: clamp(2.8rem, 7vw, 5rem);
            font-weight: 950;
            text-shadow: 0 6px 22px rgba(0, 0, 0, 0.4);
        }
        .wc-meta {
            position: relative;
            z-index: 1;
            display: flex;
            gap: 18px;
            justify-content: center;
            flex-wrap: wrap;
            margin-top: 6px;
            color: #ffffff;
            font-weight: 700;
        }
        .wc-card {
            border: 1px solid var(--wc-line);
            border-radius: 10px;
            padding: 18px;
            background: var(--wc-panel);
        }
        .wc-phase-title {
            margin: 28px 0 14px;
            padding: 12px 16px;
            border-left: 4px solid var(--wc-green);
            border-top: 1px solid rgba(84, 144, 255, 0.32);
            border-bottom: 1px solid rgba(84, 144, 255, 0.32);
            color: #ffffff;
            font-size: clamp(1.1rem, 2.2vw, 1.7rem);
            font-weight: 950;
            letter-spacing: 0.08rem;
            text-transform: uppercase;
            background: linear-gradient(90deg, rgba(9, 28, 70, 0.92), rgba(9, 28, 70, 0.18));
        }
        .wc-stat {
            font-size: 2rem;
            line-height: 1;
            font-weight: 900;
        }
        .wc-muted {
            color: var(--wc-muted);
        }
        .wc-list-row {
            display: grid;
            grid-template-columns: auto 1fr auto;
            gap: 12px;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid rgba(130, 170, 255, 0.16);
        }
        .wc-list-row:last-child {
            border-bottom: 0;
        }
        .wc-list-row img {
            width: 36px;
            height: 24px;
            object-fit: cover;
            border-radius: 3px;
        }
        div[data-testid="stMetric"] {
            background: var(--wc-panel);
            border: 1px solid var(--wc-line);
            border-radius: 10px;
            padding: 16px;
        }
        div[data-testid="stDataFrame"] {
            border: 1px solid var(--wc-line);
            border-radius: 10px;
            overflow: hidden;
        }
        div[data-testid="stDataFrame"] * {
            color: #0f172a !important;
        }
        div[data-testid="stDataFrame"] [role="columnheader"],
        div[data-testid="stDataFrame"] [role="columnheader"] * {
            color: #334155 !important;
            font-weight: 800 !important;
        }
        div[data-testid="stDataFrame"] [role="gridcell"],
        div[data-testid="stDataFrame"] [role="gridcell"] * {
            color: #071225 !important;
            font-weight: 600 !important;
        }
        @media (max-width: 800px) {
            .wc-match {
                grid-template-columns: 1fr;
                gap: 18px;
            }
            .wc-vs {
                font-size: 2.4rem;
            }
            .wc-hero {
                padding: 18px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def flag_img(team: str) -> str:
    src = flag_data_uri(team)
    if src:
        return f'<img src="{src}" alt="{team}">'
    return '<div style="height:160px;border-radius:20px;border:1px solid rgba(255,255,255,.45);display:grid;place-items:center;background:rgba(255,255,255,.08);font-weight:900;">FIFA</div>'
