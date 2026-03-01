from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_cognito as cognito,
    aws_lambda as _lambda,
)
from constructs import Construct

class CognitoStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, user_table, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # 1. Post-Confirmation Lambda (Syncs Cognito User to DynamoDB)
        self.post_confirm_fn = _lambda.Function(
            self, "PostConfirmSyncFn",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_asset("lambda/Functions/PostConfirmSync"),
            environment={
                "USER_TABLE": user_table.table_name
            }
        )
        user_table.grant_write_data(self.post_confirm_fn)

        # 2. User Pool
        self.user_pool = cognito.UserPool(
            self, "UserPool",
            user_pool_name="WilliamAppUserPool",
            self_sign_up_enabled=True,
            sign_in_aliases=cognito.SignInAliases(email=True),
            auto_verify=cognito.AutoVerifiedAttrs(email=True), 
            removal_policy=RemovalPolicy.DESTROY,
            lambda_triggers=cognito.UserPoolTriggers(
                post_confirmation=self.post_confirm_fn
            ),
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=False
            )
        )

        # 3. User Pool Client
        self.user_pool_client = self.user_pool.add_client(
            "UserPoolClient",
            auth_flows=cognito.AuthFlow(
                user_password=True,
                user_srp=True
            )
        )