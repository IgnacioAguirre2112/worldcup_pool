from io import BytesIO

import streamlit as st
from streamlit_autorefresh import st_autorefresh

from database import ranking_dataframe
from ui import inject_theme


st.set_page_config(page_title="Ranking", page_icon="🏆", layout="wide")
inject_theme()
st.title("Ranking")
st_autorefresh(interval=60000, key="ranking_refresh")

df = ranking_dataframe()
if df.empty:
    st.info("Aún no hay puntajes calculados.")
else:
    st.dataframe(df, hide_index=True, use_container_width=True)

buffer = BytesIO()
with __import__("pandas").ExcelWriter(buffer, engine="openpyxl") as writer:
    df.to_excel(writer, index=False, sheet_name="Ranking")
st.download_button(
    "Descargar Ranking.xlsx",
    data=buffer.getvalue(),
    file_name="Ranking.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
st.info("Publica esta app en Streamlit Community Cloud y comparte la URL pública con los participantes.")
