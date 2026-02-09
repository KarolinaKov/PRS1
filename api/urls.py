from django.urls import path
from .views import (
    ApplianceStartView,
    ApplianceFinishView,
    AuthChallengeView,
    AuthVerifyView,
)

urlpatterns = [
    path("auth/challenge/", AuthChallengeView.as_view()),
    path("auth/verify/", AuthVerifyView.as_view()),
    path("appliance/start/", ApplianceStartView.as_view()),
    path("appliance/finish/", ApplianceFinishView.as_view()),
]
