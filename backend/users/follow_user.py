import json
import os
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError

users = boto3.resource("dynamodb").Table(os.environ["USERS_TABLE"])
follows = boto3.resource("dynamodb").Table(os.environ["FOLLOWS_TABLE"])


# API Gateway runs this for POST /users/{userId}/follow.
def handler(event, context):
    follower_id = event["requestContext"]["authorizer"]["jwt"]["claims"]["sub"]
    followee_id = event["pathParameters"]["userId"]

    if follower_id == followee_id:
        return {"statusCode": 400, "body": json.dumps({"error": "Cannot follow yourself"})}

    followee = users.get_item(Key={"userId": followee_id}).get("Item")
    if not followee:
        return {"statusCode": 404, "body": json.dumps({"error": "User not found"})}

    try:
        follows.put_item(
            Item={
                "followerId": follower_id,
                "followeeId": followee_id,
                "createdAt": datetime.now(timezone.utc).isoformat(),
            },
            ConditionExpression="attribute_not_exists(followerId) AND attribute_not_exists(followeeId)",
        )
    except ClientError as err:
        if err.response["Error"]["Code"] == "ConditionalCheckFailedException":
            # Already following — treat as success
            return {"statusCode": 200, "body": json.dumps({"following": True})}
        raise

    # Keep denormalized counts in sync on both users
    users.update_item(
        Key={"userId": follower_id},
        UpdateExpression="ADD followingCount :one",
        ExpressionAttributeValues={":one": 1},
    )
    users.update_item(
        Key={"userId": followee_id},
        UpdateExpression="ADD followerCount :one",
        ExpressionAttributeValues={":one": 1},
    )

    return {"statusCode": 200, "body": json.dumps({"following": True})}
