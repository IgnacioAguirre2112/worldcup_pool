import plotly.express as px
import streamlit as st

from database import ranking_dataframe, ranking_history_dataframe
from ui import inject_theme


st.set_page_config(page_title="Estadísticas", page_icon="📊", layout="wide")
inject_theme()
st.title("Estadísticas")

df = ranking_dataframe()
if df.empty:
    st.info("Sin datos suficientes.")
    st.stop()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Promedio de puntos", round(df["Total"].mean(), 2))
c2.metric("Máximo exactos", int(df["Exactos"].max()))
c3.metric("Máximo resultado", int(df["Resultado"].max()))
c4.metric("Máximo cant. goles", int(df["Cant. goles"].max()))
c5.metric("Máximo sin puntaje", int(df["Sin puntaje"].max()))

st.plotly_chart(px.bar(df, x="Participante", y="Total", title="Ranking histórico"), use_container_width=True)
st.plotly_chart(
    px.bar(
        df,
        x="Participante",
        y=["Exactos", "Resultado", "Cant. goles", "Sin puntaje", "Bonus"],
        barmode="group",
        title="Distribución de puntos",
    ),
    use_container_width=True,
)
history = ranking_history_dataframe()
if history.empty:
    st.info("El bump chart aparecerá cuando existan partidos con resultado oficial cargado.")
else:
    fig = px.line(
        history,
        x="Partido",
        y="Posición",
        color="Participante",
        markers=True,
        title="Evolución de posiciones",
        hover_data={"Fecha": True, "Total": True, "Posición": True, "Partido": True},
    )
    fig.update_yaxes(autorange="reversed", dtick=1, title="Posición")
    fig.update_xaxes(title="Partido", tickangle=-35)
    fig.update_traces(line=dict(width=3), marker=dict(size=8))
    fig.update_layout(legend_title_text="Participante", hovermode="closest")
    st.plotly_chart(fig, use_container_width=True)
