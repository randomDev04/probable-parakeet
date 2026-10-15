from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import User, OTPCode, RefreshToken
from app.schemas import OTPRequest, OTPVerify, TokenResponse, RefreshRequest
from app.security import (
    as_utc,
    create_access_token,
    generate_otp,
    generate_refresh_token,
    hash_value,
    utcnow,
    verify_hash
)
from app.sms import send_otp_sms

router = APIRouter(prefix="/auth", tags=["auth"])

def _issue_token(db: Session, user: User) -> TokenResponse:
    raw_refresh = generate_refresh_token()
    db.add(
        RefreshToken(
            user_id= user.id,
            token_hash=hash_value(raw_refresh),
            expires_at=utcnow() + timedelta(days=settings.refresh_token_expire_days),
        )
    )
    db.commit()
    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=raw_refresh,
        expires_int=settings.access_token_expire_minutes * 60 
    )

@router.post("/otp/request", status_code=status.HTTP_202_ACCEPTED)
def request_otp(body: OTPRequest, db: Session = Depends(get_db)):
    # Rate limit per phone number (protects your SMS bill and the user)
    window_start = utcnow() - timedelta(minutes=settings.otp_request_window_minutes)
    recent = db.scalar(
        select(func.count())
        .select_from(OTPCode)
        .where(OTPCode.phone_number == body.phone_number, OTPCode.created_at >= window_start)
    )
    print(f"Mein pagal ho gaya hu -> {recent}")
    if recent >= settings.otp_max_requests_per_window:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Too many OTP requests. Try again later.")

    # Only the newest OTP should work
    db.execute(
        update(OTPCode)
        .where(OTPCode.phone_number == body.phone_number, OTPCode.consumed.is_(False))
        .values(consumed=True)
    )

    code = generate_otp()
    db.add(
        OTPCode(
            phone_number=body.phone_number,
            code_hash=hash_value(f"{body.phone_number}:{code}"),
            expires_at=utcnow()+ timedelta(minutes=settings.otp_expire_minutes)
        )
    )
    db.commit()
    send_otp_sms(body.phone_number, code)
    return {"message": "OTP sent", "expires_in":settings.otp_expire_minutes * 60}


@router.post("/otp/verify", response_model=TokenResponse)
def verify_otp(body:OTPVerify, db:Session = Depends(get_db)):
    invalid = HTTPException(status.HTTP_400_BAD_REQUEST, "Invalide or expired OTP")

    otp = db.scalar(
        select(OTPCode)
        .where(OTPCode.phone_number == body.phone_number, OTPCode.consumed.is_(False))
        .order_by(OTPCode.created_at.desc())
        .limit(1)
        .with_for_update() # stops two simulataneous requests using the same OTP
    )

    if not otp or as_utc(otp.expires_at) < utcnow():
        raise invalid
    if otp.attempts >= settings.otp_max_attempts:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Too many wrong attempts. Request a new OTP.")

    otp.attempts += 1
    if not verify_hash(f"{body.phone_number}:{body.otp}", otp.code_hash):
        db.commit() # save the failed attempts
        raise invalid

    otp.consumed = True

    # Login and sign-up are teh same step: create the user on first login
    user = db.scalar(select(User).where(User.phone_number == body.phone_number))
    if not user :
        user = User(phone_number = body.phone_number)
        db.add(user)
        db.flush() # assigns user.id
    if not user.is_active:
        db.commit()
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account disabled")

    return _issue_token(db, user)

@router.post("/refresh", response_model=TokenResponse)
def refresh_token(body: RefreshRequest, db: Session = Depends(get_db)):
    invalid = HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token")

    token = db.scalar(
        select(RefreshToken)
        .where(RefreshToken.token_hash == hash_value(body.refresh_token))
        .with_for_update()
    )

    if not token:
        raise invalid

    if token.revoked:
        # An already-used token came back: it was probably stolen.
        # Log the user out on every device to be safe
        db.execute(
            update(RefreshToken).where(RefreshToken.user_id == token.user_id).values(revoked=True)
        )
        db.commit()
        raise invalid

    if as_utc(token.expires_at) < utcnow():
        raise invalid

    user = db.get(User, token.user_id)
    if not user or not user.is_active:
        raise invalid

    token.revoked = True # rotation: each refresh token works exactly once
    return _issue_token(db, user)

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(body: RefreshRequest, db: Session = Depends(get_db)):
    db.execute(
        update(RefreshToken)
        .where(RefreshToken.token_hash == hash_value(body.refresh_token))
        .values(revoked=True)
    )
    db.commit()