import aws_cdk as core
import aws_cdk.assertions as assertions
import pytest

from group4_project.group4_project_stack import Group4ProjectStack


@pytest.fixture(scope="module")
def template():
    app = core.App()
    stack = Group4ProjectStack(app, "Group4ProjectStack-test")
    return assertions.Template.from_stack(stack)


def test_cognito_user_pool_configured(template):
    template.has_resource_properties(
        "AWS::Cognito::UserPool",
        {
            "AdminCreateUserConfig": {"AllowAdminCreateUserOnly": False},
            "AutoVerifiedAttributes": ["email"],
            "UsernameAttributes": ["email"],
            "Policies": {
                "PasswordPolicy": {
                    "MinimumLength": 8,
                    "RequireLowercase": True,
                    "RequireUppercase": True,
                    "RequireNumbers": True,
                    "RequireSymbols": True,
                }
            },
        },
    )


def test_website_and_image_buckets_created(template):
    template.resource_count_is("AWS::S3::Bucket", 2)


def test_image_bucket_allows_put_and_get_cors(template):
    buckets = template.find_resources("AWS::S3::Bucket")
    cors_buckets = [
        props
        for props in buckets.values()
        if "CorsConfiguration" in props.get("Properties", {})
    ]
    assert len(cors_buckets) == 1
    rules = cors_buckets[0]["Properties"]["CorsConfiguration"]["CorsRules"]
    assert any(
        set(rule.get("AllowedMethods", [])) >= {"PUT", "GET"} for rule in rules
    )


def test_cloudfront_serves_index_html(template):
    template.has_resource_properties(
        "AWS::CloudFront::Distribution",
        {
            "DistributionConfig": {
                "DefaultRootObject": "index.html",
            }
        },
    )


def test_dynamodb_tables_and_gsis_created(template):
    template.resource_count_is("AWS::DynamoDB::Table", 6)

    tables = template.find_resources("AWS::DynamoDB::Table")
    gsi_names = set()
    for props in tables.values():
        for gsi in props.get("Properties", {}).get("GlobalSecondaryIndexes", []):
            gsi_names.add(gsi["IndexName"])

    assert gsi_names == {"byUsername", "byFollowee", "byPostId", "byFeed"}


def test_upload_lambda_and_api_route_configured(template):
    template.has_resource_properties(
        "AWS::Lambda::Function",
        {
            "Handler": "posts.create_upload.handler",
            "Runtime": "python3.12",
        },
    )
    template.has_resource_properties(
        "AWS::ApiGatewayV2::Route",
        {
            "RouteKey": "POST /upload",
        },
    )


def test_create_post_lambda_can_publish_sns(template):
    template.has_resource_properties(
        "AWS::Lambda::Function",
        {
            "Handler": "posts.create_post.handler",
            "Runtime": "python3.12",
        },
    )
    template.has_resource_properties(
        "AWS::IAM::Policy",
        {
            "PolicyDocument": {
                "Statement": assertions.Match.array_with([
                    assertions.Match.object_like({
                        "Action": "sns:Publish",
                        "Effect": "Allow",
                    })
                ])
            }
        },
    )


def test_feed_and_follow_routes_configured(template):
    template.has_resource_properties(
        "AWS::Lambda::Function",
        {
            "Handler": "posts.get_feed.handler",
            "Runtime": "python3.12",
        },
    )
    template.has_resource_properties(
        "AWS::Lambda::Function",
        {
            "Handler": "users.follow_user.handler",
            "Runtime": "python3.12",
        },
    )
    template.has_resource_properties(
        "AWS::ApiGatewayV2::Route",
        {"RouteKey": "GET /posts"},
    )
    template.has_resource_properties(
        "AWS::ApiGatewayV2::Route",
        {"RouteKey": "POST /users/{userId}/follow"},
    )
    template.has_resource_properties(
        "AWS::ApiGatewayV2::Route",
        {"RouteKey": "POST /users/{userId}/unfollow"},
    )


def test_post_confirmation_lambda_can_create_sns_topic(template):
    template.has_resource_properties(
        "AWS::Lambda::Function",
        {
            "Handler": "users.init_user.handler",
            "Runtime": "python3.12",
        },
    )
    template.has_resource_properties(
        "AWS::IAM::Policy",
        {
            "PolicyDocument": {
                "Statement": assertions.Match.array_with([
                    assertions.Match.object_like({
                        "Action": assertions.Match.array_with([
                            "sns:CreateTopic",
                            "sns:Subscribe",
                        ]),
                        "Effect": "Allow",
                    })
                ])
            }
        },
    )
