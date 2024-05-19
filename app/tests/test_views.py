import json

import pytest
from django.db import connection
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
def test_create_dynamic_table(api_client):
    url = reverse("create-table")
    data = {
        "name": "DynamicTable",
        "fields": [
            {"name": "field1", "type": "string"},
            {"name": "field2", "type": "number"},
            {"name": "field3", "type": "boolean"},
        ],
    }
    response = api_client.post(url, data, format="json")
    assert response.status_code == 201

    # Uzyskaj dane odpowiedzi w formacie JSON
    response_data = json.loads(response.content)
    assert response_data["message"] == "Table created successfully"
    assert "table_id" in response_data

    # Verify the table is created in the database
    table_id = response_data["table_id"]

    with connection.cursor() as cursor:
        cursor.execute(
            f"SELECT * FROM information_schema.tables WHERE table_name = 'app_{table_id}'"
        )
        assert cursor.fetchone() is not None


@pytest.mark.django_db
def test_update_dynamic_table(api_client):
    # Najpierw utwórz tabelę
    create_url = reverse("create-table")
    create_data = {
        "name": "DynamicTable2",
        "fields": [
            {"name": "field1", "type": "string"},
            {"name": "field2", "type": "number"},
            {"name": "field3", "type": "boolean"},
        ],
    }
    create_response = api_client.post(create_url, create_data, format="json")
    assert create_response.status_code == 201
    create_response_data = json.loads(create_response.content)
    table_id = create_response_data["table_id"]

    # Zaktualizuj tabelę
    update_url = reverse("update-table", kwargs={"id": table_id})
    update_data = {"fields": [{"name": "field4", "type": "string"}]}
    update_response = api_client.put(update_url, update_data, format="json")
    assert update_response.status_code == 200
    assert update_response.json()["message"] == "Table updated successfully"

    # Sprawdź, czy tabela została zaktualizowana
    with connection.cursor() as cursor:
        cursor.execute(
            f"SELECT column_name FROM information_schema.columns WHERE table_name = 'app_{table_id}'"
        )
        columns = cursor.fetchall()
        assert ("field1",) in columns
        assert ("field2",) in columns
        assert ("field3",) in columns
        assert ("field4",) in columns


@pytest.mark.django_db
def test_add_row(api_client):
    create_url = reverse("create-table")
    create_data = {
        "name": "DynamicTable3",
        "fields": [
            {"name": "field1", "type": "string"},
            {"name": "field2", "type": "number"},
            {"name": "field3", "type": "boolean"},
        ],
    }
    create_response = api_client.post(create_url, create_data, format="json")
    assert create_response.status_code == 201
    create_response_data = create_response.json()
    table_id = create_response_data["table_id"]

    add_row_url = reverse("add-row", kwargs={"id": table_id})
    row_data = {"field1": "Test String", "field2": 123, "field3": True}
    add_row_response = api_client.post(add_row_url, row_data, format="json")
    print(add_row_response.json())
    assert add_row_response.status_code == 201
    assert add_row_response.json()["message"] == "Row added successfully"

    # Verify the row is added to the database
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT * FROM app_{table_id}")
        rows = cursor.fetchall()
        assert len(rows) == 1
        assert rows[0][1:] == ("Test String", 123, True)


@pytest.mark.django_db
def test_get_rows(api_client):
    create_url = reverse("create-table")
    create_data = {
        "name": "DynamicTable4",
        "fields": [
            {"name": "field1", "type": "string"},
            {"name": "field2", "type": "number"},
            {"name": "field3", "type": "boolean"},
        ],
    }
    create_response = api_client.post(create_url, create_data, format="json")
    assert create_response.status_code == 201
    create_response_data = create_response.json()
    table_id = create_response_data["table_id"]

    add_row_url = reverse("add-row", kwargs={"id": table_id})
    row_data = {"field1": "Test String", "field2": 123, "field3": True}
    add_row_response = api_client.post(add_row_url, row_data, format="json")
    assert add_row_response.status_code == 201

    get_rows_url = reverse("get-rows", kwargs={"id": table_id})
    get_rows_response = api_client.get(get_rows_url)
    assert get_rows_response.status_code == 200
    rows_data = get_rows_response.json()
    assert len(rows_data) == 1
    print(f"rows_data: {rows_data}")
    assert rows_data[0]["field1"] == "Test String"
    assert rows_data[0]["field2"] == 123
    assert rows_data[0]["field3"] is True

@pytest.mark.django_db
def test_update_table_add_column(api_client):
    # Step 1: Create a new table
    create_url = reverse("create-table")
    create_data = {
        "name": "TestTable",
        "fields": [
            {"name": "field1", "type": "string"},
            {"name": "field2", "type": "number"},
        ],
    }
    create_response = api_client.post(create_url, create_data, format="json")
    assert create_response.status_code == 201
    create_response_data = create_response.json()
    table_id = create_response_data["table_id"]

    # Step 2: Add a row to the table
    add_row_url = reverse("add-row", kwargs={"id": table_id})
    row_data = {"field1": "Test String", "field2": 123}
    add_row_response = api_client.post(add_row_url, row_data, format="json")
    assert add_row_response.status_code == 201

    # Step 3: Update the table by adding a new column
    update_url = reverse("update-table", kwargs={"id": table_id})
    update_data = {
        "fields": [
            {"name": "field3", "type": "boolean"},
        ]
    }
    update_response = api_client.put(update_url, update_data, format="json")
    assert update_response.status_code == 200

    # Step 4: Add a new row with the new column
    row_data_with_new_column = {"field1": "New String", "field2": 456, "field3": True}
    add_row_response_with_new_column = api_client.post(add_row_url, row_data_with_new_column, format="json")
    assert add_row_response_with_new_column.status_code == 201

    # Step 5: Get all rows and check if the new column is added correctly
    get_rows_url = reverse("get-rows", kwargs={"id": table_id})
    get_rows_response = api_client.get(get_rows_url)
    assert get_rows_response.status_code == 200
    rows_data = get_rows_response.json()
    
    assert len(rows_data) == 2
    assert rows_data[0]["field1"] == "Test String"
    assert rows_data[0]["field2"] == 123
    assert rows_data[0].get("field3") is None
    assert rows_data[1]["field1"] == "New String"
    assert rows_data[1]["field2"] == 456
    assert rows_data[1]["field3"] is True
