"""
URL configuration for quwei_mall project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from django.contrib import admin
from django.urls import path,include,re_path

urlpatterns = [
    path('admin/', admin.site.urls),
    #haystack,#该路是官方固定的，不能改动
    re_path(r'^search/', include('haystack.urls')),
    #users
    re_path(r'^', include(('users.urls','users'),namespace='users')),
    #contents
    re_path(r'^', include(('contents.urls','contents'),namespace='contents')),
    #verifications
    re_path(r'^', include('verifications.urls')),
    #oauth
    re_path(r'^', include('oauth.urls')),
    #areas
    re_path(r'^', include('areas.urls')),
    #goods
    re_path(r'^', include(('goods.urls','goods'),namespace='goods')),
    #carts
    re_path(r'^', include(('carts.urls','carts'),namespace='carts')),
    #orders
    re_path(r'^', include(('orders.urls','orders'),namespace='orders')),
    #payment
    re_path(r'^', include(('payment.urls', 'payment'),namespace='payment'))
]

