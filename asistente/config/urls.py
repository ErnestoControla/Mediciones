from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views import defaults as default_views
from django.views.generic import TemplateView

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    # Páginas base (puedes eliminarlas si no las usas)
    path("", TemplateView.as_view(template_name="pages/home.html"), name="home"),
    path("about/", TemplateView.as_view(template_name="pages/about.html"), name="about"),

    # Django Admin
    path(settings.ADMIN_URL, admin.site.urls),

    # Gestión de usuarios y cuentas
    path("users/", include("asistente.users.urls", namespace="users")),
    path("accounts/", include("allauth.urls")),
    
    # Sistema de análisis de coples
    path("analisis/", include("analisis_coples.urls", namespace="analisis_coples")),

    # API (nucleo del backend)
    path("api/", include("config.api_router")),

    # Auth extra (token DRF tradicional y JWT)
    path("api/auth-token/", obtain_auth_token, name="obtain_auth_token"),  # viejo
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),  # JWT login
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # API schema y docs
    path("api/schema/", SpectacularAPIView.as_view(), name="api-schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="api-schema"), name="api-docs"),
]

# Archivos media (solo en desarrollo)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Vistas de errores (solo en desarrollo)
if settings.DEBUG:
    urlpatterns += [
        path("400/", default_views.bad_request, kwargs={"exception": Exception("Bad Request!")}),
        path("403/", default_views.permission_denied, kwargs={"exception": Exception("Permission Denied")}),
        path("404/", default_views.page_not_found, kwargs={"exception": Exception("Page not Found")}),
        path("500/", default_views.server_error),
    ]

    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar
        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
