from __future__ import annotations
from django.db import transaction

from appliance_module.model.appliance import Appliance
from appliance_module.model.endpoint import Endpoint
from appliance_module.model.state import EndpointApplianceStateRoom   
from .appliance_service import ApplianceService


class ApplianceServiceFactory:
    """
    Responsible for constructing ApplianceService with locked DB rows.
    """

    @staticmethod
    @transaction.atomic
    def create(
        appliance_name: str,
        endpoint_id: int
    ) -> ApplianceService:

        appliance = Appliance.objects.get(name=appliance_name)
        endpoint = Endpoint.objects.get(pk=endpoint_id)

        state = (
            EndpointApplianceStateRoom.objects
            .get(endpoint=endpoint, appliance=appliance)
        )

        return ApplianceService(
            state=state
        )
