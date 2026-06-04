# Quiniela Mundial FIFA 2026

Aplicación Streamlit para administrar una competencia de pronósticos del Mundial FIFA 2026.

## Qué incluye

- Fixture de 104 partidos extraído desde `Mundial_2026.xlsx`.
- Ingreso de participantes por nombre, listo para compartir por link público.
- Pronósticos por partido editables solo hasta la hora de inicio.
- Horarios mostrados en hora de Chile y guardados internamente en UTC.
- Ranking automático con puntaje: exacto 5, ganador/empate correcto 3, diferencia correcta +1.
- Bonus: Campeón +5, Subcampeón +3, Tercer lugar +1, Goleador +3.
- Panel admin para cargar resultados, bonus oficiales, exportar datos y recargar fixture.
- Interfaz oscura estilo Mundial 2026 con banderas desde `scripts/assets/flags.zip`.

## Instalación local

```bash
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m streamlit run app.py
```

Luego abre `http://localhost:8501`.

## Admin

Configura credenciales en `.streamlit/secrets.toml` o en Streamlit Community Cloud:

```toml
ADMIN_USER="admin"
ADMIN_PASSWORD="password"
```

## Publicar y compartir

1. Sube este proyecto a GitHub.
2. En Streamlit Community Cloud, crea una app apuntando a `app.py`.
3. Configura los secrets de admin.
4. Comparte la URL pública con los participantes.

## Fixture CSV

La app carga automáticamente `uploads/fixture_mundial_2026.csv`. Formato:

```csv
id_partido,fecha,hora_chile,fase,grupo,local,visita
1,2026-06-11,15:00,Fase de grupos,A,México,Sudáfrica
```
