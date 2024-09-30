from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from schemas import PlayerGameInfo, PlayerTable
from .player_model import GameInfo, PlayersRegister
from db import get_db
from utils import get_password_hash

router = APIRouter(prefix="/player", tags=["Player"])


@router.post("/")
def add_player(player: PlayersRegister, db: Session = Depends(get_db)):
    player.password = get_password_hash(player.password)
    new = PlayerTable(**player.model_dump())
    db.add(new)
    db.commit()
    return player


@router.put("/{player_id}")
def update_player(
    player_id: int, player: PlayersRegister, db: Session = Depends(get_db)
):
    player.password = get_password_hash(player.password)
    db.query(PlayersRegister).filter(PlayersRegister.id == player_id).update(
        player.model_dump()
    )
    db.commit()
    return player


@router.post("/add_game_info/{player_id}")
def add_game_info(player_id: int, player: GameInfo, db: Session = Depends(get_db)):
    new = PlayerGameInfo(**player.model_dump(), player_id=player_id)
    db.add(new)
    db.commit()
    return player


@router.get("/get_game_info/{player_id}")
def get_game_info(player_id: int, db: Session = Depends(get_db)):
    game_info = (
        db.query(PlayerGameInfo).filter(PlayerGameInfo.player_id == player_id).all()
    )
    return game_info


@router.get("/get_game_info_by_game/{game}/{player_id}")
def get_game_info_by_game(game: str, player_id: int, db: Session = Depends(get_db)):
    game_info = (
        db.query(PlayerGameInfo)
        .filter(PlayerGameInfo.player_id == player_id)
        .filter(PlayerGameInfo.game == game)
        .first()
    )
    return game_info


@router.get("/get_game_info_by_game_id/{game_id}/{player_id}")
def get_game_info_by_game_id(
    game_id: str, player_id: int, db: Session = Depends(get_db)
):
    game_info = (
        db.query(PlayerGameInfo)
        .filter(PlayerGameInfo.player_id == player_id)
        .filter(PlayerGameInfo.game_id == game_id)
        .first()
    )
    return game_info


@router.put("/update_game_info/{game_info_id}")
def update_game_info(
    game_info_id: int, player: GameInfo, db: Session = Depends(get_db)
):
    db.query(PlayerGameInfo).filter(PlayerGameInfo.id == game_info_id).update(
        player.model_dump()
    )
    db.commit()
    return player


@router.get("/")
def get_all_players(db: Session = Depends(get_db)):
    players = db.query(PlayerTable).order_by(PlayerTable.created_at.desc()).all()
    return players


@router.get("/{player_id}")
def get_player_by_id(player_id: int, db: Session = Depends(get_db)):
    player = (
        db.query(PlayerTable)
        .join(PlayerTable.game_info)
        .filter(PlayerTable.id == player_id)
        .first()
    )
    return player
