import aws_cdk as core
import aws_cdk.assertions as assertions

from py_cdk_stacks.state_stack import StateStack
from py_cdk_stacks.compute_stack import ComputeStack

# example tests. To run these tests, uncomment this file along with the example
# resource in py_cdk/py_cdk_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = StateStack(app, "py-cdk")
    template = assertions.Template.from_stack(stack)


#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
