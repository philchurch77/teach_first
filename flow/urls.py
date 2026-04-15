from django.urls import path

from .views import flow_view


urlpatterns = [
    path('', flow_view, name='flow'),
]