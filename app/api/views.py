import logging

from django.db import connection, models, transaction, utils
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework import status

logger = logging.getLogger(__name__)


class CreateTableView(APIView):
    def post(self, request):
        table_name = request.data.get("name")
        fields = request.data.get("fields")

        if not table_name or not fields:
            return JsonResponse(
                {"error": "Invalid input"}, status=status.HTTP_400_BAD_REQUEST
            )

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
                return JsonResponse(
                    {"error": "Invalid field type"}, status=status.HTTP_400_BAD_REQUEST
                )

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
                {"error": "Table creation failed", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return JsonResponse(
            {"message": "Table created successfully", "table_id": table_name},
            status=status.HTTP_201_CREATED,
        )


class UpdateTableView(APIView):
    def put(self, request, id):
        table_name = f"app_{id}"
        new_fields = request.data.get("fields", [])

        # Define a dynamic model class
        DynamicModel = type(
            "DynamicModel",
            (models.Model,),
            {
                "__module__": "app.models",
                "Meta": type("Meta", (object,), {"db_table": table_name}),
            },
        )

        # Connect to the database schema editor
        with connection.schema_editor() as schema_editor:
            for field in new_fields:
                field_name = field["name"]
                field_type = field["type"]

                if field_type == "string":
                    new_field = models.CharField(max_length=255, null=True, blank=True)
                elif field_type == "number":
                    new_field = models.IntegerField(null=True, blank=True)
                elif field_type == "boolean":
                    new_field = models.BooleanField(null=True, blank=True)
                else:
                    return JsonResponse(
                        {"error": f"Unsupported field type: {field_type}"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # Set the field name
                new_field.set_attributes_from_name(field_name)

                # Add the new field to the table
                try:
                    schema_editor.add_field(DynamicModel, new_field)
                except utils.ProgrammingError as e:
                    logger.error(f"Adding new field failed: {e}")
                    return JsonResponse(
                        {"error": "Adding new field failed", "details": str(e)},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

        return JsonResponse(
            {"message": "Table updated successfully"}, status=status.HTTP_200_OK
        )


class AddRowView(APIView):
    def post(self, request, id):
        table_name = f"app_{id}"
        data = request.data

        # Define a dynamic model class
        DynamicModel = type(
            "DynamicModel",
            (models.Model,),
            {
                "__module__": "app.models",
                "Meta": type("Meta", (object,), {"db_table": table_name}),
            },
        )

        # Add fields dynamically based on the existing table schema
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table_name}'"
            )
            columns = cursor.fetchall()
            for column in columns:
                column_name, data_type = column
                if column_name == "id":
                    field = models.AutoField(primary_key=True)
                elif data_type == "character varying":
                    field = models.CharField(max_length=255)
                elif data_type in ["integer", "bigint"]:
                    field = models.IntegerField()
                elif data_type == "boolean":
                    field = models.BooleanField()
                else:
                    return JsonResponse(
                        {"error": f"Unsupported column type: {data_type}"}, status=400
                    )
                if not hasattr(DynamicModel, column_name):
                    DynamicModel.add_to_class(column_name, field)

        # Validate and save the data
        try:
            with transaction.atomic():
                instance = DynamicModel(**data)
                instance.save()
            return JsonResponse(
                {"message": "Row added successfully"}, status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class DynamicTableRowsView(APIView):
    def get(self, request, id):
        # Ustal dynamiczny model na podstawie id tabeli
        table_name = f"app_{id}"

        with connection.cursor() as cursor:
            # Sprawdź, czy tabela istnieje
            cursor.execute(
                f"SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name='{table_name}'"
            )
            if not cursor.fetchone():
                return JsonResponse(
                    {"error": "Table not found"}, status=status.HTTP_404_NOT_FOUND
                )

            # Pobierz wszystkie wiersze z tabeli
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()

            # Pobierz nazwy kolumn
            cursor.execute(
                f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table_name}' ORDER BY ordinal_position"
            )
            columns = [col[0] for col in cursor.fetchall()]

        # Przekształć wiersze na listę słowników
        results = [dict(zip(columns, row)) for row in rows]

        return JsonResponse(results, safe=False)
