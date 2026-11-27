import json
import os

import boto3

# connect to the users table.
users = boto3.resource("dynamodb").Table(os.environ["USERS_TABLE"])

# API Gateway runs this function for GET /users/{userId}.
def handler(event, context):
    # get userId from path parameters
    user_id = event["pathParameters"]["userId"]

    user = users.get_item(Key={"userId": user_id}).get("Item")
    if not user:
        # 404 = "Not Found"; send an error message back to the frontend
        return {"statusCode": 404, "body": json.dumps({"error": "User not found"})}

    # we'd want to keep user's email private
    # i'll uncomment this if we add usernames, but for now this is fine for testing
    #user.pop("email", None)

    # 200 = "OK"; send the retrieved user back to the frontend
    # default=int converts DynamoDB's Decimal numbers (like followerCount) for JSON
    return {"statusCode": 200, "body": json.dumps(user, default=int)}