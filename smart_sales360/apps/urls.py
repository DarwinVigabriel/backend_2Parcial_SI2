from django.urls import include, path

urlpatterns = [
    path('auth/', include('apps.authentication.urls')),
    path('company/', include('apps.company.urls')),
    path('categories/', include('apps.categories.urls')),
    path('products/', include('apps.products.urls')),
    path('sales/', include('apps.sales.urls')),
    path('stock/', include('apps.stock.urls')),
    path('clients/', include('apps.clients.urls')),
]
