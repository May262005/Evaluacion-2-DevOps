# app/schemas.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional


# ---------- USERS ----------
class UserCreate(BaseModel):
    username: str = Field(min_length=1, max_length=150, strict=True)
    password: str = Field(min_length=1, max_length=128, strict=True)
    is_admin: bool = False

    @field_validator("username")
    @classmethod
    def username_no_vacio(cls, v):
        if not v or not v.strip():
            raise ValueError("username no puede estar vacío ni ser solo espacios")
        return v.strip()

    @field_validator("password")
    @classmethod
    def password_no_vacio(cls, v):
        if not v or not v.strip():
            raise ValueError("password no puede estar vacío ni ser solo espacios")
        return v

    @field_validator("is_admin", mode="before")
    @classmethod
    def is_admin_booleano(cls, v):
        if isinstance(v, bool):
            return v
        if isinstance(v, int) and v in (0, 1):
            return bool(v)
        raise ValueError("is_admin debe ser booleano")


class UserUpdate(BaseModel):
    username: Optional[str] = Field(default=None, min_length=1, max_length=150, strict=True)
    password: Optional[str] = Field(default=None, min_length=1, max_length=128, strict=True)
    is_admin: Optional[bool] = None

    @field_validator("username")
    @classmethod
    def username_no_vacio(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError("username no puede estar vacío ni ser solo espacios")
        return v.strip() if v else v

    @field_validator("password")
    @classmethod
    def password_no_vacio(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError("password no puede estar vacío ni ser solo espacios")
        return v


class UserOut(BaseModel):
    id: int
    username: str
    is_admin: bool

    model_config = {"from_attributes": True}


# ---------- GUITARS ----------
class GuitarCreate(BaseModel):
    brand: str = Field(min_length=1, max_length=100, strict=True)
    model: str = Field(min_length=1, max_length=100, strict=True)
    price: float = Field(gt=0, strict=True, description="El precio debe ser mayor a 0")

    @field_validator("brand")
    @classmethod
    def brand_no_vacio(cls, v):
        if not v or not v.strip():
            raise ValueError("brand no puede estar vacío ni ser solo espacios")
        return v.strip()

    @field_validator("model")
    @classmethod
    def model_no_vacio(cls, v):
        if not v or not v.strip():
            raise ValueError("model no puede estar vacío ni ser solo espacios")
        return v.strip()


class GuitarOut(BaseModel):
    id: int
    brand: str
    model: str
    price: float

    model_config = {"from_attributes": True}


# ---------- TOKEN ----------
class Token(BaseModel):
    access_token: str
    token_type: str