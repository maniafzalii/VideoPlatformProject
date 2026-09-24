from django.urls import path
from . import views


urlpatterns = [
    path('plans/', views.PlanListView.as_view(), name='plans'),
    path('me/', views.MySubscriptionView.as_view(), name='my-subscription'),
    path('subscribe/', views.SubscribeView.as_view(), name='subscribe'),
    path('renew/', views.RenewView.as_view(), name='renew'),
    path('cancel/', views.CancelView.as_view(), name='cancel'),
    path('payments/', views.PaymentListView.as_view(), name='payments'),
]