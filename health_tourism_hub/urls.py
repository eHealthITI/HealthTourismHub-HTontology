from django.contrib import admin
from django.urls import include, path, re_path
from django.conf import settings
from django.conf.urls.static import static


handler404 = 'hth_app.views.error_404'

urlpatterns = [
    path('', include('hth_app.urls')),
    path('', include('pwa.urls')),
    path('', include('accounts.urls')),
    path('admin/', admin.site.urls),
    re_path(r'^chaining/', include('smart_selects.urls')),
]
if bool(settings.DEBUG):
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
