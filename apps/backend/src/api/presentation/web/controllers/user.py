import time
from dataclasses import dataclass
from typing import Annotated
from uuid import uuid4

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Cookie, Depends
from starlette import status
from starlette.responses import Response

from api.application.exceptions.user import (
    InvalidCredentialsError,
    UsernameAlreadyExistsError,
)
from api.presentation.web.controllers.schemas.requests.user import UserRequestSchema

router = APIRouter(tags=["Users"], route_class=DishkaRoute)

MOCK_DB = {}
SESSION_IDS = {}


@dataclass
class UserDBModel:
    user_id: int
    username: str
    hashed_password: str


class Argon2Hasher:
    def __init__(
        self,
        salt: bytes = bytes("SomeSalt", "UTF-8"),
        hasher: PasswordHasher = PasswordHasher(),
    ):
        self._hasher = hasher
        self._salt = salt

    def hash_password(self, raw_password: str) -> str:
        return self._hasher.hash(
            password=raw_password,
            salt=self._salt,
        )

    def verify(self, hashed_password: str, raw_password: str):
        try:
            return self._hasher.verify(hashed_password, raw_password)
        except VerifyMismatchError:
            raise InvalidCredentialsError


def get_hasher() -> Argon2Hasher:
    return Argon2Hasher()


def check_username(username: str):
    for v in MOCK_DB.values():
        if v["username"] == username:
            raise UsernameAlreadyExistsError(username)


def insert_user(
    username: str,
    hashed_password: str,
) -> int:
    user_id = len(MOCK_DB) + 1

    MOCK_DB[user_id] = {
        "username": username,
        "hashed_password": hashed_password,
    }

    return user_id


def get_user_by_username(username: str) -> UserDBModel | None:
    for user_id, data in MOCK_DB.items():
        db_username = data["username"]
        hashed_password = data["hashed_password"]

        if db_username == username:
            return UserDBModel(
                user_id=user_id,
                username=username,
                hashed_password=hashed_password,
            )


def set_session_id(username: str) -> str:
    session_id = uuid4().hex

    SESSION_IDS[session_id] = {
        "username": username,
        "login_at": time.time(),
    }

    return session_id


def delete_session_id(session_id: str) -> None:
    SESSION_IDS.pop(session_id, None)


@router.post(
    "/users",
    status_code=status.HTTP_201_CREATED,
    responses={},
)
async def register_user(
    user: UserRequestSchema,
    hasher: Argon2Hasher = Depends(get_hasher),
):
    # TODO: check password strength

    check_username(user.username)
    user_id = insert_user(user.username, hasher.hash_password(user.secret))

    return {"user_id": user_id}


@router.post(
    "/users/login",
    status_code=status.HTTP_200_OK,
    responses={},
)
async def login_user(
    response: Response,
    user: UserRequestSchema,
    hasher: Argon2Hasher = Depends(get_hasher),
):
    db_user = get_user_by_username(user.username)
    if not db_user:
        raise InvalidCredentialsError

    hasher.verify(db_user.hashed_password, user.secret)

    session_id = set_session_id(db_user.username)

    response.set_cookie("session_id", session_id, httponly=True)  # TODO: max_age

    return {"result": "Success"}


@router.post(
    "/users/logout",
    status_code=status.HTTP_200_OK,
    responses={},
)
async def logout_user(
    response: Response,
    session_id: Annotated[str | None, Cookie()] = None,
):
    delete_session_id(session_id)

    response.delete_cookie(session_id)

    return {"result": "Success"}
