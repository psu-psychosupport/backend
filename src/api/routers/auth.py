from typing import Optional

from fastapi import APIRouter, Depends, Response
from fastapi.security import HTTPBearer

from ..auth import TokenTypes
from ...api import auth
from ...api.dependencies import (
    ICurrentUser,
    get_current_user,
    get_current_user_from_email_token,
    get_email_service,
    get_user_from_password_token,
    get_user_service,
    validate_auth_user,
    validate_user_register,
)
from .. import exceptions
from ...models.schemas.auth import ChangeEmailPayload, RequestEmail, ChangePasswordPayload, Token
from ...models.schemas.update import UserUpdate
from ...models.schemas.users import UserCreate, UserSchema
from ...services.email_sender_service import EmailSenderService
from ...services.user_service import UserService

__all__ = ("router",)

router = APIRouter(tags=["Users"], dependencies=[Depends(HTTPBearer(auto_error=False))])


@router.post("/signup")
async def signup(
    user_create: UserCreate = Depends(validate_user_register),
    user_service: UserService = Depends(get_user_service),
    email_service: EmailSenderService = Depends(get_email_service),
):
    user = await user_service.add_user(user_create)
    email_service.send_verification_email(user, user.email)


@router.get("/resend/{user_id}")
async def resend_verification(
    user_id: int,
    user_service: UserService = Depends(get_user_service),
    email_service: EmailSenderService = Depends(get_email_service),
):
    user = await user_service.get_user(user_id=user_id)
    if user is None:
        raise exceptions.user_not_found
    if user.is_verified:
        raise exceptions.user_already_verified

    email_service.send_verification_email(user)


@router.post("/change-email")
async def email_verification(
    payload: ChangeEmailPayload,
    user_service: UserService = Depends(get_user_service),
):
    user, email = await get_current_user_from_email_token(payload.token, user_service)
    await user_service.update_user(user.id, UserUpdate(email=email, is_verified=True))


@router.post("/signin")
async def signin(
    response: Response,
    as_admin: bool = False,
    user: UserSchema = Depends(validate_auth_user)
) -> Token:
    if as_admin and not user.is_admin:
        raise exceptions.missing_permissions

    access_token = auth.create_access_token(user.id)
    refresh_token = auth.create_refresh_token(user.id)
    token = Token(
        access_token=access_token["token"],
        refresh_token=refresh_token["token"],
    )

    response.set_cookie(
        "access_token",
        token.access_token,
        max_age=refresh_token["max_age"],
        secure=True,
        samesite="none",
        httponly=True
    )
    response.set_cookie(
        "refresh_token",
        token.refresh_token,
        max_age=refresh_token["max_age"],
        secure=True,
        samesite="none",
        httponly=True
    )

    return token


@router.post("/refresh", response_model_exclude_none=True)
async def auth_refresh_jwt(
    response: Response,
    user: UserSchema = Depends(get_current_user(TokenTypes.REFRESH)),
) -> Token:
    access_token = auth.create_access_token(user.id)
    token = Token(access_token=access_token["token"])

    response.set_cookie(
        "access_token", token.access_token, max_age=access_token["max_age"]
    )

    return token

@router.post("/request-email-change")
async def request_email_change(
    request_email: RequestEmail,
    user: Optional[UserSchema] = Depends(get_current_user(required=False)),
    user_service: UserService = Depends(get_user_service),
    email_service: EmailSenderService = Depends(get_email_service),
):
    email = request_email.email
    if user is not None and user.email == email:
        raise exceptions.same_email_address

    _user = await user_service.get_user(email=email)
    if user is not None and _user is not None:
        raise exceptions.email_address_already_taken

    email_service.send_verification_email(_user.id, email)


@router.post("/request-password-change")
async def request_password_change(
    user: ICurrentUser,
    request_email: Optional[RequestEmail] = None,
    user_service: UserService = Depends(get_user_service),
    email_service: EmailSenderService = Depends(get_email_service),
):
    user = await user_service.get_user(email=request_email.email) if request_email else user
    if user is None:
        raise exceptions.user_not_found

    email_service.send_reset_password_email(user)


@router.post("/change-password")
async def change_user_password(
    payload: ChangePasswordPayload,
    user_service: UserService = Depends(get_user_service),
):
    user = await get_user_from_password_token(payload.token, user_service)
    await user_service.update_user(user.id, UserUpdate(hashed_password=auth.get_password_hash(payload.password)))
