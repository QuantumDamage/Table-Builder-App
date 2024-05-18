import logging

from django.apps import apps
from django.db import connection, models
from django.http import JsonResponse
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


class CreateTableView(APIView):
    def post(self, request):
        table_name = request.data.get("name")
        fields = request.data.get("fields")

        if not table_name or not fields:
            return JsonResponse({"error": "Invalid input"}, status=400)

        # Tworzenie dynamicznego modelu
        attrs = {"__module__": "app.models"}
        for field in fields:
            field_name = field["name"]
            field_type = field["type"]

            if field_type == "string":
                field_instance = models.CharField(max_length=255)
            elif field_type == "number":
                field_instance = models.IntegerField()
            elif field_type == "boolean":
                field_instance = models.BooleanField()
            else:
                return JsonResponse({"error": "Invalid field type"}, status=400)

            attrs[field_name] = field_instance

        table_name = table_name.lower()  # Ensure the table name is in lowercase
        DynamicTable = type(table_name, (models.Model,), attrs)

        # Rejestracja modelu w aplikacji
        try:
            with connection.schema_editor() as schema_editor:
                schema_editor.create_model(DynamicTable)
        except Exception as e:
            logger.error(f"Table creation failed: {e}")
            return JsonResponse(
                {"error": "Table creation failed", "details": str(e)}, status=500
            )

        return JsonResponse(
            {"message": "Table created successfully", "table_id": table_name},
            status=201,
        )


class UpdateTableView(APIView):
    def put(self, request, id):
        table_name = id
        fields = request.data.get("fields")

        if not fields:
            return JsonResponse({"error": "Invalid input"}, status=400)

        # Spróbuj pobrać dynamiczny model
        try:
            DynamicModel = apps.get_model("app", table_name.capitalize())
        except LookupError:
            return JsonResponse({"error": "Table not found"}, status=404)

        # Aktualizacja modelu
        for field in fields:
            field_name = field["name"]
            field_type = field["type"]

            if field_type == "string":
                field_instance = models.CharField(max_length=255)
            elif field_type == "number":
                field_instance = models.IntegerField()
            elif field_type == "boolean":
                field_instance = models.BooleanField()
            else:
                return JsonResponse({"error": "Invalid field type"}, status=400)

            field_instance.set_attributes_from_name(field_name)
            DynamicModel.add_to_class(field_name, field_instance)

        # Aktualizacja schematu bazy danych
        try:
            with connection.schema_editor() as schema_editor:
                schema_editor.alter_db_table(DynamicModel, table_name, table_name)
        except Exception as e:
            logger.error(f"Table update failed: {e}")
            return JsonResponse(
                {"error": "Table update failed", "details": str(e)}, status=500
            )

        return JsonResponse({"message": "Table updated successfully"}, status=200)


class AddRowView(APIView):
    def post(self, request):
        pass


class GetAllRowsView(APIView):
    def GET(self, request):
        pass
