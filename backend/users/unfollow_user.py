import json
import os

import boto3
from botocore.exceptions import ClientError

users = boto3.resource("dynamodb").Table(os.environ["USERS_TABLE"])
follows = boto3.resource("dynamodb").Table(os.environ["FOLLOWS_TABLE"])


# API Gateway runs this for POST /users/{userId}/unfollow.
def handler(event, context):
    follower_id = event["requestContext"]["authorizer"]["jwt"]["claims"]["sub"]
    followee_id = event["pathParameters"]["userId"]

    if follower_id == followee_id:
        return {"statusCode": 400, "body": json.dumps({"error": "Cannot unfollow yourself"})}

    try:
        follows.delete_item(
            Key={"followerId": follower_id, "followeeId": followee_id},
            ConditionExpression="attribute_exists(followerId) AND attribute_exists(followeeId)",
        )
    except ClientError as err:
        if err.response["Error"]["Code"] == "ConditionalCheckFailedException":
            # Not following — treat as success
            return {"statusCode": 200, "body": json.dumps({"following": False})}
        raise

    _decrement_count(follower_id, "followingCount")
    _decrement_count(followee_id, "followerCount")

    return {"statusCode": 200, "body": json.dumps({"following": False})}


def _decrement_count(user_id, attr):
    try:
        users.update_item(
            Key={"userId": user_id},
            UpdateExpression=f"ADD {attr} :neg",
            ExpressionAttributeValues={":neg": -1, ":zero": 0},
            ConditionExpression=f"{attr} > :zero",
        )
    except ClientError as err:
        if err.response["Error"]["Code"] != "ConditionalCheckFailedException":
            raise
