from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_apigateway as apigw
)
from constructs import Construct


class LambdaStack(Stack):

    def __init__(self, scope: Construct, construct_id: str,
                 user_table, product_table, iam_role, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # ---------- LAMBDA ----------
        create_user_fn = _lambda.Function(
            self, "CreateUserFn",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_asset("lambda/Functions/CreateUser"),
            role=iam_role,
            environment={"USER_TABLE": user_table.table_name}
        )

        get_users_fn = _lambda.Function(
            self, "GetUsersFn",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_asset("lambda/Functions/GetUsers"),
            role=iam_role,
            environment={"USER_TABLE": user_table.table_name}
        )

        get_user_by_id_fn = _lambda.Function(
            self, "GetUserByIdFn",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_asset("lambda/Functions/GetUserById"),
            role=iam_role,
            environment={"USER_TABLE": user_table.table_name}
        )

        update_user_fn = _lambda.Function(
            self, "UpdateUserFn",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_asset("lambda/Functions/UpdateUser"),
            role=iam_role,
            environment={"USER_TABLE": user_table.table_name}
        )

        delete_user_fn = _lambda.Function(
            self, "DeleteUserFn",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_asset("lambda/Functions/DeleteUser"),
            role=iam_role,
            environment={"USER_TABLE": user_table.table_name}
        )

        create_product_fn = _lambda.Function(
            self, "CreateProductFn",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_asset("lambda/Functions/CreateProduct"),
            role=iam_role,
            environment={"PRODUCT_TABLE": product_table.table_name}
        )

        get_product_fn = _lambda.Function(
            self, "GetProductFn",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_asset("lambda/Functions/GetProduct"),
            role=iam_role,
            environment={"PRODUCT_TABLE": product_table.table_name}
        )

        get_product_by_id_fn = _lambda.Function(
            self, "GetProductByIdFn",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_asset("lambda/Functions/GetProductById"),
            role=iam_role,
            environment={"PRODUCT_TABLE": product_table.table_name}
        )

        update_product_fn = _lambda.Function(
            self, "UpdateProductFn",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_asset("lambda/Functions/UpdateProduct"),
            role=iam_role,
            environment={"PRODUCT_TABLE": product_table.table_name}
        )

        delete_product_fn = _lambda.Function(
            self, "DeleteProductFn",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_asset("lambda/Functions/DeleteProduct"),
            role=iam_role,
            environment={"PRODUCT_TABLE": product_table.table_name}
        )

        # ---------- API GATEWAY ----------
        api = apigw.RestApi(
            self,
            "CrudApi",
            rest_api_name="CrudApi",
            deploy_options=apigw.StageOptions(stage_name="prod")
        )

        # /users
        users = api.root.add_resource("users")
        users.add_method("GET",  apigw.LambdaIntegration(get_users_fn))
        users.add_method("POST", apigw.LambdaIntegration(create_user_fn))

        # /users/{id}
        user_id = users.add_resource("{id}")
        user_id.add_method("GET",    apigw.LambdaIntegration(get_user_by_id_fn))
        user_id.add_method("PUT",    apigw.LambdaIntegration(update_user_fn))
        user_id.add_method("DELETE", apigw.LambdaIntegration(delete_user_fn))

        # /products
        products = api.root.add_resource("products")
        products.add_method("GET",  apigw.LambdaIntegration(get_product_fn))
        products.add_method("POST", apigw.LambdaIntegration(create_product_fn))

        # /products/{id}
        product_id = products.add_resource("{id}")
        product_id.add_method("GET",    apigw.LambdaIntegration(get_product_by_id_fn))
        product_id.add_method("PUT",    apigw.LambdaIntegration(update_product_fn))
        product_id.add_method("DELETE", apigw.LambdaIntegration(delete_product_fn))