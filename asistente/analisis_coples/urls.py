# analisis_coples/urls.py

from django.urls import path, include

app_name = 'analisis_coples'

urlpatterns = [
    # APIs REST
    path('api/', include('analisis_coples.api.urls')),
]
