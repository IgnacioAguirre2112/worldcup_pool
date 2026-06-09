# Quiniela Mundial FIFA 2026

Aplicación Streamlit para administrar una competencia de pronósticos del Mundial FIFA 2026.

## Qué incluye

- Fixture extraído desde `Mundial_2026.xlsx`.
- Ingreso de participantes por nombre, listo para compartir por link público.
- Pronósticos por partido editables solo hasta la hora de inicio.
- Horarios mostrados en hora de Chile y guardados internamente en UTC.
- Ranking automático con puntaje excluyente: exacto 5, ganador correcto 3, cantidad total de goles 1, sin acierto 0.
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

## Base de datos persistente

En local la app usa SQLite:

```text
data/mundial2026.db
```

En Streamlit Community Cloud debes usar una base externa para que los participantes y pronósticos no se borren al hacer reboot o redeploy. Crea una base Postgres en Supabase o Neon y agrega el connection string en los secrets de Streamlit:

```toml
DATABASE_URL="postgresql://usuario:password@host:5432/database"
ADMIN_USER="admin"
ADMIN_PASSWORD="password"
```

La app creará las tablas automáticamente y cargará el fixture inicial desde `uploads/fixture_mundial_2026.csv`.

## Admin

Configura credenciales en `.streamlit/secrets.toml` o en Streamlit Community Cloud:

```toml
ADMIN_USER="admin"
ADMIN_PASSWORD="password"
```

## Publicar y compartir

1. Sube este proyecto a GitHub.
2. En Streamlit Community Cloud, crea una app apuntando a `worldcup_pool/app.py`.
3. Configura `DATABASE_URL`, `ADMIN_USER` y `ADMIN_PASSWORD` en secrets.
4. Comparte la URL pública con los participantes.

## Fixture CSV

La app carga automáticamente `uploads/fixture_mundial_2026.csv`. Formato:

```csv
id_partido,fecha,hora_chile,fase,grupo,local,visita
1,2026-06-11,15:00,Fase de grupos,A,México,Sudáfrica
```
