from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from .auth_views import LoginView


urlpatterns = [
    path('admin/', admin.site.urls),

    # Authentication
    path('api/auth/login/', LoginView.as_view(), name='api-login'),

    # Application APIs
    path('api/ingredients/', include('inventory.urls')),
    path('api/recipes/', include('recipe.urls')),
    path('api/production/', include('production.urls')),
    path('api/dashboard/', include('dashboard.urls')),
    path('api/reports/', include('reports.urls')),
    path('api/settings/', include('app_settings.urls')),
    path('api/audit-logs/', include('audit.urls')),
]

urlpatterns += static(
    settings.MEDIA_URL,
    document_root=settings.MEDIA_ROOT
)