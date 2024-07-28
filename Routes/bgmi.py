from datetime import datetime
import json
from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, WebSocket
from fastapi.responses import FileResponse
from pydantic import EmailStr
from uuid import UUID
from Routes.models_bgmi import Player, TeamList
from schemas import BgmiMatches, MatchTeams, TeamTable, BgmiPlayers, TournamentTable
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


@router.post("/match/addPlayers")
def add_players_to_match(
    match_id: uuid.UUID = Form(...),
    team_ids: List[uuid.UUID] = Form(...),
    db: Session = Depends(get_db),
):
    for team_id in team_ids:
        team = db.query(TeamTable).filter(TeamTable.id == team_id).first()
        db.add(MatchTeams(id=uuid.uuid4(), match_id=match_id, player_id=team_id))
    db.commit()
    return {"message": "Players Added to Match"}


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
        teamCount = (
            db.query(MatchTeams.team_id.distinct())
            .filter(MatchTeams.match_id == i.id)
            .count()
        )
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
                "teams": teamCount,
            }
        )
    return res


@router.post("/addTeamInMatch/{match_id}/{team_id}")
def addTeamInMatch(team_id: UUID, match_id: UUID, db: Session = Depends(get_db)):

    inMatch = db.query(MatchTeams).filter(MatchTeams.team_id == team_id)
    if inMatch.first():
        inMatch.delete()
        db.commit()
        return {"message": "Team Removed from Match"}
    player = db.query(BgmiPlayers).filter(BgmiPlayers.team_id == team_id).all()
    if not player:
        raise HTTPException(status_code=404, detail="Team Not Found")
    for i in player:
        db.add(MatchTeams(match_id=match_id, team_id=team_id, player_id=i.id))

    db.commit()

    return {"message": "Team Added to Match"}


@router.get("/getMatchPlayers/{match_id}")
def getMatchPlayers(match_id: UUID, db: Session = Depends(get_db)):
    data = db.query(MatchTeams).filter(MatchTeams.match_id == match_id).all()
    res = []
    team_data = {}
    for i in data:
        if i.team_id not in team_data:
            team_data[i.team_id] = {
                "team_id": i.team_id,
                "teamName": i.team.teamName,
                "logo": i.team.logo,
                "players": [],
            }
        team_data[i.team_id]["players"].append(
            {
                "id": i.id,
                "player_id": i.player_id,
                "player_name": i.player.player_name,
                "game_id": i.player.game_id,
                "captain": i.player.captain,
                "is_joined": i.is_joined,
                "kill": i.kill,
                "rank": i.rank,
                "is_dead": i.is_dead,
            }
        )

    for team_id, team_info in team_data.items():
        res.append(
            {
                "team_id": team_id,
                "teamName": team_info["teamName"],
                "logo": team_info["logo"],
                "players": sorted(team_info["players"], key=lambda x: x["player_name"]),
            }
        )

    return res


@router.get("/getTeams/{matchId}/{teamsId}")
def getTeams(matchId: UUID, teamsId: str, db: Session = Depends(get_db)):
    teamsId = teamsId.split(",")
    data = []
    if matchId:
        data = (
            db.query(MatchTeams)
            .filter(MatchTeams.match_id == matchId, MatchTeams.team_id.in_(teamsId))
            .all()
        )

    res = []
    team_data = {}
    for i in data:
        if i.team_id not in team_data:
            team_data[i.team_id] = {
                "team_id": i.team_id,
                "teamName": i.team.teamName,
                "logo": i.team.logo,
                "players": [],
            }
        team_data[i.team_id]["players"].append(
            {
                "id": i.id,
                "plater_id": i.player_id,
                "player_name": i.player.player_name,
                "game_id": i.player.game_id,
                "captain": i.player.captain,
                "is_joined": i.is_joined,
                "kill": i.kill,
                "rank": i.rank,
                "is_dead": i.is_dead,
            }
        )

    print(team_data)

    for team_id, team_info in team_data.items():
        res.append(
            {
                "team_id": team_id,
                "teamName": team_info["teamName"],
                "logo": team_info["logo"],
                "players": sorted(team_info["players"], key=lambda x: x["player_name"]),
            }
        )
    return sorted(res, key=lambda x: x["teamName"])


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


@router.get("/verifyEnrollment/{enroll}")
def getTeams(enroll: str):
    return checkEnrollment(enroll)


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
        logo=str(teamId) + "_" + logo.filename if logo else "",
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


