from django.db import models
from appliance_module.model.room import Room

class ValidPayments(models.Model):
    id = models.AutoField(primary_key=True)
    transaction_id = models.CharField(max_length=255, unique=True,db_index=True)
    amount = models.IntegerField()
    key = models.ForeignKey(Room, on_delete=models.PROTECT, db_index=True)
    payment_time = models.DateTimeField(auto_now_add=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment of {self.amount} at {self.timestamp}"

class InvalidPayments(models.Model):
    id = models.AutoField(primary_key=True)
    transaction_id = models.CharField(max_length=255, unique=True,db_index=True)
    amount = models.IntegerField()
    key = models.CharField(max_length=255, db_index=True)
    payment_time = models.DateTimeField(auto_now_add=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invalid Payment of {self.amount} at {self.timestamp} but really at {self.payment_time}"