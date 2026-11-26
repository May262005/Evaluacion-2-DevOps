from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from prometheus_fastapi_instrumentator import Instrumentator

from .database import engine, get_db, Base
from . import models, schemas, auth
from .telemetry import setup_telemetry

app = FastAPI(title="Guitar Store API")

# Inicializar Telemetría OpenTelemetry / OpenObserve y Métricas Prometheus
setup_telemetry(app, engine)
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    """Crea las tablas al arrancar la app (no al importar)."""
    Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {"message": "Guitar Store API funcionando"}


# ---------- AUTH ----------
@app.post("/register", response_model=schemas.UserOut)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.username == user.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already registered")

    total_users = db.query(models.User).count()
    is_admin = True if total_users == 0 else user.is_admin

    new_user = models.User(
        username=user.username,
        hashed_password=auth.get_password_hash(user.password),
        is_admin=is_admin,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.post("/token", response_model=schemas.Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    if not form_data.username or not form_data.username.strip():
        raise HTTPException(status_code=400, detail="Username vacío")
    if not form_data.password or not form_data.password.strip():
        raise HTTPException(status_code=400, detail="Password vacía")
    if len(form_data.password.encode("utf-8")) > 72:
        raise HTTPException(status_code=400, detail="Password demasiado larga")
    if len(form_data.username) > 150:
        raise HTTPException(status_code=400, detail="Username demasiado largo")

    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}


@app.get("/users/me", response_model=schemas.UserOut)
def read_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user


# ---------- USERS CRUD (solo admin) ----------
@app.get("/users/", response_model=List[schemas.UserOut])
def list_users(
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(auth.get_current_admin),
):
    return db.query(models.User).all()


@app.post("/users/", response_model=schemas.UserOut)
def create_user(
    user: schemas.UserCreate,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(auth.get_current_admin),
):
    existing = db.query(models.User).filter(models.User.username == user.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already registered")

    new_user = models.User(
        username=user.username,
        hashed_password=auth.get_password_hash(user.password),
        is_admin=user.is_admin,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.put("/users/{user_id}", response_model=schemas.UserOut)
def update_user(
    user_id: int,
    user: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(auth.get_current_admin),
):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.username is not None:
        if user.username != db_user.username:
            dup = db.query(models.User).filter(models.User.username == user.username).first()
            if dup:
                raise HTTPException(status_code=400, detail="Username already registered")
        db_user.username = user.username

    if user.password is not None:
        db_user.hashed_password = auth.get_password_hash(user.password)

    if user.is_admin is not None:
        db_user.is_admin = user.is_admin

    db.commit()
    db.refresh(db_user)
    return db_user


@app.delete("/users/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(auth.get_current_admin),
):
    if current_admin.id == user_id:
        raise HTTPException(status_code=400, detail="No puedes eliminarte a ti mismo")

    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(db_user)
    db.commit()
    return


# ---------- GUITARS CRUD ----------
@app.post("/guitars/", response_model=schemas.GuitarOut)
def create_guitar(
    guitar: schemas.GuitarCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    db_guitar = models.Guitar(**guitar.model_dump())
    db.add(db_guitar)
    db.commit()
    db.refresh(db_guitar)
    return db_guitar


@app.get("/guitars/", response_model=List[schemas.GuitarOut])
def read_guitars(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return db.query(models.Guitar).all()


@app.get("/guitars/{guitar_id}", response_model=schemas.GuitarOut)
def read_guitar(
    guitar_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    db_guitar = db.query(models.Guitar).filter(models.Guitar.id == guitar_id).first()
    if not db_guitar:
        raise HTTPException(status_code=404, detail="Guitar not found")
    return db_guitar


@app.put("/guitars/{guitar_id}", response_model=schemas.GuitarOut)
def update_guitar(
    guitar_id: int,
    guitar: schemas.GuitarCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    db_guitar = db.query(models.Guitar).filter(models.Guitar.id == guitar_id).first()
    if not db_guitar:
        raise HTTPException(status_code=404, detail="Guitar not found")

    for key, value in guitar.model_dump().items():
        setattr(db_guitar, key, value)

    db.commit()
    db.refresh(db_guitar)
    return db_guitar


@app.delete("/guitars/{guitar_id}", status_code=204)
def delete_guitar(
    guitar_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    db_guitar = db.query(models.Guitar).filter(models.Guitar.id == guitar_id).first()
    if not db_guitar:
        raise HTTPException(status_code=404, detail="Guitar not found")

    db.delete(db_guitar)
    db.commit()
    return