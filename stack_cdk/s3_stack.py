from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_s3 as s3,
    aws_sns as sns,
    aws_s3_notifications as s3n,
)
from constructs import Construct

class S3Stack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # Create the bucket with no knowledge of who uses it
        self.bucket = s3.Bucket(
            self, "ProfileImagesBucket",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            cors=[s3.CorsRule(
                allowed_methods=[s3.HttpMethods.GET, s3.HttpMethods.PUT, s3.HttpMethods.POST],
                allowed_origins=["*"],
                allowed_headers=["*"]
            )]
        )

        # Topic to publish report-related object-created events. Using SNS breaks
        # the direct bucket->lambda CloudFormation reference and avoids cyclical
        # cross-stack dependencies (S3Stack stays independent).
        self.report_topic = sns.Topic(self, "ReportTopic")

        # Send only objects under `reports/` to SNS. The Lambda subscription
        # will be created in ReportingStack which depends on S3Stack (one-way).
        self.bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3n.SnsDestination(self.report_topic),
            s3.NotificationKeyFilter(prefix="reports/")
        )