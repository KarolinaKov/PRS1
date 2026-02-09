from __future__ import annotations

from django.db import models
from django.utils import timezone

from .endpoint import Endpoint
from .appliance import Appliance
from .room import Room


class RunsLog(models.Model):
    """
    Tracks appliance execution lifecycle.
    """

    class State(models.IntegerChoices):
        RUNNING = 1, "Running"
        FINISHED = 2, "Finished"
        ABORTED = 3, "Aborted"

    logid: int = models.BigAutoField(primary_key=True)

    endpoint = models.ForeignKey(Endpoint, on_delete=models.PROTECT)
    appliance = models.ForeignKey(Appliance, on_delete=models.PROTECT)
    room = models.ForeignKey(Room, on_delete=models.PROTECT)

    created_at = models.DateTimeField(auto_now_add=True)

    inic_units: int = models.IntegerField()
    inic_price: int = models.IntegerField()

    state: int = models.IntegerField(
        choices=State.choices,
        default=State.RUNNING
    )

    finished_at = models.DateTimeField(null=True, blank=True)
    final_units: int | None = models.IntegerField(null=True, blank=True)
    final_price: int | None = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "runs_logs"

    def finish(
        self,
        final_units: int,
        final_price: int,
        aborted: bool = False
    ) -> None:
        """
        Finalizes the log.
        """

        self.state = (
            RunsLog.State.ABORTED
            if aborted else RunsLog.State.FINISHED
        )

        self.final_units = final_units
        self.final_price = final_price
        self.finished_at = timezone.now()

        self.save()
