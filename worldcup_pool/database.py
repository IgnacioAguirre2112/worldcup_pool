from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from sqlalchemy import create_engine, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from models import Base, Partido, Pronostico, PronosticoBonus, ResultadoBonus, Usuario
from scoring import calcular_puntaje


ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "data" / "mundial2026.db"
FIXTURE_PATH = ROOT / "uploads" / "fixture_mundial_2026.csv"
CHILE_TZ = ZoneInfo("America/Santiago")
UTC_TZ = ZoneInfo("UTC")

DB_PATH.parent.mkdir(exist_ok=True)
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

FASES = ["Grupos", "Dieciseisavos", "Octavos", "Cuartos", "Semifinal", "Tercer Lugar", "Final"]


def init_db() -> None:
    Base.metadata.create_all(engine)
    ensure_fixture_loaded()


def ensure_fixture_loaded() -> None:
    with SessionLocal() as db:
        partidos = db.scalar(select(func.count(Partido.id))) or 0
        pronosticos = db.scalar(select(func.count(Pronostico.id))) or 0
    if partidos == 0:
        seed_fixture_from_csv()
    elif partidos < 100 and pronosticos == 0:
        seed_fixture_from_csv(force=True)


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
    primera = primera_fecha_mundial()
    return bool(primera and datetime.utcnow() >= primera)


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
        usuarios = db.scalars(select(Usuario).order_by(Usuario.nombre)).all()
        oficial = db.get(ResultadoBonus, 1)
        for u in usuarios:
            total = exactos = parciales = bonus = 0
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
                    parciales += tipo in {"parcial", "parcial+diferencia"}
            bonus = calcular_bonus_usuario(db.get(PronosticoBonus, u.id), oficial)
            total += bonus
            rows.append({"Participante": u.nombre, "Exactos": exactos, "Parciales": parciales, "Bonus": bonus, "Total": total})

    df = pd.DataFrame(rows, columns=["Participante", "Exactos", "Parciales", "Bonus", "Total"])
    if not df.empty:
        df = df.sort_values(["Total", "Exactos", "Parciales"], ascending=False).reset_index(drop=True)
        df.insert(0, "Posición", range(1, len(df) + 1))
    return df
