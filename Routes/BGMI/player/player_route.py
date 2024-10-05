import random
import uuid
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
)
import requests
from pydantic import EmailStr

from Routes.BGMI.player.player_model import PlayersRegister, RegisterTeam

from sqlalchemy.orm import Session

# from schemas import PlayerGameInfo, PlayerTable
# from .player_model import GameInfo, PlayersRegister
from db import get_db
from schemas import PlayerGameInfo, PlayerTable, TeamTable
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
        f"You are successfully register with dronafoundation with team code <b style='color:red'>{teamCode}</b>. <br> <b>Note: </b> Use this code to fill other player information.<br><h2> || All the best for Tournament ||<h2> <br> <b>Best Regards<b><br><b>Drona Education Foundation</b>",
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


@router.get("/verify/{player_id}")
def verify(
    player_id: uuid.UUID, background: BackgroundTasks, db: Session = Depends(get_db)
):
    player = db.query(PlayerTable).filter(PlayerTable.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player Not Found")
    player.verified = True
    db.commit()
    background.add_task(
        send_email,
        f"Player Registration {player.player_name}",
        f"Your Information is successfully verified by our team. <h2> || All the best for Tournament ||<h2> <br> <b>Best Regards<b><br><b>Drona Education Foundation</b>",
        player.email,
    )
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
    background.add_task(
        send_email,
        f"Player Registration {player.player_name}",
        f"Information you provide for Free Fire Registration is not correct if you want to verify please fill correct information. <h2> || All the best for Tournament ||<h2> <br> <b>Best Regards<b><br><b>Drona Education Foundation</b>",
        player.email,
    )
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
        "players": team.players,
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
