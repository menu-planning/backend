import os

from src.contexts.products_catalog.aws_lambda.search_product_similar_name import lambda_handler

# Define a mock event (with URL-encoded name)
event = {
    "pathParameters": {"name": "banana%20ma%C3%A7%C3%A3"},
    "requestContext": {"authorizer": {"claims": {"sub": "mocked-user-id"}}},
}

os.environ["IS_LOCALSTACK"] = "true"

# Mock context (can be empty)
context = {}

# Call the lambda handler
lambda_handler(event, context)
