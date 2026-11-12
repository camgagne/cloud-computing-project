import aws_cdk as core
import aws_cdk.assertions as assertions

from group4_project.group4_project_stack import Group4ProjectStack

# example tests. To run these tests, uncomment this file along with the example
# resource in group4_project/group4_project_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = Group4ProjectStack(app, "group4-project")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
