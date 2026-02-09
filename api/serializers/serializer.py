from rest_framework import serializers

class AuthenticateRoomSerializer(serializers.Serializer):
    room_num = serializers.IntegerField()
    endpoint_id = serializers.IntegerField()

class AuthorizeRoomSerializer(serializers.Serializer):
    token = serializers.CharField()
    auth_code = serializers.IntegerField()


class StartApplianceSerializer(serializers.Serializer):
    token = serializers.CharField()
    appliance_name = serializers.CharField()
    units = serializers.IntegerField(min_value=1, max_value=14400)
    price = serializers.IntegerField(max_digits=4, min_value=1)


class FinishApplianceSerializer(serializers.Serializer):
    token = serializers.CharField()
    units = serializers.IntegerField(min_value=1, max_value=14400)
    price = serializers.IntegerField(max_digits=4, min_value=1)
    aborted = serializers.BooleanField(default=False)

