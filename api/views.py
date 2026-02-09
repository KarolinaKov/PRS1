

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


from appliance_module.model.room import Room
from appliance_module.model.endpoint import Endpoint
from appliance_module.model.appliance import Appliance
from appliance_module.servicies_factories.appliance_service_factory import ApplianceServiceFactory
from appliance_module.servicies_factories.auth_service import AuthService
from .serializers.serializer import (
    StartApplianceSerializer,
    FinishApplianceSerializer,
    AuthenticateRoomSerializer,
    AuthorizeRoomSerializer,
)
class AuthChallengeView(APIView):
    """
    Provides challenge token for authenticating appliance control requests.
    """

    def post(self, request):
        serializer = AuthenticateRoomSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        room_num = serializer.validated_data["room_num"]
        endpoint_id = serializer.validated_data["endpoint_id"]
        try:
            Room.objects.get(key=room_num)
            Endpoint.objects.get(pk=endpoint_id)
            challenge_token = AuthService.encode(serializer.validated_data, "challenge")
            return Response({"token": challenge_token},
                            status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)},
                             status=status.HTTP_400_BAD_REQUEST)

class AuthVerifyView(APIView):
    """
    Verifies challenge token and authorization code for appliance control requests.
    """ 

    def post(self, request):
        serializer = AuthorizeRoomSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data["token"]
        auth_code = serializer.validated_data["auth_code"]
        try:
            decoded = AuthService.verify_token(token)
            access_token = AuthService.verify_room(decoded, auth_code)
            return Response({"token": str(access_token),
                             "balance": Room.objects.get(key=decoded["room_num"]).balance,
                             "appliances": [{"name": a.name, "value": a.price_per_unit} for a in Appliance.objects.all()]},
                            status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)},
                             status=status.HTTP_400_BAD_REQUEST)

class ApplianceStartView(APIView):

    def post(self, request):
        serializer = StartApplianceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        token_payload = AuthService.verify_token(data["token"])
        try:
            service = ApplianceServiceFactory.create(
                appliance_name=data["appliance_name"],
                endpoint_id = token_payload["endpoint_id"]
            )
            remaining =service.start(room_num=token_payload["room_num"], units=data["units"], price = 100*data["price"])
            token = AuthService.encode(token_payload, "start", data["units"])

            return Response(
                    {
                        "newbalance": remaining,
                        "token": token, 
                    },
                    status=status.HTTP_201_CREATED,
                )

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
class ApplianceFinishView(APIView):

    def post(self, request):
        serializer = FinishApplianceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        token_payload = AuthService.verify_token(data["token"])

        try:
            service = ApplianceServiceFactory.create(
                appliance_name=token_payload["appliance_name"],
                endpoint_id=token_payload["endpoint_id"],
            )

            service.finish(
                final_units=data["units"],
                final_price=100*data["price"],
                aborted=data["aborted"],
            )

            return Response(
                {"status": "finished"},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

