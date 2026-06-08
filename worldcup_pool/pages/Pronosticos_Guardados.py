import streamlit as st

from database import init_db, pronosticos_publicos_dataframe, using_persistent_database
from ui import inject_theme


st.set_page_config(page_title="Pronósticos Guardados", page_icon="📋", layout="wide")
inject_theme()
init_db()

st.title("Pronósticos Guardados")

if not using_persistent_database():
    st.warning(
        "La app está usando SQLite local. En Streamlit Cloud estos datos pueden borrarse con reboot. "
        "Configura DATABASE_URL con Neon para que sean persistentes."
    )

st.caption("Los pronósticos de partidos abiertos se ocultan hasta la hora de inicio para evitar copias.")

df = pronosticos_publicos_dataframe()
if df.empty:
    st.info("Aún no hay pronósticos guardados.")
else:
    estado = st.radio("Mostrar", ["Todos", "Cerrado", "Abierto"], horizontal=True)
    filtrado = df if estado == "Todos" else df[df["Estado"] == estado]
    st.dataframe(filtrado, hide_index=True, use_container_width=True)
