from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Usuario(Base):
    __tablename__ = "usuarios"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    fecha_registro: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    pronosticos = relationship("Pronostico", back_populates="usuario", cascade="all, delete-orphan")


class Partido(Base):
    __tablename__ = "partidos"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fecha_hora_utc: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    fase: Mapped[str] = mapped_column(String(40), nullable=False)
    equipo_local: Mapped[str] = mapped_column(String(80), nullable=False)
    equipo_visita: Mapped[str] = mapped_column(String(80), nullable=False)
    goles_local: Mapped[int | None] = mapped_column(Integer, nullable=True)
    goles_visita: Mapped[int | None] = mapped_column(Integer, nullable=True)
    resultado_oficial_cargado: Mapped[bool] = mapped_column(Boolean, default=False)
    pronosticos = relationship("Pronostico", back_populates="partido", cascade="all, delete-orphan")


class Pronostico(Base):
    __tablename__ = "pronosticos"
    __table_args__ = (UniqueConstraint("usuario_id", "partido_id", name="uq_usuario_partido"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    partido_id: Mapped[int] = mapped_column(ForeignKey("partidos.id"), nullable=False)
    goles_local_pronosticado: Mapped[int] = mapped_column(Integer, nullable=False)
    goles_visita_pronosticado: Mapped[int] = mapped_column(Integer, nullable=False)
    fecha_ingreso: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    usuario = relationship("Usuario", back_populates="pronosticos")
    partido = relationship("Partido", back_populates="pronosticos")


class PronosticoBonus(Base):
    __tablename__ = "pronosticos_bonus"
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), primary_key=True)
    campeon: Mapped[str | None] = mapped_column(String(80))
    subcampeon: Mapped[str | None] = mapped_column(String(80))
    tercer_lugar: Mapped[str | None] = mapped_column(String(80))
    goleador: Mapped[str | None] = mapped_column(String(80))


class ResultadoBonus(Base):
    __tablename__ = "resultado_bonus"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    campeon: Mapped[str | None] = mapped_column(String(80))
    subcampeon: Mapped[str | None] = mapped_column(String(80))
    tercer_lugar: Mapped[str | None] = mapped_column(String(80))
    goleador: Mapped[str | None] = mapped_column(String(80))
