from typing import List
from pydantic import BaseModel, EmailStr
from uuid import UUID


class Player(BaseModel):
    id: UUID | None

    player_name: str | None
    game_id: str | None
    captain: bool | None
    mobile: str | None
    email: EmailStr | None
    age: int | None
    city: str | None
    college: str | None
    is_joined: bool | None
    is_dead: bool | None
    kill: int | None


class TeamList(BaseModel):
    id: UUID | None
    teamName: str | None
    logo: str | None
    email: str | None
    mobile: str | None
    city: str | None
    college: str | None
    payment_received: bool | None
    rank: int | None
    players: List[Player]
