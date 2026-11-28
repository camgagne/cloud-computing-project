import json
import os

import boto3

# connect to the users and follows tables.
users = boto3.resource("dynamodb").Table(os.environ["USERS_TABLE"])
follows = boto3.resource("dynamodb").Table(os.environ["FOLLOWS_TABLE"])

# API Gateway runs this function for GET /users/{userId}.
def handler(event, context):
    # get userId from path parameters
    user_id = event["pathParameters"]["userId"]
    viewer_id = event["requestContext"]["authorizer"]["jwt"]["claims"]["sub"]

    user = users.get_item(Key={"userId": user_id}).get("Item")
    if not user:
        # 404 = "Not Found"; send an error message back to the frontend
        return {"statusCode": 404, "body": json.dumps({"error": "User not found"})}

    # keep private fields off the response
    user.pop("email", None)
    user.pop("snsTopicArn", None)

    # Tell the frontend whether the signed-in user already follows this profile
    user["isSelf"] = viewer_id == user_id
    if user["isSelf"]:
        user["isFollowing"] = False
    else:
        follow = follows.get_item(
            Key={"followerId": viewer_id, "followeeId": user_id}
        ).get("Item")
        user["isFollowing"] = follow is not None

    # 200 = "OK"; send the retrieved user back to the frontend
    # default=int converts DynamoDB's Decimal numbers (like followerCount) for JSON
    return {"statusCode": 200, "body": json.dumps(user, default=int)}
