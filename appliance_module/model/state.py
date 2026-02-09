from __future__ import annotations
from django.db import models

from .endpoint import Endpoint
from .appliance import Appliance
from .room import Room
from .runslog import RunsLog


class EndpointApplianceStateRoomManager(models.Manager["EndpointApplianceStateRoom"]):

    def get_state(
        self,
        endpoint_id: int,
        appliance_id: int
    ) -> "EndpointApplianceStateRoom":

        return (
            self.select_related(
                "endpoint",
                "appliance",
                "room",
                "log"
            )
            .get(endpoint_id=endpoint_id, appliance_id=appliance_id)
        )


class EndpointApplianceStateRoom(models.Model):
    """
    Maintains runtime state of appliance on endpoint.
    """

    endpoint = models.ForeignKey(Endpoint, on_delete=models.CASCADE)
    appliance = models.ForeignKey(Appliance, on_delete=models.CASCADE)

    is_occupied: bool = models.BooleanField(default=False)

    room = models.ForeignKey(Room, null=True, on_delete=models.PROTECT)
    log = models.ForeignKey(RunsLog, null=True, on_delete=models.PROTECT)

    objects = EndpointApplianceStateRoomManager()

    class Meta:
        db_table = "endpoint_appliance_states"
        unique_together = ("endpoint", "appliance")
