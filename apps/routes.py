from django.urls import path, include
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions


schema_view = get_schema_view(
    openapi.Info(
        title='AlexChat',
        default_version='v1',
        description='Backend of AlexChat',
        contact=openapi.Contact(email='alex@shvarev.com')
    ),
    public=True,
    permission_classes=(permissions.AllowAny, ),
)

urlpatterns = [
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    path('oauth/', include('apps.oauth.urls')),
    path('groups/', include('apps.groups.urls')),
]
