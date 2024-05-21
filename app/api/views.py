import logging

import psycopg2
from django.db import connection, models, transaction, utils
from django.http import JsonResponse
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


class CreateTableView(APIView):
    @swagger_auto_schema(
        operation_description="Create a new dynamic table",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "name": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Table name"
                ),
                "fields": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "name": openapi.Schema(
                                type=openapi.TYPE_STRING, description="Field name"
                            ),
                            "type": openapi.Schema(
                                type=openapi.TYPE_STRING,
                                description="Field type",
                                enum=["string", "number", "boolean"],
                            ),
                        },
                        required=["name", "type"],
                    ),
                    description="List of fields to create in the table",
                ),
            },
            required=["name", "fields"],
            example={
                "name": "DynamicTable_123",
                "fields": [
                    {"name": "field1", "type": "string"},
                    {"name": "field2", "type": "number"},
                ],
            },
        ),
        responses={
            201: "Table created successfully",
            400: "Invalid input",
            409: "Duplicate Table",
        },
    )
    def post(self, request):
        table_name = request.data.get("name")
        fields = request.data.get("fields")

        if not table_name or not fields:
            return JsonResponse(
                {"error": "Invalid input"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Create dynamic model
        attrs = {"__module__": "app.models"}
        for field in fields:
            field_name = field["name"]
            field_type = field["type"]

            if field_type == "string":
                field_instance = models.CharField(max_length=255, null=True, blank=True)
            elif field_type == "number":
                field_instance = models.IntegerField(null=True, blank=True)
            elif field_type == "boolean":
                field_instance = models.BooleanField(null=True, blank=True)
            else:
                return JsonResponse(
                    {"error": "Invalid field type"}, status=status.HTTP_400_BAD_REQUEST
                )

            attrs[field_name] = field_instance

        table_name = table_name.lower()  # Ensure the table name is in lowercase
        DynamicTable = type(table_name, (models.Model,), attrs)

        # Register model in the application
        try:
            with connection.schema_editor() as schema_editor:
                schema_editor.create_model(DynamicTable)
        except utils.ProgrammingError as e:
            # Check if the error is a DuplicateTable error
            if isinstance(e.__cause__, psycopg2.errors.DuplicateTable):
                return JsonResponse(
                    {"error": f"Duplicate Table: {e}"}, status=status.HTTP_409_CONFLICT
                )
            else:
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
    @swagger_auto_schema(
        operation_description="Update the table by adding new columns",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "fields": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "name": openapi.Schema(
                                type=openapi.TYPE_STRING, description="Field name"
                            ),
                            "type": openapi.Schema(
                                type=openapi.TYPE_STRING,
                                description="Field type",
                                enum=["string", "number", "boolean"],
                            ),
                        },
                        required=["name", "type"],
                    ),
                    description="List of new fields to add",
                ),
            },
            required=["fields"],
            example={
                "fields": [
                    {"name": "field3", "type": "boolean"},
                ],
            },
        ),
        responses={
            200: "Table updated successfully",
            400: "Invalid field type",
        },
    )
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
    @swagger_auto_schema(
        operation_description="Add a new row to the dynamic table",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "field1": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Field 1"
                ),
                "field2": openapi.Schema(
                    type=openapi.TYPE_INTEGER, description="Field 2"
                ),
                "field3": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN, description="Field 3"
                ),
            },
            required=["field1", "field2"],
            example={
                "field1": "New String",
                "field2": 456,
                "field3": True,
            },
        ),
        responses={
            201: "Row added successfully",
            400: "Invalid input or adding row failed",
            404: "Table not found",
        },
    )
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
            if not columns:
                return JsonResponse(
                    {"error": f"Table {id} not found"}, status=status.HTTP_404_NOT_FOUND
                )
            for column in columns:
                column_name, data_type = column
                if column_name == "id":
                    field = models.AutoField(primary_key=True)
                elif data_type == "character varying":
                    field = models.CharField(max_length=255, null=True, blank=True)
                elif data_type in ["integer", "bigint"]:
                    field = models.IntegerField(null=True, blank=True)
                elif data_type == "boolean":
                    field = models.BooleanField(null=True, blank=True)
                else:
                    return JsonResponse(
                        {"error": f"Unsupported column type: {data_type}"}, status=400
                    )
                if not hasattr(DynamicModel, column_name):
                    DynamicModel.add_to_class(column_name, field)

        # Validate and save the data
        for field_name, field_value in data.items():
            column_type = next(
                (column[1] for column in columns if column[0] == field_name), None
            )
            if column_type == "integer" and not isinstance(field_value, int):
                return JsonResponse(
                    {
                        "error": f"Invalid data type for field '{field_name}': expected integer"
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if column_type == "character varying" and not isinstance(field_value, str):
                return JsonResponse(
                    {
                        "error": f"Invalid data type for field '{field_name}': expected string"
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if column_type == "boolean" and not isinstance(field_value, bool):
                return JsonResponse(
                    {
                        "error": f"Invalid data type for field '{field_name}': expected boolean"
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
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
    @swagger_auto_schema(
        operation_description="Get all rows from the dynamic table",
        responses={
            200: "List of all rows in the dynamic table",
            404: "Table not found",
        },
    )
    def get(self, request, id):
        # Determine the dynamic model based on the table id
        table_name = f"app_{id}"

        with connection.cursor() as cursor:
            # Check if the table exists
            cursor.execute(
                f"SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name='{table_name}'"
            )
            if not cursor.fetchone():
                return JsonResponse(
                    {"error": "Table not found"}, status=status.HTTP_404_NOT_FOUND
                )

            # Fetch all rows from the table
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()

            # Fetch column names
            cursor.execute(
                f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table_name}' ORDER BY ordinal_position"
            )
            columns = [col[0] for col in cursor.fetchall()]

        # Convert rows to a list of dictionaries
        results = [dict(zip(columns, row)) for row in rows]

        return JsonResponse(results, safe=False)
