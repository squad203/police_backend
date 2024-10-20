from datetime import datetime
import random
import time
from typing import List, Literal
import uuid
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Body,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
)
from fastapi.responses import FileResponse
import requests
from pydantic import EmailStr

from Routes.BGMI.player.player_model import PlayersRegister, RegisterTeam

from sqlalchemy.orm import Session

# from schemas import PlayerGameInfo, PlayerTable
# from .player_model import GameInfo, PlayersRegister
from db import get_db
from schemas import BgmiMatches, MatchTeams, PlayerGameInfo, PlayerTable, TeamTable
from sheets import insertData
from utils import send_email

# from utils import get_password_hash

router = APIRouter(prefix="/player", tags=["Player"])


def register_team_form(
    team_name: str = Form(...),
    email: EmailStr = Form(...),
    mobile: str = Form(..., pattern=r"[6-9]\d{9}"),
    city: str = Form(...),
    college: str = Form(...),
    logo: UploadFile | None = File(None),
):
    return logo, RegisterTeam(
        **{
            "team_name": team_name,
            "email": email,
            "mobile": mobile,
            "city": city,
            "college": college,
        }
    )


def checkEnrollment(enroll: str):
    data = requests.get(
        f"https://api.airtable.com/v0/appwU8yBYoG1yhBXx/TBL_STUDENT?fields%5B%5D=name&filterByFormula=AND(IF('{enroll}' = enrollment_number,TRUE(),FALSE()))",
        headers={
            "Authorization": "Bearer patCZjaKmxphLgU7n.352e40422482c2ddc32a600c2d17d7e92b15f3eb3aa50fb884088f8d1329bb5a"
        },
    )
    if len(data.json()["records"]) == 0:
        return {"name": "", "find": False}
    return {"name": data.json()["records"][0]["fields"]["name"], "find": True}


def check_already_register(
    mobile: str, email: str, team_name: str, team_code: str, db: Session
):
    # check_already_register_player(mobile, email, db)
    team = db.query(TeamTable).filter(TeamTable.mobile == mobile).first()
    if team:
        raise HTTPException(
            status_code=422, detail="Team with same mobile number already Registered"
        )
    team = db.query(TeamTable).filter(TeamTable.email == email).first()

    if team:
        raise HTTPException(
            status_code=422, detail="Team with same email number already Registered"
        )
    team = db.query(TeamTable).filter(TeamTable.teamName == team_name).first()

    if team:
        raise HTTPException(
            status_code=422, detail="Team with same name already Registered"
        )
    team = db.query(TeamTable).filter(TeamTable.teamCode == team_code).first()

    if team:
        raise HTTPException(
            status_code=422, detail="Team with same code already Registered"
        )


def check_already_register_player(mobile: str, email: str, db: Session):

    player = db.query(PlayerTable).filter(PlayerTable.mobile == mobile).first()
    if player:
        raise HTTPException(
            status_code=422, detail="Player with same mobile number already Registered"
        )
    player = db.query(PlayerTable).filter(PlayerTable.email == email).first()
    if player:
        raise HTTPException(
            status_code=422, detail="Player with same email number already Registered"
        )


def check_already_register_player_with_id(
    mobile: str, email: str, player_id: uuid.UUID, db: Session
):

    player = (
        db.query(PlayerTable)
        .filter(PlayerTable.mobile == mobile, PlayerTable.id != player_id)
        .first()
    )
    if player:
        raise HTTPException(
            status_code=422, detail="Player with same mobile number already Registered"
        )
    player = (
        db.query(PlayerTable)
        .filter(PlayerTable.email == email, PlayerTable.id != player_id)
        .first()
    )
    if player:
        raise HTTPException(
            status_code=422, detail="Player with same email number already Registered"
        )


