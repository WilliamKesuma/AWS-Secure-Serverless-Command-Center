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
        self.lambda_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "AWSXRayDaemonWriteAccess"
            )
        )

        # 3. Full DynamoDB access (includes Streams read)
        self.lambda_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "AmazonDynamoDBFullAccess"
            )
        )

        # 4. OpenSearch access
        self.lambda_role.add_to_policy(
            iam.PolicyStatement(
                sid="AllowOpenSearchAccess",
                effect=iam.Effect.ALLOW,
                actions=["es:*"],
                resources=["*"]
            )
        )

        # 5. DynamoDB Streams read permission (required for stream Lambda trigger)
        self.lambda_role.add_to_policy(
            iam.PolicyStatement(
                sid="AllowDynamoDBStreams",
                effect=iam.Effect.ALLOW,
                actions=[
                    "dynamodb:GetShardIterator",
                    "dynamodb:DescribeStream",
                    "dynamodb:ListStreams",
                    "dynamodb:GetRecords"
                ],
                resources=["*"]
            )
        )