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
            # Fine-grained access control with Lambda role as master user
            # This allows the Lambda role to authenticate as admin to OpenSearch
            fine_grained_access_control=opensearch.AdvancedSecurityOptions(
                master_user_arn=lambda_role_arn
            ),
            # Required settings when fine-grained access control is enabled
            encryption_at_rest=opensearch.EncryptionAtRestOptions(enabled=True),
            node_to_node_encryption=True,
            enforce_https=True,
            # Resource-based access policy that allows the Lambda role to access the domain
            access_policies=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    principals=[iam.ArnPrincipal(lambda_role_arn)],
                    actions=["es:*"],
                    resources=["*"]  # Will be scoped to this domain automatically by CDK
                )
            ],
            removal_policy=RemovalPolicy.DESTROY
        )

        # Also grant read/write via CDK helper (adds additional resource policy)
        self.os_domain.grant_read_write(role_to_grant)

    @property
    def domain_endpoint(self) -> str:
        return self.os_domain.domain_endpoint