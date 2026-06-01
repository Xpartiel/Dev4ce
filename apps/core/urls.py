from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("en-construccion/", views.en_construccion, name="en_construccion"),
]