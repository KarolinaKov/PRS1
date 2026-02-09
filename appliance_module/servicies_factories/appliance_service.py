from __future__ import annotations

from django.db import transaction

from appliance_module.model.room import Room
from appliance_module.model.runslog import RunsLog
from appliance_module.model.state import EndpointApplianceStateRoom



class ApplianceService:
    """
    Encapsulates business logic for appliance lifecycle.
    """

    def __init__(
        self,
        state: EndpointApplianceStateRoom,
    ) -> None:
        
        self.state = state

    # -----------------------------

    @transaction.atomic
    def start(self, room_num: int, units: int, price: int) -> int:
        """
        Starts appliance run.
        """

        if self.state.is_occupied:
            raise RuntimeError("Appliance already running")

        room = Room.objects.select_for_update().get(key=room_num)
        room.withdraw(price)

        log = RunsLog.objects.create(
            endpoint=self.state.endpoint,
            appliance=self.state.appliance,
            room=room,
            inic_units=units,
            inic_price=price,
        )

        self.state.is_occupied = True
        self.state.room = room
        self.state.log = log
        self.state.save()

        return room.balance

    # -----------------------------

    @transaction.atomic
    def finish(self, final_units: int,final_price: int, aborted: bool = False) -> None:
        """
        Finishes appliance execution.
        """

        if not self.state.is_occupied:
            raise RuntimeError("No active run")

        log = self.state.log
        if log.inic_units < final_units:
            raise ValueError("Final units cannot exceed initial units")

        log.finish(
            final_units=final_units,
            final_price=final_price,
            aborted=aborted
        )

        diff = log.inic_price - final_price

        if diff > 0:
            room = Room.objects.select_for_update().get(pk=log.room.pk)
            room.deposit(diff)

        self.state.is_occupied = False
        self.state.room = None
        self.state.log = None
        self.state.save()

    # -----------------------------

