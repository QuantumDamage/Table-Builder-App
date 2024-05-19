from django.urls import path

from .views import AddRowView, CreateTableView, DynamicTableRowsView, UpdateTableView

urlpatterns = [
    path("table", CreateTableView.as_view(), name="create-table"),
    path("table/<str:id>", UpdateTableView.as_view(), name="update-table"),
    path("table/<str:id>/row", AddRowView.as_view(), name="add-row"),
    path("table/<str:id>/rows", DynamicTableRowsView.as_view(), name="get-rows"),
]
