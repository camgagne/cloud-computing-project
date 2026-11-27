import json
import os

import boto3
from boto3.dynamodb.conditions import Key

# connect to the posts table.
posts = boto3.resource("dynamodb").Table(os.environ["POSTS_TABLE"])
s3 = boto3.client("s3")
IMAGE_BUCKET = os.environ["IMAGE_BUCKET"]


# API Gateway runs this function for GET /users/{userId}/posts.
def handler(event, context):
    # get posts from specific user
    user_id = event["pathParameters"]["userId"]

    # query all posts by this user, sorted by createdAt
    # ScanIndexForward=False sorts by createdAt, newest first.
    items = posts.query(KeyConditionExpression=Key("userId").eq(user_id), 
    ScanIndexForward=False,
    )["Items"]  # returns a dictionary with an "Items" key containing the list of posts

    # the images bucket is private, so give each post a temporary URL the browser 
    # can use to display its image
    for post in items:
        post["imageUrl"] = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": IMAGE_BUCKET, "Key": post["imageKey"]},
            ExpiresIn=3600,    # link works for 1 hour
        )

    # default=int converts DynamoDB's Decimal numbers (likeCount etc.) for JSON
    return {"statusCode": 200, "body": json.dumps(items, default=int)}