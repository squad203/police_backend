import json
from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import EmailStr
from Routes.models_bgmi import Player, TeamList
from schemas import TeamTable, BgmiPlayers, TournamentTable
from sqlalchemy.orm import Session
from db import get_db

router = APIRouter(prefix="/bgmi", tags=["BGMI"])


def getTournamentId(db: Session):
    data = db.query(TournamentTable).filter(TournamentTable.status == "active").first()
    if not data:
        raise HTTPException(status_code=404, detail="No Active Tournament Found")
    return data.id


@router.post("/register")
async def register(
    teamName: str = Form(...),
    logo: UploadFile = File(...),
    email: EmailStr = Form(...),
    mobile: str = Form(...),
    city: str = Form(...),
    college: str = Form(...),
    players: str = Form(...),
    db: Session = Depends(get_db),
):
    teamId = uuid.uuid4()
    playersJson = json.loads(players)
    newTeam = TeamTable(
        id=teamId,
        tournament_id=getTournamentId(db),
        teamName=teamName,
        email=email,
        mobile=mobile,
        city=city,
        college=college,
        logo=logo.filename,
        rank=0,
    )
    db.add(newTeam)
    gameId = set()
    with open(f"media/{teamId}.png", "wb") as f:
        f.write(logo.file.read())
    for player in playersJson:
        if player["game_id"] not in gameId:

            newPlayer = BgmiPlayers(
                id=uuid.uuid4(),
                team_id=teamId,
                player_name=player["player_name"],
                game_id=player["game_id"],
                captain=player["captain"],
                mobile=player["mobile"],
                email=player["email"],
                age=player["age"],
                city=player["city"],
                college=player["college"],
                kill=0,
                rank=0,
            )
            db.add(newPlayer)
        else:
            raise Exception("Duplicate game id Found")
    db.commit()
    newTeam.players
    return {"message": newTeam}


@router.get("/getTeams", response_model=List[TeamList])
def getTeams(
    tournament_id: Optional[uuid.UUID | None] = None, db: Session = Depends(get_db)
):
    if not tournament_id:
        tournament_id = getTournamentId(db)
    data = db.query(TeamTable).filter(TeamTable.tournament_id == tournament_id).all()
    return data


@router.put("/togglePaymentReceived")
def togglePaymentReceived(team_id: uuid.UUID, db: Session = Depends(get_db)):
    team = db.query(TeamTable).filter(TeamTable.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team Not Found")
    team.payment_received = not team.payment_received
    db.commit()
    return {"message": "Payment Received Toggled"}


@router.put("/toggleIsJoined")
def toggleIsJoined(player_id: uuid.UUID, db: Session = Depends(get_db)):
    player = db.query(BgmiPlayers).filter(BgmiPlayers.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player Not Found")
    player.is_joined = not player.is_joined
    db.commit()
    return {"message": "Is Joined Toggled"}


@router.put("/toggleIsDead")
def toggleIsDead(player_id: uuid.UUID, db: Session = Depends(get_db)):
    player = db.query(BgmiPlayers).filter(BgmiPlayers.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player Not Found")
    player.is_dead = not player.is_dead
    db.commit()
    return {"message": "Is Dead Toggled"}


@router.put("/updateKill")
def toggleIsJoined(player_id: uuid.UUID, type: str, db: Session = Depends(get_db)):
    player = db.query(BgmiPlayers).filter(BgmiPlayers.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player Not Found")
    if type == "add":
        if player.kill is None:
            player.kill = 1
        else:
            player.kill += 1
    elif type == "remove":
        if player.kill is None:
            player.kill = 0
        else:
            player.kill -= 1
    db.commit()
    return {"message": "Is Joined Toggled"}


@router.get("/getPlayers", response_model=List[Player])
def getPlayers(
    team_id: Optional[uuid.UUID | None] = None, db: Session = Depends(get_db)
):
    data = db.query(BgmiPlayers)

    if team_id:
        data = data.filter(BgmiPlayers.team_id == team_id)
    data = data.order_by(BgmiPlayers.is_dead, BgmiPlayers.kill.desc()).all()

    return data


@router.get("/getTeamsRanking")
def getTeams(
    tournament_id: Optional[uuid.UUID | None] = None, db: Session = Depends(get_db)
):
    if not tournament_id:
        tournament_id = getTournamentId(db)
    data = db.query(TeamTable).filter(TeamTable.tournament_id == tournament_id).all()
    res = []
    for i in data:
        alive = 0
        total_kill = 0
        for player in i.players:
            if not player.is_dead:
                alive += 1
            total_kill += player.kill
        i.kills = total_kill
        res.append((i, alive, total_kill))
    res.sort(key=lambda x: (-x[1], -x[2], x[0].created_at))
    return [team for team, _, _ in res]
