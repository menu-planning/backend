from sqlalchemy import Column, ForeignKey, Table
from src.db.base import SaBase

receipts_houses_association = Table(
    "receipts_houses_association",
    SaBase.metadata,
    Column("receipt_id", ForeignKey("receipt_tracker.receipts.id"), primary_key=True),
    Column("house_id", ForeignKey("receipt_tracker.houses.id"), primary_key=True),
    schema="receipt_tracker",
)
