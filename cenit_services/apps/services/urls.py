from django.urls import path
from . import views
app_name = "services_app"

urlpatterns = [
    path(
        'api/services/v1/generate-certificate/<str:subscription_id>/<str:proof_id>/',
        views.Generate_Certificate.as_view()
    ),
]