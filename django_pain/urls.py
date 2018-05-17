from django.urls import path

from .views import PaymentListView

urlpatterns = [
    path('payments/', PaymentListView.as_view()),
]
