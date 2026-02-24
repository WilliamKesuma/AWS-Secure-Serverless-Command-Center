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
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com")
        )

        # Basic logging permissions
        self.lambda_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "service-role/AWSLambdaBasicExecutionRole"
            )
        )

        # FULL DynamoDB access (as required)
        self.lambda_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "AmazonDynamoDBFullAccess"
            )
        )