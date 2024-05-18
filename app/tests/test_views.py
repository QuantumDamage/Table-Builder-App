import json
import logging

import pytest
from django.db import connection
from django.urls import reverse
from rest_framework.test import APIClient

logger = logging.getLogger(__name__)


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
    logging.info(response_data)
    assert response_data["message"] == "Table created successfully"
    assert "table_id" in response_data

    # Verify the table is created in the database
    table_id = response_data["table_id"]
    with connection.cursor() as cursor:
        cursor.execute(
            f"SELECT * FROM information_schema.tables WHERE table_name = '{table_id}'"
        )
        assert cursor.fetchone() is not None


@pytest.mark.django_db
def test_update_dynamic_table(api_client):
    # Najpierw utwórz tabelę
    create_url = reverse("create-table")
    create_data = {
        "name": "DynamicTable",
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

    # Sprawdź, czy tabela została zaktualizowana
    with connection.cursor() as cursor:
        cursor.execute(
            f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table_id}' AND column_name = 'field4'"
        )
        assert cursor.fetchone() is not None
