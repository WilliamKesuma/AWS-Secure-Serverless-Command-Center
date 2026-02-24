from aws_cdk import (
    Stack,
    aws_iam as iam
)
from constructs import Construct


class IamStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # Role assumed by Lambda
        self.lambda_role = iam.Role(
            self,
            "LambdaCrudRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            description="Role for William_Phase2 Lambda functions with X-Ray and DynamoDB access"
        )

        # 1. Basic logging permissions (Allows writing to CloudWatch)
        self.lambda_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "service-role/AWSLambdaBasicExecutionRole"
            )
        )

        # 2. X-Ray Tracing permissions 
        # This fixes the "Potential missing permissions" error and allows tracer.put_annotation to work
        self.lambda_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "AWSXRayDaemonWriteAccess"
            )
        )

        # 3. FULL DynamoDB access
        self.lambda_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "AmazonDynamoDBFullAccess"
            )
        )