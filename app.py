#!/usr/bin/env python3
import aws_cdk as cdk

from group4_project.group4_project_stack import Group4ProjectStack


app = cdk.App()

# Unique per classmate so parallel deploys don't overwrite each other.
# Required for any cdk command, e.g.:
#   cdk deploy -c name=rl
#   cdk destroy -c name=rl
#   ./scripts/setup.sh rl
name = app.node.try_get_context("name")
if not name:
    raise ValueError("use format: cdk deploy -c name=abc")

Group4ProjectStack(app, f"Group4ProjectStack-{name}")

app.synth()
