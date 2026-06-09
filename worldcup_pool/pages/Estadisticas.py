import plotly.express as px
import streamlit as st

from database import ranking_dataframe
from ui import inject_theme


st.set_page_config(page_title="Estadísticas", page_icon="📊", layout="wide")
inject_theme()
st.title("Estadísticas")

df = ranking_dataframe()
if df.empty:
    st.info("Sin datos suficientes.")
    st.stop()

c1, c2, c3 = st.columns(3)
c1.metric("Promedio de puntos", round(df["Total"].mean(), 2))
c2.metric("Máximo exactos", int(df["Exactos"].max()))
c3.metric("Máximo ganadores", int(df["Ganadores"].max()))

st.plotly_chart(px.bar(df, x="Participante", y="Total", title="Ranking histórico"), use_container_width=True)
st.plotly_chart(
    px.bar(df, x="Participante", y=["Exactos", "Ganadores", "Bonus"], barmode="group", title="Distribución de puntos"),
    use_container_width=True,
)
st.plotly_chart(
    px.line(df.sort_values("Posición"), x="Participante", y="Total", markers=True, title="Evolución acumulada"),
    use_container_width=True,
)
