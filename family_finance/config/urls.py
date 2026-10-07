from django.contrib import admin
from django.urls import include, path

from finance.views.health import health_check

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', health_check),
    path('api/', include('finance.urls')),
]
