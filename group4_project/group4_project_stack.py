from aws_cdk import (
    RemovalPolicy,
    Stack,
    CfnOutput,
    aws_s3 as s3,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_s3_deployment as s3deploy,
    aws_cognito as cognito,
)
from constructs import Construct


class Group4ProjectStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Cognito handles signup / login / email verification for the SPA.
        # Amplify talks to Cognito directly — no Lambda required for auth.
        user_pool = cognito.UserPool(
            self, "UserPool",
            user_pool_name=f"Group4UserPool-{construct_id}",
            self_sign_up_enabled=True,
            sign_in_aliases=cognito.SignInAliases(email=True),
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            standard_attributes=cognito.StandardAttributes(
                email=cognito.StandardAttribute(required=True, mutable=True),
            ),
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=True,
            ),
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
            removal_policy=RemovalPolicy.DESTROY,
        )

        user_pool_client = user_pool.add_client(
            "WebClient",
            user_pool_client_name="web",
            auth_flows=cognito.AuthFlow(user_srp=True),
            generate_secret=False,  # public SPA client — no client secret
        )

        CfnOutput(
            self, "UserPoolId",
            value=user_pool.user_pool_id,
            description="Cognito User Pool ID",
        )
        CfnOutput(
            self, "UserPoolClientId",
            value=user_pool_client.user_pool_client_id,
            description="Cognito App Client ID",
        )
        CfnOutput(
            self, "CognitoRegion",
            value=Stack.of(self).region,
            description="AWS region for Cognito",
        )

        # 1. Create an S3 bucket for the website
        website_bucket = s3.Bucket(
            self,
            "WebsiteBucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
            # For production, change to RemovalPolicy.RETAIN
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # 2. Create a CloudFront distribution for the S3 bucket
        distribution = cloudfront.Distribution(
            self, "WebsiteDistribution",
            default_root_object="index.html",
            default_behavior=cloudfront.BehaviorOptions(
                # Automatically creates an OAC and attaches the bucket policy
                origin=origins.S3BucketOrigin.with_origin_access_control(website_bucket),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
            ),
        )

        # 3. Deploy site + runtime Cognito config (no .env / rebuild needed)
        s3deploy.BucketDeployment(
            self, "DeployWebsite",
            sources=[
                s3deploy.Source.asset("./website-dist"),
                s3deploy.Source.json_data("config.json", {
                    "userPoolId": user_pool.user_pool_id,
                    "userPoolClientId": user_pool_client.user_pool_client_id,
                    "region": Stack.of(self).region,
                }),
            ],
            destination_bucket=website_bucket,
            distribution=distribution,
            distribution_paths=["/*"],
        )

        # 4. Output the live CloudFront URL
        CfnOutput(
            self, "DistributionDomainName",
            value=f"https://{distribution.distribution_domain_name}",
            description="The URL of the CloudFront distribution",
        )

        # Create a bucket for storing images (auth is in place; wire uploads next)
        # photo_bucket = s3.Bucket(
        #     self,
        #     "PhotoAlbumBucket",
        #     block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
        #     encryption=s3.BucketEncryption.S3_MANAGED,
        #     enforce_ssl=True,
        #     removal_policy=RemovalPolicy.DESTROY,
        #     auto_delete_objects=True,
        # )
