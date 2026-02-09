from __future__ import annotations
from django.db import models


class ApplianceManager(models.Manager["Appliance"]):
    """
    Custom manager for appliance lookup.
    """

    def by_name(self, name: str) -> "Appliance":
        return self.get(name=name)


class Appliance(models.Model):
    """
    Represents an appliance with per-unit pricing.
    """

    appliance_id: int = models.AutoField(primary_key=True)
    name: str = models.CharField(max_length=200)
    price_per_unit: int = models.IntegerField()

    objects = ApplianceManager()

    class Meta:
        db_table = "appliances"

    def __str__(self) -> str:
        return f"{self.name} ({self.price_per_unit})"
