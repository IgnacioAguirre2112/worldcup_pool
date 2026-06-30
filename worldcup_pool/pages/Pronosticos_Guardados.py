import streamlit as st

from database import init_db, pronosticos_publicos_dataframe, ultimos_pronosticos_cerrados_dataframe, using_persistent_database
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
    if "pronosticos_guardados_modo" not in st.session_state:
        st.session_state.pronosticos_guardados_modo = "Todos"

    ultimos_cerrados = st.button("Últimos cerrados", use_container_width=False)

    opciones = ["Todos", "Cerrado", "Abierto"]
    estado = st.radio(
        "Mostrar",
        opciones,
        horizontal=True,
        index=opciones.index(st.session_state.pronosticos_guardados_modo)
        if st.session_state.pronosticos_guardados_modo in opciones
        else 0,
    )
    if ultimos_cerrados:
        st.session_state.pronosticos_guardados_modo = "Últimos cerrados"
    elif estado != st.session_state.pronosticos_guardados_modo:
        st.session_state.pronosticos_guardados_modo = estado

    if st.session_state.pronosticos_guardados_modo == "Últimos cerrados":
        filtrado = ultimos_pronosticos_cerrados_dataframe(limit=2)
    else:
        modo = st.session_state.pronosticos_guardados_modo
        filtrado = df if modo == "Todos" else df[df["Estado"] == modo]
    st.dataframe(filtrado, hide_index=True, use_container_width=True)
