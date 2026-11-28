import json
import os
import uuid
from datetime import datetime, timezone

import boto3

# connect to the Posts and Users tables.
posts = boto3.resource("dynamodb").Table(os.environ["POSTS_TABLE"])
users = boto3.resource("dynamodb").Table(os.environ["USERS_TABLE"])
sns = boto3.client("sns")

# API Gateway runs this function for POST /posts.
# the frontend calls it after the image has already been uploaded to S3.
def handler(event, context):
    user_id = event["requestContext"]["authorizer"]["jwt"]["claims"]["sub"]
    body = json.loads(event.get("body") or "{}")
    # get image and caption
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
        # feedBucket lets the home page query newest posts across all users
        "feedBucket": "ALL",
    }
    # store post in Posts table
    posts.put_item(Item=post)

    # email the user via SNS to confirm their post was created
    _send_post_created_email(user_id, post)

    # 201 = "created"; send the saved post back to the frontend
    return {"statusCode": 201, "body": json.dumps(post)}


def _send_post_created_email(user_id, post):
    try:
        user = users.get_item(Key={"userId": user_id}).get("Item") or {}
        topic_arn = user.get("snsTopicArn")
        if not topic_arn:
            return

        caption = post.get("caption") or "(no caption)"
        message = (
            f"Your post was created successfully.\n\n"
            f"Post ID: {post['postId']}\n"
            f"Created at: {post['createdAt']}\n"
            f"Caption: {caption}\n"
        )
        sns.publish(
            TopicArn=topic_arn,
            Subject="Your post was created",
            Message=message,
        )
    except Exception:
        # Post is already saved; don't fail the request if email delivery fails.
        pass
