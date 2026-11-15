from aws_cdk import (
    # Duration,
    Stack,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    # aws_sqs as sqs,
)
from constructs import Construct

class Group4ProjectStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here

        # example resource
        # queue = sqs.Queue(
        #     self, "Group4ProjectQueue",
        #     visibility_timeout=Duration.seconds(300),
        # )

        home_page_function = _lambda.Function(
            self,
            "HomePageFunction",
            runtime = _lambda.Runtime.NODEJS_20_X,
            code = _lambda.Code.from_asset("lambda"),
            handler = "homePage.handler",
        )

        api = apigateway.LambdaRestApi(
            self,
            "HomePageApi",
            handler=home_page_function,
            proxy=False,
        )

        api.root.add_method("GET")
        home_page_resource = api.root.add_resource("home")
        home_page_resource.add_method("GET")
