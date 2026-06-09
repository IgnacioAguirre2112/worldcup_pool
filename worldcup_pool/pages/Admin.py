from datetime import date, datetime, time
from io import BytesIO

import pandas as pd
import streamlit as st
from sqlalchemy import select

from database import FASES, SessionLocal, chile_to_utc_naive, equipos_disponibles, init_db, seed_fixture_from_csv, utc_to_chile
from models import Partido, Pronostico, PronosticoBonus, ResultadoBonus, Usuario
from ui import inject_theme


st.set_page_config(page_title="Admin", page_icon="🛠️", layout="wide")
inject_theme()
st.title("Panel Administrador")
init_db()

user = st.text_input("Usuario admin")
password = st.text_input("Password", type="password")
if user != st.secrets.get("ADMIN_USER", "admin") or password != st.secrets.get("ADMIN_PASSWORD", "password"):
    st.warning("Ingresa credenciales de administrador.")
    st.stop()

st.success("Acceso concedido")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Partidos", "Resultados", "Bonus oficiales", "Fixture", "Exportaciones"])

with tab1:
    st.subheader("Crear partido")
    col1, col2 = st.columns(2)
    fecha = col1.date_input("Fecha Chile", value=date(2026, 6, 11))
    hora = col2.time_input("Hora Chile", value=time(15, 0))
    fase = st.selectbox("Fase", FASES)
    local = st.text_input("Equipo local")
    visita = st.text_input("Equipo visita")
    if st.button("Crear partido") and local and visita:
        with SessionLocal() as db:
            db.add(
                Partido(
                    fecha_hora_utc=chile_to_utc_naive(fecha.isoformat(), hora.strftime("%H:%M")),
                    fase=fase,
                    equipo_local=local.strip(),
                    equipo_visita=visita.strip(),
                )
            )
            db.commit()
        st.success("Partido creado")

    with SessionLocal() as db:
        partidos = db.scalars(select(Partido).order_by(Partido.fecha_hora_utc)).all()
    for partido in partidos:
        hora_chile = utc_to_chile(partido.fecha_hora_utc)
        with st.expander(f"{partido.id} · {partido.equipo_local} vs {partido.equipo_visita} · {hora_chile:%Y-%m-%d %H:%M}"):
            st.caption("Edita este partido para reemplazar placeholders por equipos reales sin hacer reboot.")
            edit_col1, edit_col2 = st.columns(2)
            nueva_fecha = edit_col1.date_input("Fecha Chile", value=hora_chile.date(), key=f"fecha_{partido.id}")
            nueva_hora = edit_col2.time_input("Hora Chile", value=hora_chile.time(), key=f"hora_{partido.id}")
            nueva_fase = st.selectbox(
                "Fase",
                FASES,
                index=FASES.index(partido.fase) if partido.fase in FASES else 0,
                key=f"fase_{partido.id}",
            )
            nuevo_local = st.text_input("Equipo local", value=partido.equipo_local, key=f"local_{partido.id}")
            nuevo_visita = st.text_input("Equipo visita", value=partido.equipo_visita, key=f"visita_{partido.id}")

            save_col, delete_col = st.columns(2)
            if save_col.button("Guardar cambios", key=f"save_{partido.id}", use_container_width=True):
                if not nuevo_local.strip() or not nuevo_visita.strip():
                    st.error("El equipo local y visita no pueden estar vacíos.")
                else:
                    with SessionLocal() as db:
                        obj = db.get(Partido, partido.id)
                        obj.fecha_hora_utc = chile_to_utc_naive(nueva_fecha.isoformat(), nueva_hora.strftime("%H:%M"))
                        obj.fase = nueva_fase
                        obj.equipo_local = nuevo_local.strip()
                        obj.equipo_visita = nuevo_visita.strip()
                        db.commit()
                    st.success("Partido actualizado")
                    st.rerun()

            if delete_col.button("Eliminar", key=f"del_{partido.id}", use_container_width=True):
                with SessionLocal() as db:
                    obj = db.get(Partido, partido.id)
                    db.delete(obj)
                    db.commit()
                st.rerun()

with tab2:
    with SessionLocal() as db:
        partidos = db.scalars(select(Partido).order_by(Partido.fecha_hora_utc)).all()
    for partido in partidos:
        with st.container(border=True):
            hora_chile = utc_to_chile(partido.fecha_hora_utc)
            st.write(f"{partido.equipo_local} vs {partido.equipo_visita} · {hora_chile:%d-%m-%Y %H:%M} Chile")
            gl = st.number_input("Goles local", 0, 30, value=partido.goles_local or 0, key=f"rgl_{partido.id}")
            gv = st.number_input("Goles visita", 0, 30, value=partido.goles_visita or 0, key=f"rgv_{partido.id}")
            if st.button("Guardar resultado", key=f"res_{partido.id}"):
                with SessionLocal() as db:
                    obj = db.get(Partido, partido.id)
                    obj.goles_local = int(gl)
                    obj.goles_visita = int(gv)
                    obj.resultado_oficial_cargado = True
                    db.commit()
                st.success("Resultado cargado. El ranking se recalcula al consultar.")

