#!/bin/bash

# Configuration constants
API_BASE_URL="http://localhost:8000/api"
FIELDS='[{"name": "field1", "type": "string"},{"name": "field2", "type": "number"}]'
NEW_FIELD='[{"name": "field3", "type": "boolean"}]'
ROW_DATA='{"field1": "Test String", "field2": 123}'
NEW_ROW_DATA='{"field1": "New String", "field2": 456, "field3": true}'

# Generate random table name
TABLE_NAME="DynamicTable_$(head /dev/urandom | tr -dc A-Za-z0-9 | head -c 10)"

# Function to print error and exit
handle_error() {
    echo "Error: $1"
    exit 1
}

# Function to make a POST request and check the response
post_request() {
    local url="$1"
    local data="$2"
    local expected_message="$3"

    response=$(curl -s -X POST -H "Content-Type: application/json" -d "$data" "$url")
    message=$(echo "$response" | jq -r '.message')
    [[ "$message" == "$expected_message" ]] || handle_error "$response"
}

# Function to make a PUT request and check the response
put_request() {
    local url="$1"
    local data="$2"
    local expected_message="$3"

    response=$(curl -s -X PUT -H "Content-Type: application/json" -d "$data" "$url")
    message=$(echo "$response" | jq -r '.message')
    [[ "$message" == "$expected_message" ]] || handle_error "$response"
}

# Function to get rows and print them
get_rows() {
    local url="$1"

    response=$(curl -s -X GET "$url")
    echo "Rows in the dynamic table:"
    echo "$response" | jq '.'
}

# Step 1: Create dynamic table
echo "Step 1: Creating dynamic table named: $TABLE_NAME"
post_request "$API_BASE_URL/table" "{\"name\": \"$TABLE_NAME\", \"fields\": $FIELDS}" "Table created successfully"
table_id=$(echo "$response" | jq -r '.table_id')
echo "Dynamic table created successfully. Table ID: $table_id"

# Step 2: Add row to the table
echo "Step 2: Adding row to the dynamic table"
post_request "$API_BASE_URL/table/$table_id/row" "$ROW_DATA" "Row added successfully"

# Step 2a: Get and display all rows in the table
echo "Step 2a: Getting all rows from the dynamic table"
get_rows "$API_BASE_URL/table/$table_id/rows"

# Step 3: Update table by adding a new column
echo "Step 3: Updating table by adding a new column"
put_request "$API_BASE_URL/table/$table_id" "{\"fields\": $NEW_FIELD}" "Table updated successfully"

# Step 4: Add row with new column to the table
echo "Step 4: Adding row with new column to the dynamic table"
post_request "$API_BASE_URL/table/$table_id/row" "$NEW_ROW_DATA" "Row added successfully"

# Step 5: Get and display all rows in the table
echo "Step 5: Getting all rows from the dynamic table"
get_rows "$API_BASE_URL/table/$table_id/rows"
