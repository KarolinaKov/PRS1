from __future__ import annotations
from django.db import models
from django.db.models import Q, CheckConstraint


class Room(models.Model):
    """
    Represents a room holding a monetary balance.
    """

    room_id: int = models.BigAutoField(primary_key=True)
    balance: int = models.IntegerField()
    key: int = models.BigIntegerField(unique=True)

    class Meta:
        db_table = "rooms"
        constraints = [
            CheckConstraint(
                check=Q(balance__gte=0),
                name="balance_non_negative"
            )
        ]

    def __str__(self) -> str:
        return f"Room {self.room_id} — balance={self.balance} - key={self.key}"

    def withdraw(self, amount: int) -> None:
        """
        Withdraw funds from the room.

        Raises:
            RuntimeError: if insufficient balance.
        """
        if amount > self.balance:
            raise RuntimeError("Insufficient balance")

        self.balance -= amount
        self.save(update_fields=["balance"])

    def deposit(self, amount: int) -> None:
        """
        Deposit funds back to the room.
        """
        self.balance += amount
        self.save(update_fields=["balance"])
