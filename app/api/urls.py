from django.urls import path
from .views import CreateTableView

urlpatterns = [
    path('table', CreateTableView.as_view(), name='create-table'),
]
