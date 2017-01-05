from django.conf.urls import url

from . import views

app_name = 'AnimalFeed'
urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^(?P<pk>[0-9]+)/edit$', views.CommodityEditView.as_view(), name='commodity_edit'),
    url(r'^(?P<pk>[0-9]+)/$', views.CommodityView.as_view(), name='commodity'),
    url(r'^staff_commodity/$', views.CommodityStaffView.as_view(), name='staff_commodity'),
    url(r'^staff_orders/$', views.OrderStaffView.as_view(), name='staff_orders'),
    url(r'^register/$', views.RegisterFormView.as_view(), name='register'),
    url(r'^login/$', views.LoginFormView.as_view(), name='login'),
    url(r'^logout/$', views.LogoutView.as_view(), name='logout'),
    url(r'^confirmation/$', views.OrderConfirmation.as_view(), name='confirmation'),
    url(r'^accepted/$', views.AcceptedOrderView.as_view(), name='accepted_order')
]