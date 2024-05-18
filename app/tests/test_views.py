import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from django.db import connection
import json

@pytest.fixture
def api_client():
    return APIClient()

@pytest.mark.django_db
def test_create_dynamic_table(api_client):
    url = reverse('create-table')
    data = {
        "name": "DynamicTable",
        "fields": [
            {"name": "field1", "type": "string"},
            {"name": "field2", "type": "number"},
            {"name": "field3", "type": "boolean"}
        ]
    }
    response = api_client.post(url, data, format='json')
    assert response.status_code == 201
    
    # Uzyskaj dane odpowiedzi w formacie JSON
    response_data = json.loads(response.content)
    assert response_data['message'] == 'Table created successfully'

    # Verify the table is created in the database
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM information_schema.tables WHERE table_name = 'dynamictable'")
        assert cursor.fetchone() is not None
