from __future__ import annotations

import random
from django.db import models


class Endpoint(models.Model):
    """
    Represents a physical or virtual device capable of running appliances.
    """

    endpoint_id: int = models.AutoField(primary_key=True)
    ip_add: str | None = models.GenericIPAddressField(null=True, blank=True)
    connection: bool = models.BooleanField(default=False)
    token: int = models.IntegerField(default=1)

    class Meta:
        db_table = "endpoints"

    def __str__(self) -> str:
        return f"Endpoint {self.endpoint_id} ({self.ip_add})"

    def change_token(self) -> None:
        """
        Regenerates token version.
        """
        self.token = random.randint(1, 1_000_000)
        self.save(update_fields=["token"])
