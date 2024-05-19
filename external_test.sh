#!/bin/bash

# Stałe konfiguracyjne
API_BASE_URL="http://localhost:8000/api"
FIELDS='[{"name": "field1", "type": "string"},{"name": "field2", "type": "number"},{"name": "field3", "type": "boolean"}]'
ROW_DATA='{"field1": "Test String", "field2": 123, "field3": true}'

# Losowa nazwa tabeli
TABLE_NAME="DynamicTable_$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 10 | head -n 1)"

# Krok 1: Tworzenie tabeli dynamicznej
echo "Krok 1: Tworzenie tabeli dynamicznej o nazwie: $TABLE_NAME"
create_table_response=$(curl -s -X POST -H "Content-Type: application/json" -d "{\"name\": \"$TABLE_NAME\", \"fields\": $FIELDS}" "$API_BASE_URL/table")
message=$(echo "$create_table_response" | jq -r '.message')

# Sprawdzenie, czy odpowiedź zawiera komunikat o poprawnym utworzeniu tabeli
if [[ "$message" == "Table created successfully" ]]; then
    table_id=$(echo "$create_table_response" | jq -r '.table_id')
    echo "Tabela dynamiczna została utworzona poprawnie. ID tabeli: $table_id"
else
    echo "Błąd podczas tworzenia tabeli dynamicznej. Odpowiedź serwera: $create_table_response"
    exit 1
fi

# Krok 2: Dodawanie wiersza do tabeli
echo "Krok 2: Dodawanie wiersza do tabeli dynamicznej"
add_row_response=$(curl -s -X POST -H "Content-Type: application/json" -d "$ROW_DATA" "$API_BASE_URL/table/$table_id/row")
message=$(echo "$add_row_response" | jq -r '.message')

# Sprawdzenie, czy odpowiedź zawiera komunikat o poprawnym dodaniu wiersza
if [[ "$message" == "Row added successfully" ]]; then
    echo "Wiersz został dodany do tabeli dynamicznej poprawnie."
else
    echo "Błąd podczas dodawania wiersza do tabeli dynamicznej. Odpowiedź serwera: $add_row_response"
    exit 1
fi

# Krok 3: Pobieranie wszystkich wierszy z tabeli
echo "Krok 3: Pobieranie wszystkich wierszy z tabeli dynamicznej"
get_rows_response=$(curl -s -X GET "$API_BASE_URL/table/$table_id/rows")

# Sprawdzenie, czy pobrane dane zgadzają się z wysłanymi
response_body=$(echo "$get_rows_response" | jq -c)
expected_row=$(echo "$ROW_DATA" | jq -c)
actual_row=$(echo "$response_body" | jq -c '.[0] | {field1, field2, field3}')

if [[ "$expected_row" == "$actual_row" ]]; then
    echo "Pobrane dane zgadzają się z wysłanymi danymi."
else
    echo "Błąd: pobrane dane nie zgadzają się z wysłanymi danymi."
    echo "expected_row: $expected_row"
    echo "actual_row: $actual_row"
    echo "response_body: $response_body"
    exit 1
fi
