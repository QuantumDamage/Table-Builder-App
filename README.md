# Table-Builder-App
Simple backend for a table builder app, where the user can build tables dynamically.

## How to use:
There are 4 possible endpoints and request types associated with them:

 * POST /api/table - Generate dynamic Django model based on user provided fields types and titles. The field type can be a string, number, or Boolean.
 * PUT /api/table/:id - This end point allows the user to update the structure
of dynamically generated model.
 * POST /api/table/:id/row -  Allows the user to add rows to the dynamically
generated model while respecting the model schema
 * GET /api/table/:id/rows - Get all the rows in the dynamically generated model

## Limitations:

 * only adding new columns is implemented
 * every field is optional, so you can sent just new field
 * there is no row deleting

## Todo:

 * general clean up of tests - they are quite messy for now
 * add typing
 * write documentation, and clan up inline comments
 * improve consistency of views 

## Start and test:

 * `docker compose up --build`
 * exposed base url: localhost:8000
 
## Testing:

 * anytime: `docker compose exec web pytest -x`. Those are the tests running inside container and using Django structures.
 * while application is running: `./external_test.sh`. This is bash script which uses curl to communicate with API from outside of container.

## Remarks:
 * after starting app swagger is exposed at http://localhost:8000/swagger/ and redoc at http://localhost:8000/redoc/