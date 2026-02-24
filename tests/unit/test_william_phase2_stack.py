import aws_cdk as core
import aws_cdk.assertions as assertions

from william_phase2.william_phase2_stack import WilliamPhase2Stack

# example tests. To run these tests, uncomment this file along with the example
# resource in william_phase2/william_phase2_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = WilliamPhase2Stack(app, "william-phase2")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
