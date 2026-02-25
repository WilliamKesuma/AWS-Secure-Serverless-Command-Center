from aws_cdk import (
    Stack,
    Duration,
    aws_sqs as sqs
)
from constructs import Construct


class SqsStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # FIFO Queue - productId as MessageGroupId ensures
        # orders for the same product are processed in order
        self.order_queue = sqs.Queue(
            self, "OrderQueue",
            queue_name="OrderQueue.fifo",
            fifo=True,
            content_based_deduplication=True,
            visibility_timeout=Duration.seconds(30)
        )