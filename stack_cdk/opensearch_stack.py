from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_opensearchservice as opensearch,
    aws_iam as iam,
)
from constructs import Construct


class OpenSearchStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, lambda_role_arn: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Import the Lambda role using its ARN
        role_to_grant = iam.Role.from_role_arn(self, "ImportedLambdaRole", lambda_role_arn)

        self.os_domain = opensearch.Domain(
            self, "MyOpenSearchDomain",
            version=opensearch.EngineVersion.OPENSEARCH_2_11,
            capacity=opensearch.CapacityConfig(
                data_node_instance_type="t3.small.search",
                data_nodes=1,
                multi_az_with_standby_enabled=False
            ),
            # No fine-grained access control - allows SSO role to access Dashboard directly
            encryption_at_rest=opensearch.EncryptionAtRestOptions(enabled=True),
            node_to_node_encryption=True,
            enforce_https=True,
            # Allow both Lambda role and SSO admin role
            access_policies=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    principals=[iam.ArnPrincipal(lambda_role_arn)],
                    actions=["es:*"],
                    resources=["*"]
                ),
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    principals=[iam.ArnPrincipal(
                        "arn:aws:iam::078646182048:role/aws-reserved/sso.amazonaws.com/ap-southeast-1/AWSReservedSSO_AdministratorAccess_aad2ada13f3171bf"
                    )],
                    actions=["es:*"],
                    resources=["*"]
                )
            ],
            removal_policy=RemovalPolicy.DESTROY
        )

        # Grant read/write to Lambda role
        self.os_domain.grant_read_write(role_to_grant)

    @property
    def domain_endpoint(self) -> str:
        return self.os_domain.domain_endpoint