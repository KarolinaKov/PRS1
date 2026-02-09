from django.db import models
from .room import Room


class RoomTOTP(models.Model):
    """
    Represents a TOTP secret associated with a room.
    """

    room = models.OneToOneField(Room, on_delete=models.CASCADE)
    secret = models.CharField(max_length=255)

    class Meta:
        db_table = "room_totps"
    def __str__(self):
        return f"RoomTOTP(room={self.room.key}, secret={self.secret})"