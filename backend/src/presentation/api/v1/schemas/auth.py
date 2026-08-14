"""
Schemas Pydantic dos endpoints de autenticação.

Responsabilidade: validar o FORMATO da entrada HTTP (isso é diferente de
validar REGRA DE NEGÓCIO, que já é responsabilidade das entidades de
domínio e dos casos de uso). Ex: `EmailStr` aqui garante que chegou algo
com "formato" de e-mail antes mesmo de chamar o caso de uso — mas quem
decide se aquele e-mail já está cadastrado, ou se a campanha permite
login, é o caso de uso, não este arquivo.
"""

from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class RegisterTenantRequest(BaseModel):
    tenant_name: str = Field(..., min_length=3, max_length=255, examples=["Campanha João Silva 2028"])
    admin_name: str = Field(..., min_length=1, max_length=255)
    admin_email: EmailStr
    admin_password: str = Field(..., min_length=8, description="Mínimo de 8 caracteres")


class RegisterTenantResponse(BaseModel):
    tenant_id: UUID
    user_id: UUID


class LoginRequest(BaseModel):
    tenant_id: UUID
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserMeResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    email: str
    role_names: list[str]
