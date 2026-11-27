import json
import os
import boto3

from boto3.dynamodb.conditions import Key

# Connect to the Users table
users = boto3.resource("dynamodb").Table(
    os.environ["USERS_TABLE"]
)


def handler(event, context):

    params = event.get("queryStringParameters") or {}

    # Get the search term and make it lowercase
    search = params.get("q", "").strip().lower()

    if not search:
        return {
            "statusCode": 200,
            "body": json.dumps([])
        }

    # Query the username index for matching users
    response = users.query(
        IndexName="byUsername",

        KeyConditionExpression=(
            Key("searchBucket").eq("USER") &
            Key("usernameLower").begins_with(search)
        ),

        Limit=20
    )

    # Only return information needed for search results
    results = []

    for user in response["Items"]:
        results.append({
            "userId": user["userId"],
            "username": user["username"]
        })

    return {
        "statusCode": 200,
        "body": json.dumps(results)
    }