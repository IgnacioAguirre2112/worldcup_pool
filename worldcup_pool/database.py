from __future__ import annotations

import csv
import os
import ssl
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
from zoneinfo import ZoneInfo

from sqlalchemy import create_engine, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload, selectinload, sessionmaker

from models import Base, Partido, Pronostico, PronosticoBonus, ResultadoBonus, Usuario
from scoring import calcular_puntaje


ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "data" / "mundial2026.db"
FIXTURE_PATH = ROOT / "uploads" / "fixture_mundial_2026.csv"
CHILE_TZ = ZoneInfo("America/Santiago")
UTC_TZ = ZoneInfo("UTC")
BONUS_DEADLINE_CHILE = datetime(2026, 6, 28, 0, 0, tzinfo=CHILE_TZ)


def get_secret_value(key: str) -> str | None:
    if os.environ.get(key):
        return os.environ[key]
    try:
        import streamlit as st

        value = st.secrets.get(key)
        return str(value) if value else None
    except Exception:
        return None


def using_persistent_database() -> bool:
    return not IS_SQLITE


def database_status_label() -> str:
    if IS_SQLITE:
        return "SQLite local (no persistente en Streamlit Cloud)"
    return "Postgres externo (persistente)"


def database_url() -> str:
    url = get_secret_value("DATABASE_URL")
    if url:
        return normalize_postgres_url(url)
    DB_PATH.parent.mkdir(exist_ok=True)
    return f"sqlite:///{DB_PATH}"


def normalize_postgres_url(url: str) -> str:
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+pg8000://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+pg8000://", 1)
    elif url.startswith("postgresql+psycopg2://"):
        url = url.replace("postgresql+psycopg2://", "postgresql+pg8000://", 1)

    if url.startswith("postgresql+pg8000://"):
        parts = urlsplit(url)
        # Neon strings often include sslmode/channel_binding, which pg8000 does
        # not accept as direct DB-API keyword arguments. SSL is enabled below.
        return urlunsplit((parts.scheme, parts.netloc, parts.path, "", parts.fragment))

    return url


DATABASE_URL = database_url()
IS_SQLITE = DATABASE_URL.startswith("sqlite")
CONNECT_ARGS = {"check_same_thread": False} if IS_SQLITE else {"ssl_context": ssl.create_default_context()}
engine = create_engine(
    DATABASE_URL,
    connect_args=CONNECT_ARGS,
    pool_pre_ping=not IS_SQLITE,
)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

FASES = ["Prueba", "Grupos", "Dieciseisavos", "Octavos", "Cuartos", "Semifinal", "Tercer Lugar", "Final"]
_DB_INITIALIZED_ENGINE_ID: int | None = None


def init_db() -> None:
    global _DB_INITIALIZED_ENGINE_ID
    current_engine_id = id(engine)
    if _DB_INITIALIZED_ENGINE_ID == current_engine_id:
        return
    Base.metadata.create_all(engine)
    ensure_fixture_loaded()
    _DB_INITIALIZED_ENGINE_ID = current_engine_id


def ensure_fixture_loaded() -> None:
    with SessionLocal() as db:
        partidos = db.scalar(select(func.count(Partido.id))) or 0
        pronosticos = db.scalar(select(func.count(Pronostico.id))) or 0
    if partidos == 0:
        seed_fixture_from_csv()
    elif partidos < 100 and pronosticos == 0:
        seed_fixture_from_csv(force=True)
    else:
        sync_missing_fixture_from_csv()


def chile_to_utc_naive(fecha: str, hora: str) -> datetime:
    local_dt = datetime.strptime(f"{fecha} {hora}", "%Y-%m-%d %H:%M").replace(tzinfo=CHILE_TZ)
    return local_dt.astimezone(UTC_TZ).replace(tzinfo=None)


def utc_to_chile(dt: datetime) -> datetime:
    return dt.replace(tzinfo=UTC_TZ).astimezone(CHILE_TZ)


