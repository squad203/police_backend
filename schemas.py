import uuid
from sqlalchemy import (
    DateTime,
    TIMESTAMP,
    UUID,
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
    text,
)
from sqlalchemy.orm import relationship
from db import Base

from sqlalchemy import ARRAY


class UserTable(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    full_name = Column(String)
    email = Column(String, unique=True, index=True)
    disabled = Column(Boolean, server_default=text("false"))
    hashed_password = Column(String)
    permissions = Column(String, server_default="*")


class TournamentTable(Base):
    __tablename__ = "tournaments"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    name = Column(String, unique=True, index=True)
    team_type = Column(String)
    city = Column(String)
    max_teams = Column(Integer)
    pool_prize = Column(Integer)
    game = Column(String)
    org_name = Column(String)
    organizer_logo = Column(String)
    tournament_logo = Column(String)
    entry_fee = Column(String)
    entry_fee = Column(String)
    status = Column(String)
    start_date = Column(DateTime)

    created_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))
    updated_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))

    team = relationship("TeamTable", back_populates="tournament")
    matches = relationship("BgmiMatches", back_populates="tournament")
    players = relationship("BgmiPlayers", back_populates="tournament")
    # end_date = Column(DateTime)
    # mode = Column(String)
    # map = Column(String)
    # first_prize = Column(Integer)
    # second_prize = Column(Integer)
    # third_prize = Column(Integer)
    # total_teams = Column(Integer)
    # total_players = Column(Integer)


class BgmiMatches(Base):
    __tablename__ = "bgmi_matches"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    tournament_id = Column(UUID(as_uuid=True), ForeignKey("tournaments.id"))
    match_name = Column(String)
    match_type = Column(String)
    map = Column(String)
    mode = Column(String)
    match_date = Column(DateTime)
    match_status = Column(String, server_default=text("pending"))
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))

    tournament = relationship("TournamentTable", back_populates="matches")


class BgmiPlayers(Base):
    __tablename__ = "bgmi_players"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    tournament_id = Column(UUID(as_uuid=True), ForeignKey("tournaments.id"))

    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"))
    player_name = Column(String)
    game_id = Column(String)
    captain = Column(Boolean, server_default=text("false"))
    mobile = Column(String)
    email = Column(String)
    age = Column(Integer)
    enrollNo = Column(String)
    city = Column(String)
    college = Column(String)
    is_joined = Column(Boolean, server_default=text("false"))
    kill = Column(Integer, server_default=text("0"))
    rank = Column(Integer, server_default=text("0"))
    is_dead = Column(Boolean, server_default=text("false"))
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))
    verified = Column(Boolean, server_default=text("false"))
    team = relationship("TeamTable", back_populates="players")
    tournament = relationship("TournamentTable", back_populates="players")


class TeamTable(Base):
    __tablename__ = "teams"
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    tournament_id = Column(UUID(as_uuid=True), ForeignKey("tournaments.id"))
    teamName = Column(String)
    email = Column(String)
    mobile = Column(String)
    city = Column(String)
    college = Column(String)
    logo = Column(String)
    rank = Column(Integer)
    kills = Column(Integer)
    payment_received = Column(Boolean, server_default=text("false"))
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))
    players = relationship(
        "BgmiPlayers", back_populates="team", order_by="BgmiPlayers.player_name"
    )

    tournament = relationship("TournamentTable", back_populates="team")
