# PREVIOUSLY lambda_functions/handler.py
import boto3
import json
import os
import uuid
from botocore.config import Config

# Create an AWS S3 client using the Python AWS SDK
# Signature v4 is used to sign our temp upload URLs
s3 = boto3.client(
    "s3",
    config=Config(signature_version="s3v4")
)

# Get the bucket name from the Lambda environment variables
BUCKET_NAME = os.environ["BUCKET_NAME"]


# This function runs whenever API Gateway invokes Lambda
def handler(event, context):

    # Retrieve information from the Cognito token
    claims = event["requestContext"]["authorizer"]["jwt"]["claims"]

    # Make sure the user provided an access token
    if claims.get("token_use") != "access":
        return {
            "statusCode": 403,
            "body": json.dumps({
                "error": "Access token required"
            })
        }

    # Get the authenticated user's unique Cognito ID
    user_id = claims["sub"]

    # Convert the request body from JSON into a Python dictionary
    body = json.loads(event.get("body") or "{}")

    # Get the type of image the user wants to upload
    content_type = body.get("contentType")

    # Supported image types
    allowed_types = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/webp": "webp"
    }

    # in unsupported image
    if content_type not in allowed_types:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "error": "Invalid image type"
            })
        }

    # Generate a unique identifier so images do not overwrite images with the same name
    image_id = str(uuid.uuid4())

    # make sure filetype is allowed
    extension = allowed_types[content_type]

    # Create the location where the image will be stored in S3
    # Organize images according to their Cognito user ID (this could be used as an image path in dynamo)
    key = f"posts/{user_id}/{image_id}.{extension}"

    # Generate a temporary URL that allows the user to upload with an account created
    upload_url = s3.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": BUCKET_NAME,
            "Key": key,
            "ContentType": content_type
        }
    )

    # Return the upload URL and image location to React
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps({
            "uploadUrl": upload_url,
            "imageKey": key
        })
    }