from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from authentication import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.client_login, name='client_login'),
    path('authentication/', include('authentication.urls')),
    path('clients/', include('clients.urls')),
    path('ts_company/', include('ts_company.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
