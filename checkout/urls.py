from django.urls import path
from . import views
from .views import PaymentView

urlpatterns = [
    path('place_order/', views.place_order, name='place_order'),
    path('checkout', views.checkout, name='checkout'),
    path('payment', PaymentView.as_view(), name='payment'),
]
