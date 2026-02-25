from aws_cdk import (
    Stack,
    RemovalPolicy,
    Duration,
    aws_s3 as s3,
)
from constructs import Construct


class S3Stack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        self.bucket = s3.Bucket(
            self, "ProfileImagesBucket",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            cors=[s3.CorsRule(
                allowed_methods=[
                    s3.HttpMethods.GET,
                    s3.HttpMethods.PUT,
                    s3.HttpMethods.POST,
                ],
                allowed_origins=["*"],
                allowed_headers=["*"],
                max_age=3000
            )],
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="DeleteIncompleteUploads",
                    abort_incomplete_multipart_upload_after=Duration.days(1)
                )
            ]
        )