from pydantic import BaseModel, EmailStr, Field


class GameInfo(BaseModel):
    game: str = Field("FF")
    game_id: str
    game_name: str


class PlayersRegister(BaseModel):
    team_code: str
    enrollNo: str
    player_name: str = Field(..., min_length=5)
    mobile: str = Field(..., pattern=r"[6-9]\d{9}", max_length=10, min_length=10)
    email: EmailStr
    age: str | None = None
    city: str | None = None
    college: str | None = None
    discord: str | None = None
    gameInfo: GameInfo


class RegisterTeam(BaseModel):
    team_name: str
    email: str
    mobile: str
    city: str
    college: str
