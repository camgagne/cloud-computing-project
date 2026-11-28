import base64
import json
import os

import boto3
from boto3.dynamodb.conditions import Key

# Home feed: newest posts across all users, 10 at a time.
posts = boto3.resource("dynamodb").Table(os.environ["POSTS_TABLE"])
users = boto3.resource("dynamodb").Table(os.environ["USERS_TABLE"])
s3 = boto3.client("s3")
IMAGE_BUCKET = os.environ["IMAGE_BUCKET"]
PAGE_SIZE = 10


def handler(event, context):
    params = event.get("queryStringParameters") or {}
    exclusive_start_key = _decode_token(params.get("nextToken"))

    query = {
        "IndexName": "byFeed",
        "KeyConditionExpression": Key("feedBucket").eq("ALL"),
        "ScanIndexForward": False,  # newest first
        "Limit": PAGE_SIZE,
    }
    if exclusive_start_key:
        query["ExclusiveStartKey"] = exclusive_start_key

    result = posts.query(**query)
    items = result.get("Items", [])

    # Attach temporary image URLs and author usernames for the frontend
    username_cache = {}
    for post in items:
        post["imageUrl"] = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": IMAGE_BUCKET, "Key": post["imageKey"]},
            ExpiresIn=3600,
        )
        user_id = post["userId"]
        if user_id not in username_cache:
            user = users.get_item(Key={"userId": user_id}).get("Item") or {}
            username_cache[user_id] = user.get("username", "Unknown")
        post["username"] = username_cache[user_id]

    body = {
        "posts": items,
        "nextToken": _encode_token(result.get("LastEvaluatedKey")),
    }
    return {"statusCode": 200, "body": json.dumps(body, default=int)}


def _encode_token(last_key):
    if not last_key:
        return None
    return base64.urlsafe_b64encode(json.dumps(last_key).encode()).decode()


def _decode_token(token):
    if not token:
        return None
    try:
        return json.loads(base64.urlsafe_b64decode(token.encode()).decode())
    except Exception:
        return None
