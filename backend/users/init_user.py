# Creates a user after Cognito confirmation and adds them to the database. This is called by the Cognito post-confirmation Lambda trigger.

import os
import boto3

# Connect to the Users table and SNS.
users = boto3.resource("dynamodb").Table(os.environ["USERS_TABLE"])
sns = boto3.client("sns")

# gets called after a user confirms their signup in cognito. Creates a user item in the Users table.
def handler(event, context):
    if event["triggerSource"] == "PostConfirmation_ConfirmSignUp":
        # The new user's info, sent by cognito
        attrs = event["request"]["userAttributes"]
        username = attrs.get("preferred_username", "").strip() or attrs["sub"]
        email = attrs.get("email", "")
        user_id = attrs["sub"]

        # Per-user SNS topic so only this user gets post-created emails
        topic_arn = ""
        if email:
            topic_arn = sns.create_topic(
                Name=f"post-created-{user_id}",
                Attributes={"DisplayName": "Post Created Notifications"},
            )["TopicArn"]
            # SNS emails a one-time confirmation link; user must click it
            # before post-created notifications are delivered.
            sns.subscribe(
                TopicArn=topic_arn,
                Protocol="email",
                Endpoint=email,
            )

        # create user item in dynamodb
        users.put_item(Item={
            "userId": user_id,
            "username": username,
            "usernameLower": username.lower(),
            "searchBucket": "USER",
            "email": email,
            "snsTopicArn": topic_arn,
            "bio": "",
            "followerCount": 0,
            "followingCount": 0,
        })
    return event