@router.get("/logo/{file_name}")
def get_logo(file_name: str):
    return FileResponse(f"media/{file_name}")


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
        match_ = db.query(MatchTeams).filter(MatchTeams.team_id == i.id).all()
        match = []
        match_id = set()
        if match_:
            for j in match_:
                if j.match_id not in match_id:
                    match_id.add(j.match_id)
                    match.append(
                        {
                            "match_id": j.match_id,
                            "match_name": j.match.match_name,
                            "match_date": j.match.match_date,
                        }
                    )
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
                "match": match,
                "match_id": match_id,
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
    player = db.query(MatchTeams).filter(MatchTeams.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player Not Found")
    player.is_joined = not player.is_joined
    db.commit()
    return {"message": "Is Joined Toggled"}


@router.put("/toggleIsDead")
def toggleIsDead(player_id: uuid.UUID, db: Session = Depends(get_db)):
    player = db.query(MatchTeams).filter(MatchTeams.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player Not Found")
    if not player.is_dead:
        player.dead_at = datetime.now()
    player.is_dead = not player.is_dead
    db.commit()
    return {"message": "Is Dead Toggled"}


@router.put("/updateKill")
def toggleIsJoined(player_id: uuid.UUID, type: str, db: Session = Depends(get_db)):
    player = db.query(MatchTeams).filter(MatchTeams.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player Not Found")
    if type == "add":
        if player.kill is None:
            player.kill = 10
        else:
            player.kill += 1
    elif type == "remove":
        if player.kill is None:
            player.kill = 0
        else:
            player.kill -= 1
    db.commit()
    return {"message": "Is Joined Toggled"}


@router.get("/getPlayers/", response_model=List[Player])
def getPlayers(match_id: uuid.UUID = None, db: Session = Depends(get_db)):
    data = db.query(MatchTeams)

    if match_id:
        data = data.filter(MatchTeams.match_id == match_id)
    data = data.order_by(MatchTeams.dead_at, MatchTeams.kill.desc()).all()
    res = []
    for i in data:
        res.append(
            Player(
                id=i.id,
                player_name=i.player.player_name,
                game_id=i.player.game_id,
                is_dead=i.is_dead,
                kill=i.kill,
                # captain=i.player.captain,
                # mobile=i.player.mobile,
                # email=i.player.email,
                # age=i.player.age,
                # city=i.player.city,
                # college=i.player.college,
                # is_joined=i.is_joined,
            )
        )
    return res


@router.get("/getTeamsRanking")
def getTeams(match_id: uuid.UUID, db: Session = Depends(get_db)) -> List[dict]:
    data = db.query(MatchTeams).filter(MatchTeams.match_id == match_id).all()
    res = []
    team_data = {}
    for i in data:
        if i.team_id not in team_data:
            team_data[i.team_id] = {
                "team_id": i.team_id,
                "teamName": i.team.teamName,
                "logo": i.team.logo,
                "rank": i.team.rank,
                "players": [],
                "alive": 0,
                "dead_at": None,
                "kill": 0,
            }
        if not i.is_dead:
            team_data[i.team_id]["alive"] += 1
        else:
            if team_data[i.team_id]["dead_at"] is None:
                team_data[i.team_id]["dead_at"] = i.dead_at
            else:
                team_data[i.team_id]["dead_at"] = max(
                    i.dead_at, team_data[i.team_id]["dead_at"]
                )
        if i.kill:
            team_data[i.team_id]["kill"] += i.kill
        team_data[i.team_id]["players"].append(
            {
                "is_dead": i.is_dead,
            }
        )

    for team_id, team_info in team_data.items():
        res.append(
            {
                "team_id": team_id,
                "teamName": team_info["teamName"],
                "logo": team_info["logo"],
                "kill": team_info["kill"],
                "rank": team_info["rank"],
                "players": team_info["alive"],
                "dead_at": team_info["dead_at"],
                "is_eliminated": False if team_info["alive"] > 0 else True,
                "alive": sorted(team_info["players"], key=lambda x: x["is_dead"]),
            }
        )

    def sort_key(item):
        # Convert dead_at to a timestamp or use float('inf') if it is None
        dead_at_timestamp = (
            item["dead_at"].timestamp() if item["dead_at"] is not None else float("inf")
        )
        return (-item["players"], -dead_at_timestamp, -item["kill"])

    res.sort(key=sort_key)
    return res


# @router.websocket("/ws")
# async def websocket_endpoint(websocket: WebSocket, db: Session = Depends(get_db)):
#     await websocket.accept()
#     while True:

#         data = await websocket.receive_text()
#         await websocket.send_json()
