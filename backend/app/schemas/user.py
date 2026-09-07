from pydantic import BaseModel, EmailStr, Field, field_validator

# Registration is public and unauthenticated (see auth.py's register()), so
# these are the only backstop against a garbage or hostile password/name —
# nothing upstream re-checks them.
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128  # bcrypt truncates past 72 bytes anyway; this just
# blocks a multi-megabyte string from being hashed at all.
MAX_NAME_LENGTH = 200

class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=MAX_NAME_LENGTH)
    email: EmailStr
    password: str = Field(..., min_length=MIN_PASSWORD_LENGTH, max_length=MAX_PASSWORD_LENGTH)
    role: str = "learner"

    @field_validator("password")
    @classmethod
    def _password_has_letter_and_digit(cls, value: str) -> str:
        # Deliberately not a "special character" rule (those mostly just
        # push people toward predictable substitutions like "P@ssw0rd") —
        # just enough to reject the common weakest cases ("12345678",
        # "password") without being annoying about it.
        if not any(c.isalpha() for c in value) or not any(c.isdigit() for c in value):
            raise ValueError("Password must contain at least one letter and one number.")
        return value

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
