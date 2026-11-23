from aws_cdk import (
    Duration,
    RemovalPolicy,
    Stack,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    CfnOutput,
    aws_s3 as s3,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_s3_deployment as s3deploy,
    aws_cognito as cognito,
)
from aws_cdk.aws_cognito import UserPool
from constructs import Construct

class Group4ProjectStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)


        # user_pool = UserPool(
        #     self, "UserPool",
        #     user_pool_name="MyUserPool",
        #     self_sign_up_enabled=True,
        #     sign_in_aliases=cognito.SignInAliases(email=True),
        #     auto_verify=cognito.AutoVerifiedAttrs(email=True),
        #     password_policy=cognito.PasswordPolicy(
        #         min_length=8,
        #         require_lowercase=True,
        #         require_uppercase=True,
        #         require_digits=True,
        #         require_symbols=True,
        #     ),
        #     password_policy_recovery=cognito.AccountRecovery.EMAIL_ONLY,
        #     removal_policy=RemovalPolicy.DESTROY,  # For production, change to RemovalPolicy.RETAIN
        # )

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

        # 3. Deploy local site files to S3 and invalidate the CloudFront cache
        s3deploy.BucketDeployment(
            self, "DeployWebsite",
            sources=[s3deploy.Source.asset("./website-dist")],  # Path to your built site
            destination_bucket=website_bucket,
            distribution=distribution,  # Automatically invalidates CloudFront cache on deploy
            distribution_paths=["/*"],
        )

        # 4. Output the live CloudFront URL
        CfnOutput(
            self, "DistributionDomainName",
            value=f"https://{distribution.distribution_domain_name}",
            description="The URL of the CloudFront distribution",
        )

        #Create a bucket for storing images 
        #going to wait on this until we add user auth
        """photo_bucket = s3.Bucket(
            self,
            "PhotoAlbumBucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )"""
