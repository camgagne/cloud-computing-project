# Creates a user after Cognito confirmation and adds them to the database. This is called by the Cognito post-confirmation Lambda trigger.

import os
import boto3

# Connect to the Users table.
users = boto3.resource("dynamodb").Table(os.environ["USERS_TABLE"])

# gets called after a user confirms their signup in cognito. Creates a user item in the Users table.
def handler(event, context):
    if event["triggerSource"] == "PostConfirmation_ConfirmSignUp":
        # The new user's info, sent by cognito
        attrs = event["request"]["userAttributes"]
        username = event["userName"]
        # create user item in dynamodb
        users.put_item(Item={
            "userId": attrs["sub"],
            "username": username,
            "usernameLower": username.lower(),
            "searchBucket": "USER",
            "email": attrs.get("email", ""),
            "bio": "",
            "followerCount": 0,
            "followingCount": 0,
        })
    return event