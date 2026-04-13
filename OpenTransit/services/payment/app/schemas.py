"""Pydantic schemas for the payment service."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.models import PaymentProvider, TransactionStatus


class PaymentInitiateRequest(BaseModel):
    user_id: UUID
    ticket_id: UUID | None = None
    amount: Decimal = Field(gt=0, decimal_places=2)
    currency: str = Field(min_length=3, max_length=3)
    provider: PaymentProvider = PaymentProvider.sandbox
    # Provider-specific token (e.g. Stripe payment method ID)
    payment_token: str | None = None


class TransactionRead(BaseModel):
    id: UUID
    user_id: UUID
    ticket_id: UUID | None
    amount: Decimal
    currency: str
    status: TransactionStatus
    provider: PaymentProvider
    provider_reference: str | None
    failure_reason: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RefundRequest(BaseModel):
    reason: str | None = None
