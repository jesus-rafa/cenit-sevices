from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


schema_view = get_schema_view(
   openapi.Info(
      title="°Cenit Services",
      default_version='v1.0.0',
      description="API para generar los servicios necesarios para el Ecosistema °Cenit",
      terms_of_service="https://cenitservices.emerald.com/policies/terms/",
      contact=openapi.Contact(email="rafael.lopez@emerald.dev"),
      license=openapi.License(name="Emerald License"),
   ),
   public=True,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path('', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redocs/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path("", include('apps.services.urls')),
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)