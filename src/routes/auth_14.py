from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks, Request
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
    OAuth2PasswordRequestForm,
)
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.repository import users as repositories_users
from src.schemas.user import UserSchema, UserResponse, TokenSchema, RequestEmail
from src.services.auth import auth_service
from src.services.email import send_email

router = APIRouter(prefix="/auth", tags=["auth"])
get_refresh_token = HTTPBearer()


@router.post(
    "/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def signup(
    body: UserSchema,
    bt: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new user account.

    Creates a new user account with the provided email and password.

    Parameters:
        body (UserSchema): The user data to create.
        bt (BackgroundTasks): The background tasks manager.
        request (Request): The current request.
        db (AsyncSession): The database session.

    Returns:
        UserResponse: The newly created user object.

    Raises:
        HTTPException: If an account with the provided email already exists.
    """
    exist_user = await repositories_users.get_user_by_email(body.email, db)
    if exist_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Account already exists"
        )
    body.password = auth_service.get_password_hash(body.password)
    new_user = await repositories_users.create_user(body, db)
    bt.add_task(send_email, new_user.email, new_user.username, str(request.base_url))
    return new_user


@router.post("/login", response_model=TokenSchema, status_code=status.HTTP_201_CREATED)
async def login(
    body: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    """
    Authenticate a user and obtain an access token.

    Authenticates a user using their email and password, and returns an access token and refresh token.

    Parameters:
        body (OAuth2PasswordRequestForm): The user's email and password.
        db (AsyncSession): The database session.

    Returns:
        TokenSchema: The access token, refresh token, and token type.

    Raises:
        HTTPException: If the email is invalid, the email is not confirmed, or the password is invalid.
        HTTPException: If an internal server error occurs.
    """
    try:
        user = await repositories_users.get_user_by_email(body.username, db)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email"
            )
        if not user.confirmed:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not confirmed"
            )
        if not auth_service.verify_password(body.password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password"
            )
        # Generate JWT
        access_token = await auth_service.create_access_token(data={"sub": user.email})
        refresh_token = await auth_service.create_refresh_token(
            data={"sub": user.email}
        )
        await repositories_users.update_token(user, refresh_token, db)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/refresh_token", response_model=TokenSchema)
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(get_refresh_token),
    db: AsyncSession = Depends(get_db),
):
    """
    Refresh an access token using a refresh token.

    Refreshes an access token using a valid refresh token, and returns a new access token and refresh token.

    Parameters:
        credentials (HTTPAuthorizationCredentials): The refresh token.
        db (AsyncSession): The database session.

    Returns:
        TokenSchema: The new access token, refresh token, and token type.

    Raises:
        HTTPException: If the refresh token is invalid or has been revoked.
    """
    token = credentials.credentials
    email = await auth_service.decode_refresh_token(token)
    user = await repositories_users.get_user_by_email(email, db)
    if user.refresh_token != token:
        await repositories_users.update_token(user, None, db)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    access_token = await auth_service.create_access_token(data={"sub": email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": email})
    await repositories_users.update_token(user, refresh_token, db)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.get("/confirmed_email/{token}")
async def confirmed_email(token: str, db: AsyncSession = Depends(get_db)):
    """
    Confirm a user's email address.

    Confirms a user's email address using a verification token.

    Parameters:
        token (str): The verification token.
        db (AsyncSession): The database session.

    Returns:
        dict: A message indicating whether the email was confirmed or not.

    Raises:
        HTTPException: If the verification token is invalid or the user does not exist.
    """
    email = await auth_service.get_email_from_token(token)
    user = await repositories_users.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error"
        )
    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    await repositories_users.confirmed_email(email, db)
    return {"message": "Email confirmed"}


@router.post("/request_email")
async def request_email(
    body: RequestEmail,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Request email confirmation.

    Sends a confirmation email to the user's email address if it has not been confirmed yet.

    Parameters:
        body (RequestEmail): The user's email address.
        background_tasks (BackgroundTasks): The background tasks manager.
        request (Request): The current request.
        db (AsyncSession): The database session.

    Returns:
        dict: A message indicating whether the email was sent or not.

    Raises:
        None
    """
    user = await repositories_users.get_user_by_email(body.email, db)

    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    if user:
        background_tasks.add_task(
            send_email, user.email, user.username, str(request.base_url)
        )
    return {"message": "Check your email for confirmation."}


@router.post("/password-reset", status_code=status.HTTP_200_OK)
async def password_reset_request(
    body: RequestEmail,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Request a password reset.

    Sends a password reset email to the user's email address.

    Parameters:
        body (RequestEmail): The user's email address.
        background_tasks (BackgroundTasks): The background tasks manager.
        db (AsyncSession): The database session.

    Returns:
        dict: A message indicating that the password reset email has been sent.

    Raises:
        HTTPException: If the user is not found.
    """
    user = await repositories_users.get_user_by_email(body.email, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Генерація токена для скидання паролю
    reset_token = auth_service.create_email_token({"sub": body.email})

    # Відправлення листа з токеном
    background_tasks.add_task(send_email, body.email, user.username, token=reset_token)

    return {"message": "Password reset email sent"}


@router.post("/password-reset/confirm", status_code=status.HTTP_200_OK)
async def password_reset_confirm(
    token: str, new_password: str, db: AsyncSession = Depends(get_db)
):
    """
    Користувач підтверджує скидання паролю за допомогою токена.
    """
    try:
        email = await auth_service.get_email_from_token(token)
        user = await repositories_users.get_user_by_email(email, db)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Оновлення паролю
        await auth_service.update_password(email, new_password, db)
        return {"message": "Password has been reset successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token or user"
        )
