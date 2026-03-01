from aws_cdk import (
    Stack,
    aws_iam as iam
)
from constructs import Construct


class IamStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        self.lambda_role = iam.Role(
            self, "LambdaCrudRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            description="Role for William_Phase2 Lambda functions"
        )

        # 1. Basic logging
        self.lambda_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"))

        # 2. X-Ray
        self.lambda_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AWSXRayDaemonWriteAccess"))

        # 3. DynamoDB
        self.lambda_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonDynamoDBFullAccess"))

        # 4. OpenSearch
        self.lambda_role.add_to_policy(iam.PolicyStatement(
            sid="AllowOpenSearchAccess",
            effect=iam.Effect.ALLOW,
            actions=["es:*"],
            resources=["*"]))

        # 5. DynamoDB Streams
        self.lambda_role.add_to_policy(iam.PolicyStatement(
            sid="AllowDynamoDBStreams",
            effect=iam.Effect.ALLOW,
            actions=["dynamodb:GetShardIterator", "dynamodb:DescribeStream",
                     "dynamodb:ListStreams", "dynamodb:GetRecords"],
            resources=["*"]))

        # 6. S3
        self.lambda_role.add_to_policy(iam.PolicyStatement(
            sid="AllowS3Access",
            effect=iam.Effect.ALLOW,
            actions=["s3:PutObject", "s3:GetObject", "s3:DeleteObject", "s3:ListBucket"],
            resources=["*"]))

        # 7. SQS
        self.lambda_role.add_to_policy(iam.PolicyStatement(
            sid="AllowSQSAccess",
            effect=iam.Effect.ALLOW,
            actions=["sqs:SendMessage", "sqs:ReceiveMessage",
                     "sqs:DeleteMessage", "sqs:GetQueueAttributes"],
            resources=["*"]))

        # 8. Step Functions - allows Lambda to be invoked by Step Functions
        self.lambda_role.add_to_policy(iam.PolicyStatement(
            sid="AllowStepFunctions",
            effect=iam.Effect.ALLOW,
            actions=["states:StartExecution", "states:StartSyncExecution",
                     "states:DescribeExecution", "states:StopExecution"],
            resources=["*"]))

        # --- API Gateway role to invoke Step Functions ---
        self.apigw_sfn_role = iam.Role(
            self, "ApiGwStepFunctionsRole",
            assumed_by=iam.ServicePrincipal("apigateway.amazonaws.com"),
            description="Allows API Gateway to invoke Step Functions synchronously"
        )

        self.apigw_sfn_role.add_to_policy(iam.PolicyStatement(
            sid="AllowStartSyncExecution",
            effect=iam.Effect.ALLOW,
            actions=["states:StartSyncExecution"],
            resources=["*"]))