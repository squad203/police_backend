from datetime import datetime
import json
from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, WebSocket
from fastapi.responses import FileResponse
from pydantic import EmailStr
from uuid import UUID
from Routes.BGMI.models_bgmi import OrganizationRegister, Player, TeamList
from schemas import (
    BgmiMatches,
    MatchTeams,
    OrganizationTable,
    TeamTable,
    BgmiPlayers,
    TournamentTable,
)
from sqlalchemy.orm import Session
from db import get_db
import requests

from utils import get_password_hash

router = APIRouter(prefix="/organization", tags=["Organization"])


@router.post("/")
def registerOrganization(reqData: OrganizationRegister, db: Session = Depends(get_db)):
    reqData.password = get_password_hash(reqData.password)
    new = OrganizationTable(**reqData.model_dump())
    db.add(new)
    db.commit()
    return new


@router.get("/")
def getOrganization(db: Session = Depends(get_db)):
    data = (
        db.query(OrganizationTable).order_by(OrganizationTable.created_at.desc()).all()
    )
    return data


@router.get("/{org_id}")
def getOrganizationById(org_id: int, db: Session = Depends(get_db)):
    data = db.query(OrganizationTable).filter(OrganizationTable.id == org_id).first()
    return data


@router.put("/{org_id}")
def updateOrganization(
    org_id: int, reqData: OrganizationRegister, db: Session = Depends(get_db)
):
    data = db.query(OrganizationTable).filter(OrganizationTable.id == org_id).first()
    if not data:
        raise HTTPException(status_code=404, detail="Organization Not Found")
    reqData.password = get_password_hash(reqData.password)
    data.name = reqData.name
    data.games = reqData.games
    data.mobile = reqData.mobile
    data.email = reqData.email
    data.address = reqData.address
    data.city = reqData.city
    data.state = reqData.state
    data.country = reqData.country
    data.password = reqData.password
    db.commit()
    return data


@router.put("/toggleActive/{org_id}")
def toggleActive(org_id: int, db: Session = Depends(get_db)):
    data = db.query(OrganizationTable).filter(OrganizationTable.id == org_id).first()
    if not data:
        raise HTTPException(status_code=404, detail="Organization Not Found")
    data.active = not data.active
    db.commit()
    return data
