from pydantic import BaseModel


class PlayersRegister(BaseModel):
    name: str
    email: str
    password: str
    mobile: str
    games: str
    address: str
    discord: str | None = None
    city: str
    state: str
    country: str
    logo_file: str
    active: bool


class GameInfo(BaseModel):
    game: str
    game_id: str
    game_name: str
