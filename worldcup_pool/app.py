from datetime import datetime

import streamlit as st
from sqlalchemy import func, select

from database import (
    SessionLocal,
    buscar_usuario_por_nombre,
    crear_usuario,
    init_db,
    normalizar_nombre_participante,
    ranking_dataframe,
    utc_to_chile,
)
from models import Partido, Usuario
from ui import flag_data_uri, flag_img, inject_theme


st.set_page_config(page_title="Mundial 2026", page_icon="⚽", layout="wide")
inject_theme()
init_db()

with st.sidebar:
    st.markdown("## FIFA WORLD CUP 2026")
    st.caption("Canadá · México · Estados Unidos")
    st.divider()
    st.header("Ingreso")

    if "usuario_id" in st.session_state:
        st.success(f"Sesión activa: {st.session_state.get('nombre', '')}")
        st.caption("Tu nombre ya quedó confirmado para esta sesión.")
    else:
        nombre = st.text_input("Tu nombre", value=st.session_state.get("nombre_input", ""), max_chars=80)

        if st.button("Continuar", use_container_width=True) and nombre.strip():
            try:
                nombre_normalizado = normalizar_nombre_participante(nombre)
                if buscar_usuario_por_nombre(nombre_normalizado):
                    st.session_state.pop("nombre_pendiente", None)
                    st.error("Ese nombre ya está registrado. Para evitar duplicados, elige otro nombre.")
                else:
                    st.session_state["nombre_pendiente"] = nombre_normalizado
            except Exception as exc:
                st.error(str(exc))

        if st.session_state.get("nombre_pendiente"):
            nombre_pendiente = st.session_state["nombre_pendiente"]
            st.warning(f"¿Estás seguro de que tu nombre será '{nombre_pendiente}'?")
            st.caption("Después de confirmarlo no podrás volver a registrar ese mismo nombre.")
            col_confirm, col_cancel = st.columns(2)
            if col_confirm.button("Sí, confirmar", use_container_width=True):
                try:
                    user = crear_usuario(nombre_pendiente)
                    st.session_state["usuario_id"] = user.id
                    st.session_state["nombre"] = user.nombre
                    st.session_state.pop("nombre_pendiente", None)
                    st.success(f"Participante registrado: {user.nombre}")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
            if col_cancel.button("Cambiar", use_container_width=True):
                st.session_state.pop("nombre_pendiente", None)
                st.rerun()

    st.caption("Comparte el link público de Streamlit para que otros participantes entren con su nombre.")

with SessionLocal() as db:
    total_participantes = db.scalar(select(func.count(Usuario.id))) or 0
    total_partidos = db.scalar(select(func.count(Partido.id))) or 0
    jugados = db.scalar(select(func.count(Partido.id)).where(Partido.resultado_oficial_cargado == True)) or 0
    pendientes = total_partidos - jugados
    proximo = db.scalars(
        select(Partido).where(Partido.fecha_hora_utc > datetime.utcnow()).order_by(Partido.fecha_hora_utc).limit(1)
    ).first()
    siguientes = db.scalars(
        select(Partido).where(Partido.fecha_hora_utc > datetime.utcnow()).order_by(Partido.fecha_hora_utc).limit(4)
    ).all()

ranking = ranking_dataframe()
lider = ranking.iloc[0]["Participante"] if not ranking.empty else "-"

st.markdown('<div class="wc-shell">', unsafe_allow_html=True)
top_left, top_right = st.columns([1, 1])
with top_left:
    st.markdown('<div class="wc-kicker">Quiniela Mundial</div>', unsafe_allow_html=True)
    st.title("FIFA World Cup 2026")
with top_right:
    if proximo:
        hora_chile = utc_to_chile(proximo.fecha_hora_utc)
        st.markdown(
            f'<div style="text-align:right;font-size:1.2rem;font-weight:800;">{hora_chile:%a %d %b, %Y · %H:%M} Chile</div>',
            unsafe_allow_html=True,
        )

if proximo:
    hora_chile = utc_to_chile(proximo.fecha_hora_utc)
    st.markdown(
        f"""
        <div class="wc-hero">
            <div class="wc-kicker">{proximo.fase}</div>
            <div class="wc-match">
                <div class="wc-team">
                    {flag_img(proximo.equipo_local)}
                    <div class="wc-team-name">{proximo.equipo_local}</div>
                </div>
                <div class="wc-vs">VS</div>
                <div class="wc-team">
                    {flag_img(proximo.equipo_visita)}
                    <div class="wc-team-name">{proximo.equipo_visita}</div>
                </div>
            </div>
            <div class="wc-meta">
                <span>{hora_chile:%d %b %Y}</span>
                <span>{hora_chile:%H:%M} Chile</span>
                <span>Pronósticos cierran al inicio</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.info("No hay partidos futuros cargados.")

st.markdown("</div>", unsafe_allow_html=True)

st.write("")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Participantes", total_participantes)
c2.metric("Partidos", total_partidos)
c3.metric("Jugados", jugados)
c4.metric("Pendientes", pendientes)
c5.metric("Líder", lider)

left, middle, right = st.columns([1.1, 1.1, 1])
with left:
    st.markdown('<div class="wc-card">', unsafe_allow_html=True)
    st.markdown('<div class="wc-kicker">Ranking General</div>', unsafe_allow_html=True)
    if ranking.empty:
        st.info("Aún no hay participantes o puntajes.")
    else:
        st.dataframe(ranking.head(8), hide_index=True, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with middle:
    st.markdown('<div class="wc-card">', unsafe_allow_html=True)
    st.markdown('<div class="wc-kicker">Próximos Partidos</div>', unsafe_allow_html=True)
    if not siguientes:
        st.caption("Sin partidos próximos.")
    for partido in siguientes:
        hora = utc_to_chile(partido.fecha_hora_utc)
        local_flag = flag_data_uri(partido.equipo_local)
        visita_flag = flag_data_uri(partido.equipo_visita)
        local_img = f'<img src="{local_flag}" alt="{partido.equipo_local}">' if local_flag else ""
        visita_img = f'<img src="{visita_flag}" alt="{partido.equipo_visita}">' if visita_flag else ""
        st.markdown(
            f"""
            <div class="wc-list-row">
                <div>{local_img}</div>
                <div><b>{partido.equipo_local}</b> vs <b>{partido.equipo_visita}</b><br><span class="wc-muted">{partido.fase}</span></div>
                <div style="text-align:right;">{visita_img}<br><b>{hora:%d %b}</b><br><span class="wc-muted">{hora:%H:%M}</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown(
        """
        <div class="wc-card">
            <div class="wc-kicker">Bonus</div>
            <div class="wc-stat">+12</div>
            <p class="wc-muted">Campeón +5 · Subcampeón +3 · Tercer lugar +1 · Goleador +3</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

if "usuario_id" not in st.session_state:
    st.info("Ingresa tu nombre en la barra lateral, confirma que está bien escrito y luego abre la página Pronósticos.")