with tab3:
    equipos = [""] + equipos_disponibles()
    with SessionLocal() as db:
        oficial = db.get(ResultadoBonus, 1)

    def index_or_zero(value: str | None) -> int:
        return equipos.index(value) if value in equipos else 0

    st.caption("Estos valores se comparan con los bonus de cada participante.")
    c1, c2, c3, c4 = st.columns(4)
    campeon = c1.selectbox("Campeón (+5)", equipos, index=index_or_zero(oficial.campeon if oficial else None))
    subcampeon = c2.selectbox("Subcampeón (+3)", equipos, index=index_or_zero(oficial.subcampeon if oficial else None))
    tercer = c3.selectbox("Tercer lugar (+1)", equipos, index=index_or_zero(oficial.tercer_lugar if oficial else None))
    goleador = c4.text_input("Goleador (+3)", value=oficial.goleador if oficial and oficial.goleador else "")
    if st.button("Guardar bonus oficiales", use_container_width=True):
        with SessionLocal() as db:
            saved = db.get(ResultadoBonus, 1) or ResultadoBonus(id=1)
            saved.campeon = campeon or None
            saved.subcampeon = subcampeon or None
            saved.tercer_lugar = tercer or None
            saved.goleador = goleador.strip() or None
            db.merge(saved)
            db.commit()
        st.success("Bonus oficiales guardados.")

with tab4:
    st.subheader("Fixture desde Excel base")
    st.caption("La app ya incluye el fixture extraído desde Mundial_2026.xlsx.")
    if st.button("Recargar fixture incluido y borrar pronósticos", type="secondary"):
        creados = seed_fixture_from_csv(force=True)
        st.success(f"Fixture recargado: {creados} partidos.")

    archivo = st.file_uploader("Importar fixture CSV", type=["csv"])
    if archivo and st.button("Importar CSV"):
        df = pd.read_csv(archivo)
        with SessionLocal() as db:
            for _, row in df.iterrows():
                if {"fecha", "hora_chile", "fase", "local", "visita"}.issubset(df.columns):
                    fecha_value = str(row["fecha"])[:10]
                    hora_value = str(row["hora_chile"])[:5]
                    fecha_hora_utc = chile_to_utc_naive(fecha_value, hora_value)
                else:
                    fecha_hora_utc = pd.to_datetime(row["fecha_hora"]).to_pydatetime()
                db.add(
                    Partido(
                        fecha_hora_utc=fecha_hora_utc,
                        fase=row["fase"],
                        equipo_local=row["local"],
                        equipo_visita=row["visita"],
                    )
                )
            db.commit()
        st.success("Fixture importado")

with tab5:
    with SessionLocal() as db:
        partidos_df = pd.DataFrame([{c.name: getattr(p, c.name) for c in Partido.__table__.columns} for p in db.scalars(select(Partido)).all()])
        usuarios_df = pd.DataFrame([{c.name: getattr(u, c.name) for c in Usuario.__table__.columns} for u in db.scalars(select(Usuario)).all()])
        pron_df = pd.DataFrame([{c.name: getattr(p, c.name) for c in Pronostico.__table__.columns} for p in db.scalars(select(Pronostico)).all()])
        bonus_df = pd.DataFrame([{c.name: getattr(b, c.name) for c in PronosticoBonus.__table__.columns} for b in db.scalars(select(PronosticoBonus)).all()])
    for name, df in {
        "Partidos.xlsx": partidos_df,
        "Usuarios.xlsx": usuarios_df,
        "Pronosticos.xlsx": pron_df,
        "Bonus.xlsx": bonus_df,
    }.items():
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, index=False)
        st.download_button(f"Descargar {name}", buffer.getvalue(), file_name=name)

    st.warning("Zona peligrosa")
    confirm1 = st.checkbox("Confirmo que quiero reiniciar el torneo")
    confirm2 = st.text_input("Escribe REINICIAR")
    if st.button("Reiniciar Torneo") and confirm1 and confirm2 == "REINICIAR":
        from database import engine
        from models import Base

        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
        seed_fixture_from_csv(force=True)
        st.success("Torneo reiniciado")
