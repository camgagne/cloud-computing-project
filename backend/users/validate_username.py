import os
import re
import boto3

from botocore.exceptions import ClientError

# Connect to the Usernames table
usernames = boto3.resource("dynamodb").Table(
    os.environ["USERNAMES_TABLE"]
)


def handler(event, context):

    # Retrieve attributes provided during registration
    attrs = event["request"]["userAttributes"]

    # Retrieve the requested username
    username = attrs.get("preferred_username", "")

    # Validate username format
    if not re.fullmatch(r"[a-zA-Z0-9_]{3,20}", username):
        raise Exception(
            "Username must contain 3-20 letters, numbers, or underscores."
        )

    # Normalize username for case-insensitive uniqueness
    username_lower = username.lower()

    try:

        # Reserve the username only if it does not already exist
        usernames.put_item(
            Item={
                "usernameLower": username_lower,
                "username": username
            },
            ConditionExpression="attribute_not_exists(usernameLower)"
        )

    except ClientError as err:

        # Username already exists
        if err.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise Exception("Username is already taken.")

        # Handle unexpected AWS errors
        raise

    # Allow Cognito to continue registration
    return event