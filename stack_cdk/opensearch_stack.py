from aws_cdk import (
    Stack,
    aws_opensearchservice as opensearch,
    aws_iam as iam,
    RemovalPolicy
)
from constructs import Construct

class OpenSearchStack(Stack):
    # Change 'lambda_role' (object) to 'lambda_role_arn' (string)
    def __init__(self, scope: Construct, construct_id: str, lambda_role_arn: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.os_domain = opensearch.Domain(
            self, "MyOpenSearchDomain",
            version=opensearch.EngineVersion.OPENSEARCH_2_11,
            capacity=opensearch.CapacityConfig(
                data_node_instance_type="t3.small.search",
                data_nodes=1,
                multi_az_with_standby_enabled=False
            ),
            fine_grained_access_control=opensearch.AdvancedSecurityOptions(
                master_user_arn=lambda_role_arn # Use the string ARN directly
            ),
            encryption_at_rest=opensearch.EncryptionAtRestOptions(enabled=True),
            node_to_node_encryption=True,
            enforce_https=True,
            removal_policy=RemovalPolicy.DESTROY  
        )

        # To grant permissions without the object, we use the ARN to "import" the role
        role_to_grant = iam.Role.from_role_arn(self, "ImportedLambdaRole", lambda_role_arn)
        self.os_domain.grant_read_write(role_to_grant)

    @property
    def domain_endpoint(self) -> str:
        return self.os_domain.domain_endpoint