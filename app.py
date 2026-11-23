#!/usr/bin/env python3
import os

import aws_cdk as cdk

from group4_project.group4_project_stack import Group4ProjectStack


app = cdk.App()

# in case we're working at the same time this makes sure we don't deploy a stack with the same name and overwrite each others code, would need to do this for any cdk command
name = app.node.try_get_context("name")
if not name:
    raise ValueError("use format: cdk deploy -c name=abc")
    # ex: cdk deploy -c name=rl
    # ex: cdk destroy -c name=rl
	
Group4ProjectStack(app, f"Group4ProjectStack-{name}")

    # If you don't specify 'env', this stack will be environment-agnostic.
    # Account/Region-dependent features and context lookups will not work,
    # but a single synthesized template can be deployed anywhere.

    # Uncomment the next line to specialize this stack for the AWS Account
    # and Region that are implied by the current CLI configuration.

    #env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),

    # Uncomment the next line if you know exactly what Account and Region you
    # want to deploy the stack to. */

    #env=cdk.Environment(account='123456789012', region='us-east-1'),

    # For more information, see https://docs.aws.amazon.com/cdk/latest/guide/environments.html

app.synth()
