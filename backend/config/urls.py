"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path("api/v1/auth/", include("system.urls.auth")),
    path("api/v1/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/v1/system/", include("system.urls.system")),
    path("api/v1/products/", include("product.urls")),
    path("api/v1/purchase/", include("purchase.urls")),
    path("api/v1/sales/", include("sales.urls")),
    path("api/v1/inventory/", include("inventory.urls")),
    path("api/v1/finance/", include("finance.urls")),
    path("api/v1/hr/", include("hr.urls")),
]
