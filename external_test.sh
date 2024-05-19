#!/bin/bash

# Stałe konfiguracyjne
API_BASE_URL="http://localhost:8000/api"
FIELDS='[{"name": "field1", "type": "string"},{"name": "field2", "type": "number"}]'
NEW_FIELD='[{"name": "field3", "type": "boolean"}]'
ROW_DATA='{"field1": "Test String", "field2": 123}'
NEW_ROW_DATA='{"field1": "New String", "field2": 456, "field3": true}'

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

# Krok 2a: Pobieranie wszystkich wierszy z tabeli
echo "Krok 2a: Pobieranie wszystkich wierszy z tabeli dynamicznej"
get_rows_response=$(curl -s -X GET "$API_BASE_URL/table/$table_id/rows")
rows_data=$(echo "$get_rows_response" | jq '.')

# Wyświetlanie wierszy tabeli
echo "Wiersze w tabeli dynamicznej:"
echo "$rows_data"

# Krok 3: Aktualizacja tabeli, dodanie nowej kolumny
echo "Krok 3: Aktualizacja tabeli, dodanie nowej kolumny"
update_table_response=$(curl -s -X PUT -H "Content-Type: application/json" -d "{\"fields\": $NEW_FIELD}" "$API_BASE_URL/table/$table_id")
message=$(echo "$update_table_response" | jq -r '.message')

# Sprawdzenie, czy odpowiedź zawiera komunikat o poprawnym dodaniu kolumny
if [[ "$message" == "Table updated successfully" ]]; then
    echo "Kolumna została dodana do tabeli dynamicznej poprawnie."
else
    echo "Błąd podczas dodawania kolumny do tabeli dynamicznej. Odpowiedź serwera: $update_table_response"
    exit 1
fi

# Krok 4: Dodawanie wiersza do tabeli z nową kolumną
echo "Krok 4: Dodawanie wiersza do tabeli z nową kolumną"
add_row_with_new_column_response=$(curl -s -X POST -H "Content-Type: application/json" -d "$NEW_ROW_DATA" "$API_BASE_URL/table/$table_id/row")
message=$(echo "$add_row_with_new_column_response" | jq -r '.message')

# Sprawdzenie, czy odpowiedź zawiera komunikat o poprawnym dodaniu wiersza z nową kolumną
if [[ "$message" == "Row added successfully" ]]; then
    echo "Wiersz z nową kolumną został dodany do tabeli dynamicznej poprawnie."
else
    echo "Błąd podczas dodawania wiersza z nową kolumną do tabeli dynamicznej. Odpowiedź serwera: $add_row_with_new_column_response"
    exit 1
fi

# Krok 5: Pobieranie wszystkich wierszy z tabeli
echo "Krok 5: Pobieranie wszystkich wierszy z tabeli dynamicznej"
get_rows_response=$(curl -s -X GET "$API_BASE_URL/table/$table_id/rows")
rows_data=$(echo "$get_rows_response" | jq '.')

# Wyświetlanie wierszy tabeli
echo "Wiersze w tabeli dynamicznej:"
echo "$rows_data"
