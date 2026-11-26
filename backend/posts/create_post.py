import json
import os
import uuid
from datetime import datetime, timezone

import boto3

# connect to the Posts table.
posts = boto3.resource("dynamodb").Table(os.environ["POSTS_TABLE"])

# API Gateway runs this function for POST /posts.
# the frontend calls it after the image has already been uploaded to S3.
def handler(event, context):
    user_id = event["requestContext"]["authorizer"]["jwt"]["claims"]["sub"]
    body = json.loads(event.get("body") or "{}")
    # get image key and caption
    image_key = body.get("imageKey", "")
    caption = body.get("caption", "")

    # Only allow images from this user's own upload folder
    if not image_key.startswith(f"posts/{user_id}/"):
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid imageKey"})}

    # create new post item
    post = {
        "userId": user_id,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "postId": str(uuid.uuid4()),
        "imageKey": image_key,
        "caption": caption,
        "likeCount": 0,
        "commentCount": 0,
    }
    # store post in Posts table
    posts.put_item(Item=post)

    # 201 = "created"; send the saved post back to the frontend
    return {"statusCode": 201, "body": json.dumps(post)}