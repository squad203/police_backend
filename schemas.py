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

from sqlalchemy.dialects.postgresql import ARRAY


class UserTable(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    full_name = Column(String)
    email = Column(String, unique=True, index=True)
    disabled = Column(Boolean, server_default=text("false"))
    hashed_password = Column(String)
    permissions = Column(String, server_default="*")


class OrganizationTable(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    email = Column(String, unique=True)
    mobile = Column(String, unique=True)
    games = Column(ARRAY(String))
    address = Column(String)
    city = Column(String)
    state = Column(String)
    country = Column(String)
    logo_file = Column(String)
    active = Column(Boolean, server_default=text("true"))
    password = Column(String)
    permissions = Column(String, server_default="*")

    created_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))
    updated_at = Column(
        TIMESTAMP(timezone=True), server_default=text("now()"), onupdate=text("now()")
    )


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

    # team = relationship("TeamTable", back_populates="tournament")
    matches = relationship("BgmiMatches", back_populates="tournament")
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
    # mvp_player_id = Column(
    #     UUID(as_uuid=True), ForeignKey("bgmi_players.id"), nullable=True
    # )
    match_status = Column(String, server_default=text("pending"))
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))

    tournament = relationship("TournamentTable", back_populates="matches")
    matchTeam = relationship("MatchTeams", back_populates="match")


class MatchTeams(Base):
    __tablename__ = "match_players"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    match_id = Column(UUID(as_uuid=True), ForeignKey("bgmi_matches.id"))
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"))
    # player_id = Column(UUID(as_uuid=True), ForeignKey("bgmi_players.id"))
    is_joined = Column(Boolean, server_default=text("false"))
    kill = Column(Integer, server_default=text("0"))
    rank = Column(Integer, server_default=text("0"))
    is_dead = Column(Boolean, server_default=text("false"))
    dead_at = Column(DateTime, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))

    match = relationship("BgmiMatches", back_populates="matchTeam")
    # team = relationship("TeamTable", back_populates="match")


class PlayerGameInfo(Base):
    __tablename__ = "player_game_info"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(UUID(as_uuid=True), ForeignKey("players.id"))
    game = Column(String)
    game_id = Column(String, unique=True)
    game_name = Column(String, unique=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))
    updated_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))

    player = relationship("PlayerTable", back_populates="game_info")


class TeamTable(Base):
    __tablename__ = "teams"
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    # tournament_id = Column(UUID(as_uuid=True), ForeignKey("tournaments.id"))
    teamName = Column(String)
    teamCode = Column(String, nullable=True, unique=True)
    email = Column(String)
    mobile = Column(String)
    city = Column(String)
    college = Column(String)
    logo = Column(String)
    rank = Column(Integer)
    kills = Column(Integer)
    payment_received = Column(Boolean, server_default=text("false"))
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))

    # tournament = relationship("TournamentTable", back_populates="team")
    # match = relationship("MatchTeams", back_populates="team")
    players = relationship("PlayerTable", back_populates="team")


class PlayerTable(Base):
    __tablename__ = "players"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    team_code = Column(String, ForeignKey("teams.teamCode"), nullable=True)
    player_name = Column(String)
    enrollment_no = Column(String, unique=True)
    mobile = Column(String, unique=True)
    email = Column(String, unique=True)
    age = Column(Integer)
    city = Column(String)
    college = Column(String)
    discord = Column(String)
    password = Column(String)
    verified = Column(Boolean, server_default=text("false"))
    active = Column(Boolean, server_default=text("false"))
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))
    logged_in = Column(Boolean, server_default=text("false"))

    game_info = relationship("PlayerGameInfo", back_populates="player")
    team = relationship("TeamTable", back_populates="players")
