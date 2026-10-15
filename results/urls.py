from django.urls import path
from . import views

app_name = "results"
urlpatterns = [path("", views.home, name="home"), path("export/<str:kind>/", views.export_data, name="export")]
