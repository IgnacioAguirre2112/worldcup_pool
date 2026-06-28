from datetime import datetime

import streamlit as st
from sqlalchemy import select

from database import SessionLocal, bonus_bloqueado, equipos_disponibles, guardar_pronostico, utc_to_chile
from models import Partido, Pronostico, PronosticoBonus
from ui import flag_img, inject_theme


st.set_page_config(page_title="Pronósticos", page_icon="📝", layout="wide")
inject_theme()
st.title("Pronósticos")

usuario_id = st.session_state.get("usuario_id")
if not usuario_id:
    st.warning("Primero ingresa tu nombre en la página principal.")
    st.stop()

with SessionLocal() as db:
    partidos = db.scalars(select(Partido).order_by(Partido.fecha_hora_utc)).all()
    pronosticos_existentes = {
        p.partido_id: p
        for p in db.scalars(select(Pronostico).where(Pronostico.usuario_id == usuario_id)).all()
    }
    bonus = db.get(PronosticoBonus, usuario_id)

if not partidos:
    st.info("Aún no hay fixture cargado.")
    st.stop()

st.caption("Puedes editar cada pronóstico hasta la hora de inicio del partido.")

for partido in partidos:
    cerrado = datetime.utcnow() >= partido.fecha_hora_utc
    hora_chile = utc_to_chile(partido.fecha_hora_utc)
    with st.container(border=True):
        top, form = st.columns([1.5, 1])
        with top:
            st.markdown(
                f"""
                <div class="wc-match" style="min-height:190px;gap:18px;">
                    <div class="wc-team">
                        {flag_img(partido.equipo_local)}
                        <div class="wc-team-name" style="font-size:1.45rem;">{partido.equipo_local}</div>
                    </div>
                    <div class="wc-vs" style="font-size:2.4rem;">VS</div>
                    <div class="wc-team">
                        {flag_img(partido.equipo_visita)}
                        <div class="wc-team-name" style="font-size:1.45rem;">{partido.equipo_visita}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.caption(f"{partido.fase} · {hora_chile:%Y-%m-%d %H:%M} Chile")

        with form:
            existente = pronosticos_existentes.get(partido.id)
            gl = st.number_input(
                f"Goles {partido.equipo_local}",
                0,
                20,
                value=existente.goles_local_pronosticado if existente else 0,
                disabled=cerrado,
                key=f"gl_{partido.id}",
            )
            gv = st.number_input(
                f"Goles {partido.equipo_visita}",
                0,
                20,
                value=existente.goles_visita_pronosticado if existente else 0,
                disabled=cerrado,
                key=f"gv_{partido.id}",
            )
            if cerrado:
                st.warning("Pronóstico cerrado")
            elif st.button("Guardar pronóstico", key=f"save_{partido.id}", use_container_width=True):
                try:
                    guardar_pronostico(usuario_id, partido.id, int(gl), int(gv))
                    st.success("Pronóstico guardado")
                except Exception as exc:
                    st.error(str(exc))

st.divider()
st.subheader("Bonus")
st.caption("Campeón +5 · Subcampeón +3 · Tercer lugar +1 · Goleador +3")
st.caption("Disponible hasta el 29-06-2026 a las 00:00 hora Chile.")

equipos = [""] + equipos_disponibles()


def index_or_zero(options: list[str], value: str | None) -> int:
    return options.index(value) if value in options else 0


if bonus_bloqueado():
    st.warning("Pronósticos bonus cerrados")
    b1, b2, b3, b4 = st.columns(4)
    b1.metric("Campeón", bonus.campeon if bonus and bonus.campeon else "-")
    b2.metric("Subcampeón", bonus.subcampeon if bonus and bonus.subcampeon else "-")
    b3.metric("Tercer lugar", bonus.tercer_lugar if bonus and bonus.tercer_lugar else "-")
    b4.metric("Goleador", bonus.goleador if bonus and bonus.goleador else "-")
else:
    b1, b2, b3, b4 = st.columns(4)
    campeon = b1.selectbox("Campeón", equipos, index=index_or_zero(equipos, bonus.campeon if bonus else None))
    subcampeon = b2.selectbox("Subcampeón", equipos, index=index_or_zero(equipos, bonus.subcampeon if bonus else None))
    tercer = b3.selectbox("Tercer lugar", equipos, index=index_or_zero(equipos, bonus.tercer_lugar if bonus else None))
    goleador = b4.text_input("Goleador", value=bonus.goleador if bonus else "")
    if st.button("Guardar bonus", use_container_width=True):
        with SessionLocal() as db:
            saved = db.get(PronosticoBonus, usuario_id) or PronosticoBonus(usuario_id=usuario_id)
            saved.campeon = campeon or None
            saved.subcampeon = subcampeon or None
            saved.tercer_lugar = tercer or None
            saved.goleador = goleador.strip() or None
            db.merge(saved)
            db.commit()
        st.success("Bonus guardado")
