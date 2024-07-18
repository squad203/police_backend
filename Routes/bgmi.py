import json
from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import EmailStr
from Routes.models_bgmi import Player, TeamList
from schemas import BgmiMatches, TeamTable, BgmiPlayers, TournamentTable
from sqlalchemy.orm import Session
from db import get_db
import requests

router = APIRouter(prefix="/bgmi", tags=["BGMI"])


def getTournamentId(db: Session):
    data = db.query(TournamentTable).filter(TournamentTable.status == "active").first()
    if not data:
        raise HTTPException(status_code=404, detail="No Active Tournament Found")
    return data.id


@router.post("/create/tournament")
def createTournament(
    name: str = Form(...),
    org_name: str = Form(...),
    team_type: str = Form(...),
    city: str = Form(...),
    max_teams: int = Form(...),
    pool_prize: int = Form(...),
    game: str = Form(...),
    organizer_logo: UploadFile | None = Form(None),
    tournament_logo: UploadFile | None = Form(None),
    entry_fee: str = Form(...),
    db: Session = Depends(get_db),
):
    id = uuid.uuid4()
    if organizer_logo:
        with open(f"media/{id}_{organizer_logo.filename}", "wb") as f:
            f.write(organizer_logo.file.read())
    if tournament_logo:
        with open(f"media/{id}_{tournament_logo.filename}", "wb") as f:
            f.write(tournament_logo.file.read())
    newTournament = TournamentTable(
        id=id,
        name=name,
        org_name=org_name,
        team_type=team_type,
        city=city,
        max_teams=max_teams,
        pool_prize=pool_prize,
        game=game,
        organizer_logo=id + "_" + organizer_logo.filename if organizer_logo else "",
        tournament_logo=id + "_" + tournament_logo.filename if tournament_logo else "",
        entry_fee=entry_fee,
        status="active",
    )
    db.add(newTournament)
    db.commit()
    return {"message": "Tournament Created"}


@router.get("/getTournaments")
def getTournament(db: Session = Depends(get_db)):
    data = db.query(TournamentTable).all()
    if not data:
        raise HTTPException(status_code=404, detail="No Active Tournament Found")
    res = []
    for i in data:
        res.append(
            {
                "id": i.id,
                "name": i.name,
                "org_name": i.org_name,
                "team_type": i.team_type,
                "city": i.city,
                "max_teams": i.max_teams,
                "pool_prize": i.pool_prize,
                "game": i.game,
                "organizer_logo": i.organizer_logo,
                "tournament_logo": i.tournament_logo,
                "entry_fee": i.entry_fee,
                "status": i.status,
                "teams": len(i.team),
            }
        )
    return res


@router.post("/create/match")
def createMatch(
    tournament_id: uuid.UUID = Form(...),
    match_name: str = Form(...),
    match_type: str = Form(...),
    map: str = Form(...),
    mode: str = Form(...),
    match_date: str = Form(...),
    db: Session = Depends(get_db),
):
    newMatch = BgmiMatches(
        id=uuid.uuid4(),
        tournament_id=tournament_id,
        match_name=match_name,
        match_type=match_type,
        map=map,
        mode=mode,
        match_status="pending",
        match_date=match_date,
    )
    db.add(newMatch)
    db.commit()
    return {"message": "Match Created"}


@router.get("/getMatches")
def getMatches(
    tournament_id: Optional[uuid.UUID | None] = None, db: Session = Depends(get_db)
):
    if not tournament_id:
        data = db.query(BgmiMatches).all()
    else:
        data = (
            db.query(BgmiMatches)
            .filter(BgmiMatches.tournament_id == tournament_id)
            .all()
        )
    res = []
    for i in data:
        res.append(
            {
                "id": i.id,
                "match_name": i.match_name,
                "match_type": i.match_type,
                "map": i.map,
                "mode": i.mode,
                "match_date": i.match_date,
                "match_status": i.match_status,
                "tournament": i.tournament.name,
            }
        )
    return res


def checkEnrollment(enroll: str):
    data = requests.get(
        f"https://api.airtable.com/v0/appwU8yBYoG1yhBXx/TBL_STUDENT?fields%5B%5D=enrollment_number&filterByFormula=FIND('{enroll}',enrollment_number)",
        headers={
            "Authorization": "Bearer patCZjaKmxphLgU7n.352e40422482c2ddc32a600c2d17d7e92b15f3eb3aa50fb884088f8d1329bb5a"
        },
    )
    if len(data.json()["records"]) == 0:
        return False
    return True


@router.post("/register")
async def register(
    tournament_id: str = Form(...),
    teamName: str = Form(...),
    logo: UploadFile | None = File(None),
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
        tournament_id=tournament_id,
        teamName=teamName,
        email=email,
        mobile=mobile,
        city=city,
        college=college,
        logo=teamId + "_" + logo.filename if logo else "",
        rank=0,
    )
    db.add(newTeam)
    gameId = set()
    if logo:
        with open(f"media/{teamId}_{logo.filename}", "wb") as f:
            f.write(logo.file.read())
    for player in playersJson:
        if not checkEnrollment(player["enrollNo"]):
            raise HTTPException(422, "Invalid Enrollment Number")
        if player["game_id"] not in gameId:
            newPlayer = BgmiPlayers(
                id=uuid.uuid4(),
                team_id=teamId,
                tournament_id=tournament_id,
                player_name=player["player_name"],
                game_id=player["game_id"],
                captain=player["captain"],
                mobile=player["mobile"],
                enrollNo=player["enrollNo"],
                email=player["email"],
                age=player["age"],
                city=player["city"],
                college=player["college"],
                kill=0,
                rank=0,
            )
            db.add(newPlayer)
            gameId.add(player["game_id"])
        else:
            raise HTTPException(422, "Duplicate game id Found")
    db.commit()
    newTeam.players
    return {"message": newTeam}


@router.get("/getTeams")
def getTeams(
    tournament_id: Optional[uuid.UUID | None] = None, db: Session = Depends(get_db)
):
    if not tournament_id:
        data = db.query(TeamTable).order_by(TeamTable.created_at).all()
    else:
        data = (
            db.query(TeamTable)
            .filter(TeamTable.tournament_id == tournament_id)
            .order_by(TeamTable.created_at)
            .all()
        )
    res = []
    for i in data:
        total_kill = 0
        verify = True
        for player in i.players:
            if player.verified == False:
                verify = False
            total_kill += player.kill
        res.append(
            {
                "id": i.id,
                "teamName": i.teamName,
                "email": i.email,
                "mobile": i.mobile,
                "city": i.city,
                "college": i.college,
                "logo": i.logo,
                "rank": i.rank,
                "tournament": i.tournament.name,
                "payment_received": i.payment_received,
                "players_count": len(i.players),
                "verify": verify,
                "players": i.players,
                "kills": total_kill,
            }
        )
    return res


@router.put("/togglePaymentReceived")
def togglePaymentReceived(team_id: uuid.UUID, db: Session = Depends(get_db)):

    team = db.query(TeamTable).filter(TeamTable.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team Not Found")
    team.payment_received = not team.payment_received
    db.commit()
    return {"message": "Payment Received Toggled"}


@router.put("/toggleVerification")
def toggleVerification(player_id: uuid.UUID, db: Session = Depends(get_db)):
    player = db.query(BgmiPlayers).filter(BgmiPlayers.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player Not Found")
    player.verified = not player.verified
    db.commit()
    return {"message": "Is Joined Toggled"}


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
