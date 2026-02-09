from django.conf import settings
import jwt, pyotp
from datetime import datetime, timedelta
from appliance_module.model.room import Room
from appliance_module.model.roomtotp import RoomTOTP



class AuthService:

    @staticmethod
    def verify_room(payload, code):
        room = Room.objects.get(key=payload["room_num"])
        room_secret = RoomTOTP.objects.get(room=room).secret
        totp = pyotp.TOTP(room_secret)

        if not totp.verify(code, valid_window=1):
            raise ValueError("Invalid authorization code")
        
        payload = {
            "iss"  : "Backend",
            "token_type": "access",
            "room_num": payload["room_num"],
            "endpoint_id": payload["endpoint_id"],
            "exp": int((datetime.now() + settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"]).timestamp()),
        }
        access = jwt.encode(payload, settings.SIMPLE_JWT["SIGNING_KEY"], algorithm=settings.SIMPLE_JWT["ALGORITHM"])

        return str(access)
    @staticmethod
    def verify_token(token):
        try:
            payload = jwt.decode(token, settings.SIMPLE_JWT["SIGNING_KEY"], algorithms=[settings.SIMPLE_JWT["ALGORITHM"]])
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid token")
    @staticmethod
    def encode(old_payload, case, units=0):
        match case:
            case "challenge":
                payload = {
                    "iss"  : "Backend",
                    "token_type": "challenge",
                    "room_num": old_payload["room_num"],
                    "endpoint_id": old_payload["endpoint_id"],
                    "exp": int((datetime.now() + timedelta(minutes=2)).timestamp())}
                return jwt.encode(payload, settings.SIMPLE_JWT["SIGNING_KEY"], algorithm=settings.SIMPLE_JWT["ALGORITHM"])
            case "start":
                payload = {
                    "iss"  : "Backend",
                    "token_type": "start",
                    "room_num": old_payload["room_num"],
                    "endpoint_id": old_payload["endpoint_id"],
                    #timedelta is set to units + 1 minute for possible delays between start and finish requests
                    "exp": int((datetime.now() + timedelta(seconds=60+units)).timestamp())}
                return jwt.encode(payload, settings.SIMPLE_JWT["SIGNING_KEY"], algorithm=settings.SIMPLE_JWT["ALGORITHM"])