from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    username: str  # campo "username" do OAuth2PasswordRequestForm corresponde ao email
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # segundos até expirar o access token


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenPayload(BaseModel):
    sub: str  # user UUID como string
    jti: str  # JWT ID para revogação
    type: str  # "access" | "refresh"
