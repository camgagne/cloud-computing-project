from aws_cdk import (
    RemovalPolicy,
    Stack,
    CfnOutput,
    aws_s3 as s3,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_s3_deployment as s3deploy,
    aws_cognito as cognito,
    aws_lambda as lambda_,
    aws_apigatewayv2 as apigw
)

from aws_cdk.aws_apigatewayv2_authorizers import (
    HttpUserPoolAuthorizer
)

from aws_cdk.aws_apigatewayv2_integrations import (
    HttpLambdaIntegration
)
from constructs import Construct
from .init_database import DatabaseConstruct 

class Group4ProjectStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # initialize database
        self.db = DatabaseConstruct(self, "Database")

        # Cognito handles signup / login / email verification
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
            generate_secret=False,
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

        # VALIDATE_USERNAME
        # Create Lambda to validate usernames before signup
        validate_username_fn = lambda_.Function(
            self,
            "ValidateUsername",

            runtime=lambda_.Runtime.PYTHON_3_12,

            handler="users.validate_username.handler",

            code=lambda_.Code.from_asset("backend"),

            environment={
                "USERNAMES_TABLE": self.db.usernames_table.table_name
            }
        )
        # Allow Lambda to reserve usernames
        self.db.usernames_table.grant_write_data(
            validate_username_fn
        )
        # Execute Lambda before Cognito creates an account
        user_pool.add_trigger(
            cognito.UserPoolOperation.PRE_SIGN_UP,
            validate_username_fn
        )

        # INIT_USER
        # create lambda function for creating user in dynamo after cognito confirmation
        post_confirm = lambda_.Function(self, "PostConfirmation",
        runtime=lambda_.Runtime.PYTHON_3_12,
        handler="users.init_user.handler",      # backend/users/init_user.py
        code=lambda_.Code.from_asset("backend"),
        environment={"USERS_TABLE": self.db.users_table.table_name},
        )
        # allow this Lambda to write to the Users table
        self.db.users_table.grant_write_data(post_confirm)
        # add lambda as trigger for cognito post confirmation
        user_pool.add_trigger(cognito.UserPoolOperation.POST_CONFIRMATION, post_confirm)


        # Create an S3 bucket for the website
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

        # Create a CloudFront distribution for the S3 bucket
        distribution = cloudfront.Distribution(
            self, "WebsiteDistribution",
            default_root_object="index.html",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3BucketOrigin.with_origin_access_control(website_bucket),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
            ),
        )

        # Output the live CloudFront URL
        CfnOutput(
            self, "DistributionDomainName",
            value=f"https://{distribution.distribution_domain_name}",
            description="The URL of the CloudFront distribution",
        )

        #s3 bucket for storing images   
        image_bucket = s3.Bucket(
            self,
            "ImageBucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
            cors=[
                s3.CorsRule(
                    #allowed all origins for now, eventually the domain name given from deployment would be here
                    allowed_origins=["*"],
                    allowed_methods=[
                        s3.HttpMethods.PUT,
                        s3.HttpMethods.GET
                    ],
                    allowed_headers=["*"]
                )
            ]
        )

        # Create the Lambda function responsible for generating upload URLs
        upload_function = lambda_.Function(
            self,
            "ImageUploadFunction",

            # Lambda will execute our code using Python 3.12
            runtime=lambda_.Runtime.PYTHON_3_12,

            # First "handler" refers to handler.py
            # Second "handler" refers to the function inside handler.py
            # handler="handler.handler",
            # changed to use create_upload.py instead of handler.py
            handler="posts.create_upload.handler",

            # Location of the Lambda source code in our repository
            code=lambda_.Code.from_asset(
                #"lambda_functions/upload"
                # changed to use backend instead of lambda_functions/upload
                "backend"
            ),

            # Environment variables
            environment={
                "BUCKET_NAME": image_bucket.bucket_name
            }
        )

        # Give Lambda permission to upload objects under posts/
        image_bucket.grant_put(upload_function, "posts/*")  

        # Create an authorizer using our existing Cognito User Pool
        # This allows API Gateway to verify a user's authentication token
        authorizer = HttpUserPoolAuthorizer(
            "UploadAuthorizer",

            # The User Pool already defined earlier in our stack
            user_pool,

            # Only accept tokens for our existing application client
            user_pool_clients=[user_pool_client]
        )

        # Create an HTTP API that our React application can communicate with
        api = apigw.HttpApi(
            self,
            "ProjectApi",

            # Configure CORS for requests from our frontend to the API
            cors_preflight=apigw.CorsPreflightOptions(
                #this can be changed when website is fully implemented
                allow_origins=["*"],

                # Allow POST & GET requests
                allow_methods=[
                    apigw.CorsHttpMethod.POST,
                    apigw.CorsHttpMethod.GET
                ],

                # Allow the frontend to send authentication and JSON data
                allow_headers=[
                    "Authorization",
                    "Content-Type"
                ]
            )
        )

        # Create an endpoint at /upload
        api.add_routes(
            path="/upload",

            # This endpoint accepts HTTP POST requests
            methods=[apigw.HttpMethod.POST],

            # Execute our upload Lambda whenever this endpoint is called
            integration=HttpLambdaIntegration(
                "UploadIntegration",
                upload_function
            ),

            # Require Cognito authentication before executing Lambda
            authorizer=authorizer
        )

        # Output the API URL after deploying the CDK stack
        CfnOutput(
            self,
            "ApiUrl",
            value=api.api_endpoint,
            description="API Gateway URL"
        )
        #Moved this down to add image upload
        #Deploy site + runtime Cognito config 
        s3deploy.BucketDeployment(
            self,
            "DeployWebsite",
            sources=[
                s3deploy.Source.asset("./website-dist"),
                s3deploy.Source.json_data("config.json", {
                    "userPoolId": user_pool.user_pool_id,
                    "userPoolClientId": user_pool_client.user_pool_client_id,
                    "region": Stack.of(self).region,
                    "apiUrl": api.api_endpoint,
                }),
            ],
            destination_bucket=website_bucket,
            distribution=distribution,
            distribution_paths=["/*"],        
        )



        # CREATE_POST
        # create post using create_post.py lambda function
        create_post_fn = lambda_.Function(self, "CreatePost",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="posts.create_post.handler",        # backend/posts/create_post.py
            code=lambda_.Code.from_asset("backend"),
            environment={"POSTS_TABLE": self.db.posts_table.table_name},
        )
        # allow this lambda to write to the Posts table
        self.db.posts_table.grant_write_data(create_post_fn)

        # connect POST /posts on the API to this Lambda.
        # the Cognito authorizer rejects requests without a valid login token.
        api.add_routes(
            path="/posts",
            methods=[apigw.HttpMethod.POST],
            integration=HttpLambdaIntegration("CreatePostIntegration", create_post_fn),
            authorizer=authorizer,
        )



        # GET_USER
        # Lambda that returns one user's info, for GET /users/{userId}
        get_user_fn = lambda_.Function(self, "GetUser",
            runtime=lambda_.Runtime.PYTHON_3_12,

            # "users.get_user.handler" = backend/users/get_user.py, function handler()
            handler="users.get_user.handler",

            # Upload the whole backend/ folder as this Lambda's code
            code=lambda_.Code.from_asset("backend"),

            # Tell the Lambda the real (generated) name of the Users table
            environment={"USERS_TABLE": self.db.users_table.table_name},
        )

        # Allow this Lambda to read from the Users table
        self.db.users_table.grant_read_data(get_user_fn)

        # Connect GET /users/{userId} on the API to this Lambda.
        # The Cognito authorizer rejects requests without a valid login token.
        api.add_routes(
            path="/users/{userId}",
            methods=[apigw.HttpMethod.GET],
            integration=HttpLambdaIntegration("GetUserIntegration", get_user_fn),
            authorizer=authorizer,
        )



        # GET_USER_POSTS
        # Lambda that returns one user's posts, for GET /users/{userId}
        get_user_posts_fn = lambda_.Function(self, "GetUserPosts",
            runtime=lambda_.Runtime.PYTHON_3_12,

            # "users.get_user_posts.handler" = backend/users/get_user_posts.py, function handler()
            handler="users.get_user_posts.handler",

            # Upload the whole backend/ folder as this Lambda's code
            code=lambda_.Code.from_asset("backend"),

            # Tell the Lambda the real (generated) name of the Posts table
            environment={"POSTS_TABLE": self.db.posts_table.table_name,
                          "IMAGE_BUCKET": image_bucket.bucket_name},
        )

        # Allow this Lambda to read from the Posts table
        self.db.posts_table.grant_read_data(get_user_posts_fn)
        # Allow this Lambda to read from the Image bucket
        image_bucket.grant_read(get_user_posts_fn)

        # Connect GET /users/{userId} on the API to this Lambda.
        # The Cognito authorizer rejects requests without a valid login token.
        api.add_routes(
            path="/users/{userId}/posts",
            methods=[apigw.HttpMethod.GET],
            integration=HttpLambdaIntegration("GetUserPostsIntegration", get_user_posts_fn),
            authorizer=authorizer,
        )

        # Create the Lambda function for searching users
        search_users_fn = lambda_.Function(
            self,
            "SearchUsers",

            runtime=lambda_.Runtime.PYTHON_3_12,

            handler="users.search_users.handler",

            code=lambda_.Code.from_asset("backend"),

            environment={
                "USERS_TABLE": self.db.users_table.table_name
            }
        )

        # Allow Lambda to read from the Users table
        self.db.users_table.grant_read_data(search_users_fn)

        # Connect GET /users/search to the Lambda function
        api.add_routes(
            path="/users/search",
            methods=[apigw.HttpMethod.GET],
            integration=HttpLambdaIntegration(
                "SearchUsersIntegration",
                search_users_fn
            ),

            authorizer=authorizer
        )