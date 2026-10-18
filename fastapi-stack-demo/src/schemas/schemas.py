from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class LivenessResponse(BaseModel):
    status: str


class ReadinessResponse(BaseModel):
    ready: bool
    checks: dict[str, str]


class UserRequest(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(..., min_length=8)

    @field_validator("password")
    @classmethod
    def validate_password(cls, psw: str) -> str:
        required_chars = "_-0123456789"
        if not any(char in required_chars for char in psw):
            raise ValueError("слабый пароль: добавьте цифру или _ -")
        return psw


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    email: EmailStr


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AddRequest(BaseModel):
    a: int
    b: int


class TaskCreated(BaseModel):
    task_id: str


class TaskStatus(BaseModel):
    task_id: str
    state: str
    result: int | None = None
    error: str | None = None