def seed_fixture_from_csv(force: bool = False) -> int:
    if not FIXTURE_PATH.exists():
        return 0
    with SessionLocal() as db:
        if not force and (db.scalar(select(func.count(Partido.id))) or 0) > 0:
            return 0
        if force:
            db.query(Pronostico).delete()
            db.query(Partido).delete()
        with FIXTURE_PATH.open(encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            creados = 0
            for row in reader:
                db.add(
                    Partido(
                        fecha_hora_utc=chile_to_utc_naive(row["fecha"], row["hora_chile"]),
                        fase=row["fase"],
                        equipo_local=row["local"],
                        equipo_visita=row["visita"],
                    )
                )
                creados += 1
        db.commit()
        return creados


def sync_missing_fixture_from_csv() -> int:
    if not FIXTURE_PATH.exists():
        return 0
    with SessionLocal() as db:
        creados = 0
        with FIXTURE_PATH.open(encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                fecha_hora_utc = chile_to_utc_naive(row["fecha"], row["hora_chile"])
                existe = db.scalar(
                    select(Partido.id).where(
                        Partido.fecha_hora_utc == fecha_hora_utc,
                        Partido.fase == row["fase"],
                        Partido.equipo_local == row["local"],
                        Partido.equipo_visita == row["visita"],
                    )
                )
                if existe:
                    continue
                db.add(
                    Partido(
                        fecha_hora_utc=fecha_hora_utc,
                        fase=row["fase"],
                        equipo_local=row["local"],
                        equipo_visita=row["visita"],
                    )
                )
                creados += 1
        db.commit()
        return creados


def normalizar_nombre_participante(nombre: str) -> str:
    nombre = " ".join(nombre.strip().split())[:80]
    if not nombre:
        raise ValueError("Ingresa un nombre válido")
    return nombre


def buscar_usuario_por_nombre(nombre: str) -> Usuario | None:
    nombre = normalizar_nombre_participante(nombre)
    with SessionLocal() as db:
        return db.scalar(select(Usuario).where(func.lower(Usuario.nombre) == nombre.lower()))


def crear_usuario(nombre: str) -> Usuario:
    nombre = normalizar_nombre_participante(nombre)
    with SessionLocal() as db:
        if db.scalar(select(Usuario.id).where(func.lower(Usuario.nombre) == nombre.lower())):
            raise ValueError("Ese nombre ya está registrado. Usa otro nombre para evitar duplicados.")
        user = Usuario(nombre=nombre)
        db.add(user)
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise ValueError("Ese nombre ya está registrado. Usa otro nombre para evitar duplicados.") from exc
        return user


def get_or_create_user(nombre: str) -> Usuario:
    nombre = normalizar_nombre_participante(nombre)
    with SessionLocal() as db:
        user = db.scalar(select(Usuario).where(func.lower(Usuario.nombre) == nombre.lower()))
        if user:
            return user
    return crear_usuario(nombre)


def partido_bloqueado(partido: Partido) -> bool:
    return datetime.utcnow() >= partido.fecha_hora_utc


def guardar_pronostico(usuario_id: int, partido_id: int, gl: int, gv: int) -> None:
    with SessionLocal() as db:
        partido = db.get(Partido, partido_id)
        if not partido or partido_bloqueado(partido):
            raise ValueError("Pronóstico cerrado")
        p = db.scalar(select(Pronostico).where(Pronostico.usuario_id == usuario_id, Pronostico.partido_id == partido_id))
        if p:
            p.goles_local_pronosticado = gl
            p.goles_visita_pronosticado = gv
            p.fecha_ingreso = datetime.utcnow()
        else:
            db.add(
                Pronostico(
                    usuario_id=usuario_id,
                    partido_id=partido_id,
                    goles_local_pronosticado=gl,
                    goles_visita_pronosticado=gv,
                )
            )
        db.commit()


def primera_fecha_mundial() -> datetime | None:
    with SessionLocal() as db:
        return db.scalar(select(func.min(Partido.fecha_hora_utc)))


def bonus_bloqueado() -> bool:
    return datetime.now(CHILE_TZ) >= BONUS_DEADLINE_CHILE


def equipos_disponibles() -> list[str]:
    with SessionLocal() as db:
        locales = db.scalars(select(Partido.equipo_local)).all()
        visitas = db.scalars(select(Partido.equipo_visita)).all()
    return sorted({*locales, *visitas})


def calcular_bonus_usuario(bonus: PronosticoBonus | None, oficial: ResultadoBonus | None) -> int:
    if not bonus or not oficial:
        return 0
    puntos = 0
    if bonus.campeon and oficial.campeon and bonus.campeon.strip().lower() == oficial.campeon.strip().lower():
        puntos += 5
    if bonus.subcampeon and oficial.subcampeon and bonus.subcampeon.strip().lower() == oficial.subcampeon.strip().lower():
        puntos += 3
    if bonus.tercer_lugar and oficial.tercer_lugar and bonus.tercer_lugar.strip().lower() == oficial.tercer_lugar.strip().lower():
        puntos += 1
    if bonus.goleador and oficial.goleador and bonus.goleador.strip().lower() == oficial.goleador.strip().lower():
        puntos += 3
    return puntos


def ranking_dataframe():
    import pandas as pd

    rows = []
    with SessionLocal() as db:
        usuarios = db.scalars(
            select(Usuario)
            .options(selectinload(Usuario.pronosticos).selectinload(Pronostico.partido))
            .order_by(Usuario.nombre)
        ).all()
        bonus_por_usuario = {b.usuario_id: b for b in db.scalars(select(PronosticoBonus)).all()}
        oficial = db.get(ResultadoBonus, 1)
        for u in usuarios:
            total = exactos = ganadores = cant_goles = bonus = 0
            for p in u.pronosticos:
                if p.partido.resultado_oficial_cargado:
                    puntos, tipo = calcular_puntaje(
                        p.goles_local_pronosticado,
                        p.goles_visita_pronosticado,
                        p.partido.goles_local,
                        p.partido.goles_visita,
                    )
                    total += puntos
                    exactos += tipo == "exacto"
                    ganadores += tipo == "ganador"
                    cant_goles += tipo == "goles"
            bonus = calcular_bonus_usuario(bonus_por_usuario.get(u.id), oficial)
            total += bonus
            rows.append(
                {
                    "Participante": u.nombre,
                    "Exactos": exactos,
                    "Ganadores": ganadores,
                    "Cant. goles": cant_goles,
                    "Bonus": bonus,
                    "Total": total,
                }
            )

    df = pd.DataFrame(rows, columns=["Participante", "Exactos", "Ganadores", "Cant. goles", "Bonus", "Total"])
    if not df.empty:
        df = df.sort_values(["Total", "Exactos", "Ganadores", "Cant. goles"], ascending=False).reset_index(drop=True)
        df.insert(0, "Posición", range(1, len(df) + 1))
    return df


def pronosticos_publicos_dataframe():
    import pandas as pd

    rows = []
    ahora = datetime.utcnow()
    with SessionLocal() as db:
        pronosticos = db.scalars(
            select(Pronostico)
            .options(joinedload(Pronostico.usuario), joinedload(Pronostico.partido))
            .join(Pronostico.usuario)
            .join(Pronostico.partido)
            .order_by(Partido.fecha_hora_utc, Partido.equipo_local, Usuario.nombre)
        ).all()
        for pronostico in pronosticos:
            partido = pronostico.partido
            cerrado = ahora >= partido.fecha_hora_utc
            hora_chile = utc_to_chile(partido.fecha_hora_utc)
            rows.append(
                {
                    "Fecha": hora_chile.strftime("%Y-%m-%d %H:%M"),
                    "Fase": partido.fase,
                    "Partido": f"{partido.equipo_local} vs {partido.equipo_visita}",
                    "Participante": pronostico.usuario.nombre,
                    "Pronóstico": (
                        f"{pronostico.goles_local_pronosticado} - {pronostico.goles_visita_pronosticado}"
                        if cerrado
                        else "Oculto hasta el inicio"
                    ),
                    "Estado": "Cerrado" if cerrado else "Abierto",
                    "Ingresado": pronostico.fecha_ingreso.strftime("%Y-%m-%d %H:%M"),
                }
            )
    return pd.DataFrame(rows, columns=["Fecha", "Fase", "Partido", "Participante", "Pronóstico", "Estado", "Ingresado"])
