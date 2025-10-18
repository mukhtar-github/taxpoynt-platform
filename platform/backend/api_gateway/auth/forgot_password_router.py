"""Forgot password API router."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    success: bool
    message: str


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(request: ForgotPasswordRequest) -> ForgotPasswordResponse:
    # TODO: integrate with real email/password reset workflow. For now, respond as though
    # the link has been sent even if the account does not exist, to avoid user enumeration.
    return ForgotPasswordResponse(
        success=True,
        message="If this email exists on TaxPoynt, a secure reset link will arrive shortly.",
    )