@router.post("/create/match")
def createMatch(
    # tournament_id: uuid.UUID = Form(...),
    match_name: str = Form(...),
    match_type: str = Form(...),
    map: str = Form(...),
    mode: str = Form(...),
    match_date: datetime = Form(...),
    db: Session = Depends(get_db),
):
    newMatch = BgmiMatches(
        id=uuid.uuid4(),
        # tournament_id=tournament_id,
        match_name=match_name,
        match_type=match_type,
        map=map,
        mode=mode,
        match_status="pending",
        match_date=match_date,
    )
    db.add(newMatch)
    db.commit()
    return newMatch


@router.get("/get_all_match")
def getAllMatch(db: Session = Depends(get_db)):
    matches = db.query(BgmiMatches).order_by(BgmiMatches.created_at.desc()).all()
    res = []

    for i in matches:
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
                "teams": teamCount,
            }
        )
    return res
    return matches


def get_team_player(team_id: str, db: Session):
    print(team_id)
    team = db.query(TeamTable).filter(TeamTable.teamCode == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team Not Found")
    return team


from fastapi import BackgroundTasks
import random


@router.get("/export_match_data/{match_id}")
def get_match_data_for_sheet(
    match_id: uuid.UUID, background: BackgroundTasks, db: Session = Depends(get_db)
):
    match = db.query(MatchTeams).filter(MatchTeams.match_id == match_id).all()
    if not match:
        raise HTTPException(status_code=404, detail="Match Not Found")
    teams = {}
    for i in match:
        if i.team_id not in teams:
            teams[i.team_id] = {
                "team_id": i.team_id,
                "team_name": i.team.teamName,
                "team_code": i.team.teamCode,
                "email": i.team.email,
                "mobile": i.team.mobile,
                "players": [],
            }
        teams[i.team_id]["players"].append(
            {
                "player_id": i.player_id,
                "player_name": i.player.player_name,
                "mobile": i.player.mobile,
                "email": i.player.email,
                "game_name": i.player.game_info[0].game_name,
                "game_id": i.player.game_info[0].game_id,
            }
        )
    teams_list = [i for i in teams.values()]
    final_data = []
    for i in teams_list:
        final_data.append(["", "", i["team_name"], "", ""])
        for j in i["players"]:
            final_data.append(
                [
                    j["player_name"],
                    j["mobile"],
                    j["email"],
                    j["game_name"],
                    j["game_id"],
                ]
            )

    background.add_task(
        insertData,
        f"{match[0].match.match_name.upper()}_{random.randint(10,999)}",
        final_data,
    )
    return final_data


@router.post("/add/team")
def addTeam(
    match_id: uuid.UUID = Form(...),
    team_ids: str = Body(...),
    # player_id: uuid.UUID = Form(...),
    db: Session = Depends(get_db),
):
    team_ids = team_ids.split(",")
    for team_id in team_ids:
        team = get_team_player(team_id, db)
        match = (
            db.query(MatchTeams)
            .filter(MatchTeams.match_id == match_id, MatchTeams.team_id == team.id)
            .first()
        )
        if match:
            print("Already Added")
            continue
        for i in team.players:
            newMatchTeam = MatchTeams(
                id=uuid.uuid4(),
                match_id=match_id,
                team_id=team.id,
                player_id=i.id,
            )
            db.add(newMatchTeam)
        db.commit()
    return {"message": "Team Added"}


@router.get("/get_match/{match_id}")
def getMatch(match_id: uuid.UUID, db: Session = Depends(get_db)):
    match = db.query(BgmiMatches).filter(BgmiMatches.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match Not Found")
    return match


@router.get("/get_match_team/{match_id}")
def getMatchTeam(match_id: uuid.UUID, db: Session = Depends(get_db)):
    match = db.query(MatchTeams).filter(MatchTeams.match_id == match_id).all()
    if not match:
        raise HTTPException(status_code=404, detail="Match Not Found")
    teams = {}
    for i in match:
        if i.team_id not in teams:
            teams[i.team_id] = []
        teams[i.team_id].append(
            {
                "player_id": i.player_id,
                "player_name": i.player.player_name,
                "mobile": i.player.mobile,
                "email": i.player.email,
                "game_name": i.player.game_info[0].game_name,
                "game_id": i.player.game_info[0].game_id,
            }
        )
    teams_list = [
        {
            "team_id": i.team_id,
            "team_name": i.team.teamName,
            "team_code": i.team.teamCode,
            "email": i.team.email,
            "mobile": i.team.mobile,
            "players": teams[i.team_id],
        }
        for i in match
    ]

    return {
        "match_id": match_id,
        "match_name": match[0].match.match_name,
        "match_type": match[0].match.match_type,
        "map": match[0].match.map,
        "mode": match[0].match.mode,
        "match_date": match[0].match.match_date,
        "teams": teams_list,
    }


@router.put("/match_kill/")
def addKill(
    type: Literal["add", "remove"],
    player_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    match = (
        db.query(MatchTeams)
        .filter(
            MatchTeams.id == player_id,
        )
        .first()
    )
    if not match:
        raise HTTPException(status_code=404, detail="Match Not Found")
    if not match.kill:
        match.kill = 1 if type == "add" else 0
    else:
        match.kill = match.kill + 1 if type == "add" else match.kill - 1
    db.commit()
    return match


@router.get("/getTeams/{matchId}/{teamsId}")
def getTeams(matchId: uuid.UUID, teamsId: str, db: Session = Depends(get_db)):
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
                "game_id": i.player.game_info[0].game_id,
                "game_name": i.player.game_info[0].game_name,
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


@router.put("/match/toggleIsDead")
def toggleIsDead(player_id: uuid.UUID, db: Session = Depends(get_db)):
    player = db.query(MatchTeams).filter(MatchTeams.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player Not Found")
    if not player.is_dead:
        player.dead_at = datetime.now()
    player.is_dead = not player.is_dead
    db.commit()
    return {"message": "Is Dead Toggled"}


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
                "teamCode": i.team.teamCode,
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
                "teamCode": team_info["teamCode"],
                "logo": team_info["logo"],
                "kill": team_info["kill"],
                "players": team_info["alive"],
                "dead_at": team_info["dead_at"] if team_info["alive"] == 0 else None,
                "is_eliminated": False if team_info["alive"] > 0 else True,
                "alive": sorted(team_info["players"], key=lambda x: x["is_dead"]),
            }
        )

    def sort_key(item):
        # Convert dead_at to a timestamp or use float('inf') if it is None
        dead_at_timestamp = (
            item["dead_at"].timestamp() if item["dead_at"] is not None else float("inf")
        )
        return (-item["players"], -item["kill"], -dead_at_timestamp)

    res.sort(key=sort_key)
    return res


@router.get("/getTeamsRankingForLast")
def getTeams(match_id: uuid.UUID, db: Session = Depends(get_db)) -> List[dict]:
    data = db.query(MatchTeams).filter(MatchTeams.match_id == match_id).all()
    res = []
    team_data = {}
    for i in data:
        if i.team_id not in team_data:
            team_data[i.team_id] = {
                "team_id": i.team_id,
                "teamName": i.team.teamName,
                "teamCode": i.team.teamCode,
                "logo": i.team.logo,
                "rank": i.rank,
                "kill": 0,
            }

        if i.kill:
            team_data[i.team_id]["kill"] += i.kill

    for team_id, team_info in team_data.items():
        res.append(
            {
                "team_id": team_id,
                "teamName": team_info["teamName"],
                "teamCode": team_info["teamCode"],
                "logo": team_info["logo"],
                "kill": team_info["kill"],
                "rank": team_info["rank"],
            }
        )

    res.sort(key=lambda x: x["rank"])
    return res


@router.get("/updateTeamsRankingByKills")
def updateTeamsRankingByKills(
    match_id: uuid.UUID, db: Session = Depends(get_db)
) -> List[dict]:
    data = db.query(MatchTeams).filter(MatchTeams.match_id == match_id).all()
    res = []
    team_data = {}

    # Collect data and accumulate kills for each team
    for i in data:
        if i.team_id not in team_data:
            team_data[i.team_id] = {
                "team_id": i.team_id,
                "teamName": i.team.teamName,
                "teamCode": i.team.teamCode,
                "logo": i.team.logo,
                "kill": 0,
            }

        if i.kill:
            team_data[i.team_id]["kill"] += i.kill

    # Convert team data to a list and sort it by kills in descending order
    sorted_teams = sorted(team_data.values(), key=lambda x: x["kill"], reverse=True)

    # Assign ranks based on the number of kills and update the database
    for idx, team_info in enumerate(sorted_teams, start=1):
        team_info["rank"] = idx

        # Update the rank in the database
        db.query(MatchTeams).filter(
            MatchTeams.team_id == team_info["team_id"], MatchTeams.match_id == match_id
        ).update({"rank": team_info["rank"]})
        res.append(
            {
                "team_id": team_info["team_id"],
                "teamName": team_info["teamName"],
                "teamCode": team_info["teamCode"],
                "logo": team_info["logo"],
                "kill": team_info["kill"],
                "rank": team_info["rank"],
            }
        )

    # Commit the changes to the database
    db.commit()

    return res


@router.put("/match/updateRank")
def updateRank(
    team_id: uuid.UUID,
    match_id: uuid.UUID,
    rank: int,
    db: Session = Depends(get_db),
):
    if rank < 1:
        rank = 1
    existing_rank = (
        db.query(MatchTeams)
        .filter(MatchTeams.rank == rank, MatchTeams.match_id == match_id)
        .all()
    )
    player = (
        db.query(MatchTeams)
        .filter(MatchTeams.team_id == team_id, MatchTeams.match_id == match_id)
        .all()
    )
    if not player:
        raise HTTPException(status_code=404, detail="Player Not Found")
    if len(existing_rank) > 1:
        for i in existing_rank:
            i.rank = player[0].rank
    for i in player:
        i.rank = rank
    db.commit()
    return {"message": "Rank Updated"}


# @router.get("/send_mail_to_team")
# def send_main_to_data(db: Session = Depends(get_db)):
#     teams = (
#         db.query(TeamTable)
#         .filter(
#             TeamTable.teamCode.in_(
#                 [
#                     "DFT7650ODA68",
#                 ]
#             )
#         )
#         .all()
#     )

#     for team in teams:
#         send_email(
#             "Team Registration",
#             f"<b>Dear Team {team.teamName}</b>, <br>Complete Your Team Registration By Clicking Bellow Button <br> <a href='https://bgmiform.netlify.app/#/team_page/{team.teamCode}'>Click to complete registration</a><br><h3> || All the best for Tournament ||<h3> <br> <b>Best Regards<b><br><b>Drona Education Foundation</b>",
#             team.email,
#         )
#         print(f"https://bgmiform.netlify.app/#/team_page/{team.teamCode}")
#         time.sleep(10)

#     return teams


@router.get("/logo/{file_name}")
def get_logo(file_name: str):
    return FileResponse(f"media/{file_name}")


@router.post("/register/team")
def register_team(
    background: BackgroundTasks,
    reqData=Depends(register_team_form),
    db: Session = Depends(get_db),
):
    logo = reqData[0]
    team: RegisterTeam = reqData[1]
    teamCode = f"DFT{team.mobile[-4:]}{team.team_name.replace(' ', '').upper()[:3]}{random.randint(10,99)}"

    check_already_register(team.mobile, team.email, team.team_name, teamCode, db)
    if logo:
        with open(f"media/{teamCode}_{logo.filename}", "wb") as f:
            f.write(logo.file.read())

    newTeam = TeamTable(
        teamName=team.team_name,
        teamCode=teamCode,
        email=team.email,
        mobile=team.mobile,
        city=team.city,
        college=team.college,
        logo=f"{teamCode}_{logo.filename}" if logo else None,
    )
    db.add(newTeam)
    db.commit()
    db.refresh(newTeam)
    background.add_task(
        send_email,
        f"Team Registration {team.team_name}",
        f"You are successfully register with dronafoundation with team code <b style='color:red'>{teamCode}</b>. <br> <b>Note: </b> Use this code to fill other player information. <a href='https://bgmiform.netlify.app/#/team_page/{teamCode}'>Click TO Register Player</a><br><h2> || All the best for Tournament ||<h2> <br> <b>Best Regards<b><br><b>Drona Education Foundation</b>",
        team.email,
    )
    return newTeam


@router.post("/register/player")
def register_player(
    background: BackgroundTasks,
    reqData: PlayersRegister,
    db: Session = Depends(get_db),
):

    checkTeam = (
        db.query(TeamTable).filter(TeamTable.teamCode == reqData.team_code).first()
    )

    if not checkTeam:
        raise HTTPException(status_code=404, detail="Team Not Found")
    if len(checkTeam.players) >= 4:
        raise HTTPException(status_code=422, detail="Team is full")

    check_already_register_player(reqData.mobile, reqData.email, db)
    player_id = uuid.uuid4()
    enroll_data = checkEnrollment(reqData.enrollNo)
    if not enroll_data["find"]:
        raise HTTPException(status_code=404, detail="Enrollment Not Found")
    newPlayer = PlayerTable(
        id=player_id,
        enrollment_no=reqData.enrollNo,
        team_code=reqData.team_code,
        player_name=enroll_data["name"],
        mobile=reqData.mobile,
        email=reqData.email,
        age=reqData.age,
        city=reqData.city,
        college=reqData.college,
        discord=reqData.discord,
    )
    newGameInfo = PlayerGameInfo(
        player_id=player_id,
        game=reqData.gameInfo.game,
        game_id=reqData.gameInfo.game_id,
        game_name=reqData.gameInfo.game_name,
    )
    db.add_all([newPlayer, newGameInfo])
    db.commit()

    background.add_task(
        send_email,
        f"Player Registration {reqData.player_name}",
        f"You are successfully register with dronafoundation in {checkTeam.teamName} Team. <h2> || All the best for Tournament ||<h2> <br> <b>Best Regards<b><br><b>Drona Education Foundation</b> ",
        reqData.email,
    )
    background.add_task(
        send_email,
        f"New Player Registration {reqData.player_name}",
        f"New Player Registered in your team with name {enroll_data['name']}<h2> || All the best for Tournament ||<h2> <br> <b>Best Regards<b><br><b>Drona Education Foundation</b> ",
        checkTeam.email,
    )
    return reqData


@router.get("/verifyEnrollment/{enroll}")
def verify_enrollment(enroll: str):
    return checkEnrollment(enroll)


@router.get("/get_all_team")
def get_all_team(completed: bool = Query(False), db: Session = Depends(get_db)):

    teams = db.query(TeamTable).all()
    res = []
    for team in teams:
        verify = True
        if len(team.players) == 0:
            verify = False
        else:

            for i in team.players:
                if not i.verified:
                    verify = False
                    break
        if completed:
            if len(team.players) >= 4:
                res.append(
                    {
                        "id": team.id,
                        "teamName": team.teamName,
                        "teamCode": team.teamCode,
                        "email": team.email,
                        "mobile": team.mobile,
                        "city": team.city,
                        "college": team.college,
                        "logo": team.logo,
                        "player": len(team.players) if team.players else 0,
                        # "players": team.players,
                        "verify": verify,
                    }
                )
        else:
            res.append(
                {
                    "id": team.id,
                    "teamName": team.teamName,
                    "teamCode": team.teamCode,
                    "email": team.email,
                    "mobile": team.mobile,
                    "city": team.city,
                    "college": team.college,
                    "logo": team.logo,
                    "player": len(team.players) if team.players else 0,
                    # "players": team.players,
                    "verify": verify,
                }
            )
    return res


@router.get("/get_all_player")
def get_all_player(team_code: str = Query(None), db: Session = Depends(get_db)):
    players = db.query(PlayerTable)
    if team_code:
        players = players.filter(PlayerTable.team_code == team_code)
    players = players.all()
    res = []
    for player in players:
        res.append(
            {
                "id": player.id,
                "enrollment_no": player.enrollment_no,
                "team_code": player.team_code,
                "player_name": player.player_name,
                "mobile": player.mobile,
                "email": player.email,
                "age": player.age,
                "city": player.city,
                "college": player.college,
                "discord": player.discord,
                "gameInfo": player.game_info,
            }
        )
    return res


@router.get("/toggleVerification/{player_id}")
def verify(
    player_id: uuid.UUID, background: BackgroundTasks, db: Session = Depends(get_db)
):
    player = db.query(PlayerTable).filter(PlayerTable.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player Not Found")
    if player.verified == False:
        background.add_task(
            send_email,
            f"Player Registration {player.player_name}",
            f"Your Information is successfully verified by our team. <h2> || All the best for Tournament ||<h2> <br> <b>Best Regards<b><br><b>Drona Education Foundation</b>",
            player.email,
        )
    if player.verified == True:
        background.add_task(
            send_email,
            f"Player Registration {player.player_name}",
            f"Information you provide for Free Fire Registration is not correct if you want to verify please fill correct information. <h2> || All the best for Tournament ||<h2> <br> <b>Best Regards<b><br><b>Drona Education Foundation</b>",
            player.email,
        )

    player.verified = not player.verified
    db.commit()
    return player


@router.get("/unVerify/{player_id}")
def unVerify(
    player_id: uuid.UUID, background: BackgroundTasks, db: Session = Depends(get_db)
):
    player = db.query(PlayerTable).filter(PlayerTable.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player Not Found")
    player.verified = False
    db.commit()

    return player


@router.put("/update/player/{player_id}")
def update_player(
    player_id: uuid.UUID, reqData: PlayersRegister, db: Session = Depends(get_db)
):
    player = db.query(PlayerTable).filter(PlayerTable.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player Not Found")
    checkTeam = (
        db.query(TeamTable).filter(TeamTable.teamCode == reqData.team_code).first()
    )
    if not checkTeam:
        raise HTTPException(status_code=404, detail="Team Not Found")
    if checkTeam.submitted:
        raise HTTPException(
            status_code=422, detail="Team Already Submitted Meet admin to do changes"
        )

    check_already_register_player_with_id(reqData.mobile, reqData.email, player_id, db)
    enroll_data = checkEnrollment(reqData.enrollNo)
    if not enroll_data["find"]:
        raise HTTPException(status_code=404, detail="Enrollment Not Found")

    player.enrollment_no = reqData.enrollNo
    player.team_code = reqData.team_code
    player.player_name = enroll_data["name"]
    player.mobile = reqData.mobile
    player.email = reqData.email
    player.age = reqData.age
    player.city = reqData.city
    player.college = reqData.college
    player.discord = reqData.discord
    db.query(PlayerGameInfo).filter(PlayerGameInfo.player_id == player.id).delete()

    newGameInfo = PlayerGameInfo(
        player_id=player.id,
        game=reqData.gameInfo.game,
        game_id=reqData.gameInfo.game_id,
        game_name=reqData.gameInfo.game_name,
    )
    db.add(newGameInfo)
    db.commit()
    return reqData


@router.get("/get_team/{team_code}")
def get_team(team_code: str, db: Session = Depends(get_db)):
    team = db.query(TeamTable).filter(TeamTable.teamCode == team_code).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team Not Found")
    team.players
    return {
        "id": team.id,
        "teamName": team.teamName,
        "teamCode": team.teamCode,
        "logo": team.logo,
        "players": [
            {
                "id": i.id,
                "player_name": i.player_name,
                "mobile": i.mobile,
                "email": i.email,
                "age": i.age,
                "city": i.city,
                "college": i.college,
                "discord": i.discord,
                "gameInfo": i.game_info,
                "verified": i.verified,
            }
            for i in team.players
        ],
        "email": team.email,
        "mobile": team.mobile,
        "city": team.city,
        "college": team.college,
        "submitted": team.submitted,
        "pending": 4 - len(team.players),
    }


@router.get("/final_add/{team_code}")
def final_add(team_code: str, db: Session = Depends(get_db)):
    team = db.query(TeamTable).filter(TeamTable.teamCode == team_code).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team Not Found")
    if len(team.players) != 4:
        raise HTTPException(status_code=422, detail="Team is not full")
    team.submitted = True
    db.commit()
    return team


@router.get("/reOpenTeam/{team_code}")
def final_add(team_code: str, db: Session = Depends(get_db)):
    team = db.query(TeamTable).filter(TeamTable.teamCode == team_code).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team Not Found")
    team.submitted = False
    db.commit()
    return team


@router.get("/get_player/{id}")
def get_player(id: uuid.UUID, db: Session = Depends(get_db)):
    player = db.query(PlayerTable).filter(PlayerTable.id == id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player Not Found")
    player.game_info
    return player


# @router.post("/")
# def add_player(player: PlayersRegister, db: Session = Depends(get_db)):
#     player.password = get_password_hash(player.password)
#     new = PlayerTable(**player.model_dump())
#     db.add(new)
#     db.commit()
#     return player


# @router.put("/{player_id}")
# def update_player(
#     player_id: int, player: PlayersRegister, db: Session = Depends(get_db)
# ):
#     player.password = get_password_hash(player.password)
#     db.query(PlayersRegister).filter(PlayersRegister.id == player_id).update(
#         player.model_dump()
#     )
#     db.commit()
#     return player


# @router.post("/add_game_info/{player_id}")
# def add_game_info(player_id: int, player: GameInfo, db: Session = Depends(get_db)):
#     new = PlayerGameInfo(**player.model_dump(), player_id=player_id)
#     db.add(new)
#     db.commit()
#     return player


# @router.get("/get_game_info/{player_id}")
# def get_game_info(player_id: int, db: Session = Depends(get_db)):
#     game_info = (
#         db.query(PlayerGameInfo).filter(PlayerGameInfo.player_id == player_id).all()
#     )
#     return game_info


# @router.get("/get_game_info_by_game/{game}/{player_id}")
# def get_game_info_by_game(game: str, player_id: int, db: Session = Depends(get_db)):
#     game_info = (
#         db.query(PlayerGameInfo)
#         .filter(PlayerGameInfo.player_id == player_id)
#         .filter(PlayerGameInfo.game == game)
#         .first()
#     )
#     return game_info


# @router.get("/get_game_info_by_game_id/{game_id}/{player_id}")
# def get_game_info_by_game_id(
#     game_id: str, player_id: int, db: Session = Depends(get_db)
# ):
#     game_info = (
#         db.query(PlayerGameInfo)
#         .filter(PlayerGameInfo.player_id == player_id)
#         .filter(PlayerGameInfo.game_id == game_id)
#         .first()
#     )
#     return game_info


# @router.put("/update_game_info/{game_info_id}")
# def update_game_info(
#     game_info_id: int, player: GameInfo, db: Session = Depends(get_db)
# ):
#     db.query(PlayerGameInfo).filter(PlayerGameInfo.id == game_info_id).update(
#         player.model_dump()
#     )
#     db.commit()
#     return player


# @router.get("/")
# def get_all_players(db: Session = Depends(get_db)):
#     players = db.query(PlayerTable).order_by(PlayerTable.created_at.desc()).all()
#     return players


# @router.get("/{player_id}")
# def get_player_by_id(player_id: int, db: Session = Depends(get_db)):
#     player = (
#         db.query(PlayerTable)
#         .join(PlayerTable.game_info)
#         .filter(PlayerTable.id == player_id)
#         .first()
#     )
#     return player
