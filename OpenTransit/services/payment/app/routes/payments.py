"""Payment transaction routes."""

import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import PaymentProvider, Transaction, TransactionStatus
from app.schemas import PaymentInitiateRequest, RefundRequest, TransactionRead

router = APIRouter(prefix="/payments", tags=["payments"])


def _sandbox_process(amount, currency: str) -> tuple[str, TransactionStatus]:
    """
    Sandbox payment processor.
    Always succeeds and returns a fake provider reference.
    In production, replace with real Stripe/PayPal integration.
    """
    return f"sandbox_{uuid.uuid4().hex}", TransactionStatus.completed


@router.post("", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
async def initiate_payment(
    payload: PaymentInitiateRequest, db: AsyncSession = Depends(get_db)
) -> Transaction:
    """Initiate a payment transaction."""
    transaction = Transaction(
        user_id=payload.user_id,
        ticket_id=payload.ticket_id,
        amount=payload.amount,
        currency=payload.currency,
        provider=payload.provider,
        status=TransactionStatus.pending,
    )
    db.add(transaction)
    await db.flush()

    if payload.provider == PaymentProvider.sandbox or settings.enable_sandbox_mode:
        ref, tx_status = _sandbox_process(payload.amount, payload.currency)
        transaction.provider_reference = ref
        transaction.status = tx_status
    else:
        # Real provider integration placeholder
        transaction.status = TransactionStatus.failed
        transaction.failure_reason = "Provider not configured"

    await db.commit()
    await db.refresh(transaction)
    return transaction


@router.get("/{transaction_id}", response_model=TransactionRead)
async def get_transaction(transaction_id: UUID, db: AsyncSession = Depends(get_db)) -> Transaction:
    """Retrieve a transaction by ID."""
    result = await db.execute(select(Transaction).where(Transaction.id == transaction_id))
    tx = result.scalar_one_or_none()
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return tx


@router.get("", response_model=list[TransactionRead])
async def list_user_transactions(user_id: UUID, db: AsyncSession = Depends(get_db)) -> list[Transaction]:
    """List all transactions for a user."""
    result = await db.execute(
        select(Transaction).where(Transaction.user_id == user_id).order_by(Transaction.created_at.desc())
    )
    return list(result.scalars().all())


@router.post("/{transaction_id}/refund", response_model=TransactionRead)
async def refund_transaction(
    transaction_id: UUID, payload: RefundRequest, db: AsyncSession = Depends(get_db)
) -> Transaction:
    """Refund a completed transaction."""
    result = await db.execute(select(Transaction).where(Transaction.id == transaction_id))
    tx = result.scalar_one_or_none()
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    if tx.status != TransactionStatus.completed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot refund a transaction with status '{tx.status.value}'",
        )
    tx.status = TransactionStatus.refunded
    if payload.reason:
        tx.failure_reason = payload.reason
    await db.commit()
    await db.refresh(tx)
    return tx
