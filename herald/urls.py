"""
Urls for herald app
"""

from django.urls import path
from .views import TestNotificationList, TestNotification

urlpatterns = [
    path("", TestNotificationList.as_view(), name="herald_preview_list"),
    path("<int:index>/<str:type>/", TestNotification.as_view(), name="herald_preview"),
]
