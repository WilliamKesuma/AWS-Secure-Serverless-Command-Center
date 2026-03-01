from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as _lambda,
    aws_lambda_event_sources as lambda_events,
    aws_apigateway as apigw,
    aws_iam as iam,
    aws_events as events,
    aws_events_targets as targets,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as tasks,
)
from constructs import Construct

class LambdaStack(Stack):

    def __init__(self, scope: Construct, construct_id: str,
                 user_table, product_table, order_table, iam_role,
                 os_endpoint: str,
                 bucket_name: str,
                 report_bucket,
                 order_queue_url: str,
                 order_queue,
                 user_pool,
                 **kwargs):

        super().__init__(scope, construct_id, **kwargs)

        # Environment variable dictionaries
        os_env = {"OS_ENDPOINT": os_endpoint}
        s3_env = {"BUCKET_NAME": bucket_name}
        sqs_env = {"ORDER_QUEUE_URL": order_queue_url}

        # ---------- LAMBDA LAYER ----------
        self.utils_layer = _lambda.LayerVersion(
            self, "AppUtilsLayerV2",
            code=_lambda.Code.from_asset("lambda/Layer/utils_layer"),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_12],
            description="Shared utils for logging and tracing"
        )

        default_props = {
            "runtime": _lambda.Runtime.PYTHON_3_12,
            "handler": "lambda_function.lambda_handler",
            "role": iam_role,
            "layers": [self.utils_layer],
            "tracing": _lambda.Tracing.ACTIVE,
            "timeout": Duration.seconds(30)
        }

        # ---------- USER FUNCTIONS ----------
        self.main_fn = _lambda.Function(self, "CreateUserFn",
            code=_lambda.Code.from_asset("lambda/Functions/CreateUser"),
            environment={"USER_TABLE": user_table.table_name, **os_env}, **default_props)

        self.get_users_fn = _lambda.Function(self, "GetUsersFn",
            code=_lambda.Code.from_asset("lambda/Functions/GetUsers"),
            environment={"USER_TABLE": user_table.table_name, **os_env}, **default_props)

        self.get_user_by_id_fn = _lambda.Function(self, "GetUserByIdFn",
            code=_lambda.Code.from_asset("lambda/Functions/GetUserById"),
            environment={"USER_TABLE": user_table.table_name, **os_env}, **default_props)

        self.update_user_fn = _lambda.Function(self, "UpdateUserFn",
            code=_lambda.Code.from_asset("lambda/Functions/UpdateUser"),
            environment={"USER_TABLE": user_table.table_name, **os_env}, **default_props)

        self.delete_user_fn = _lambda.Function(self, "DeleteUserFn",
            code=_lambda.Code.from_asset("lambda/Functions/DeleteUser"),
            environment={"USER_TABLE": user_table.table_name, **os_env}, **default_props)

        # ---------- PRODUCT FUNCTIONS ----------
        self.create_product_fn = _lambda.Function(self, "CreateProductFn",
            code=_lambda.Code.from_asset("lambda/Functions/CreateProduct"),
            environment={"PRODUCT_TABLE": product_table.table_name, **os_env}, **default_props)

        self.get_product_fn = _lambda.Function(self, "GetProductFn",
            code=_lambda.Code.from_asset("lambda/Functions/GetProduct"),
            environment={"PRODUCT_TABLE": product_table.table_name, **os_env}, **default_props)

        self.get_product_by_id_fn = _lambda.Function(self, "GetProductByIdFn",
            code=_lambda.Code.from_asset("lambda/Functions/GetProductById"),
            environment={"PRODUCT_TABLE": product_table.table_name, **os_env}, **default_props)

        self.update_product_fn = _lambda.Function(self, "UpdateProductFn",
            code=_lambda.Code.from_asset("lambda/Functions/UpdateProduct"),
            environment={"PRODUCT_TABLE": product_table.table_name, **os_env}, **default_props)

        self.delete_product_fn = _lambda.Function(self, "DeleteProductFn",
            code=_lambda.Code.from_asset("lambda/Functions/DeleteProduct"),
            environment={"PRODUCT_TABLE": product_table.table_name, **os_env}, **default_props)

        # ---------- SEARCH, STREAM, S3 & ORDERS ----------
        self.search_user_fn = _lambda.Function(self, "SearchUserFn", code=_lambda.Code.from_asset("lambda/Functions/Search User"), environment={"USER_TABLE": user_table.table_name, **os_env}, **default_props)
        self.search_product_fn = _lambda.Function(self, "SearchProductFn", code=_lambda.Code.from_asset("lambda/Functions/Search Product"), environment={"PRODUCT_TABLE": product_table.table_name, **os_env}, **default_props)
        self.stream_fn = _lambda.Function(self, "StreamToOpenSearchFn", code=_lambda.Code.from_asset("lambda/Functions/StreamToOpenSearch"), environment={**os_env}, **default_props)
        self.user_upload_url_fn = _lambda.Function(self, "UserUploadUrlFn", code=_lambda.Code.from_asset("lambda/Functions/UserUploadUrl"), environment={"USER_TABLE": user_table.table_name, **s3_env}, **default_props)
        self.user_download_url_fn = _lambda.Function(self, "UserDownloadUrlFn", code=_lambda.Code.from_asset("lambda/Functions/UserDownloadUrl"), environment={"USER_TABLE": user_table.table_name, **s3_env}, **default_props)
        self.product_upload_url_fn = _lambda.Function(self, "ProductUploadUrlFn", code=_lambda.Code.from_asset("lambda/Functions/ProductUploadUrl"), environment={"PRODUCT_TABLE": product_table.table_name, **s3_env}, **default_props)
        self.product_download_url_fn = _lambda.Function(self, "ProductDownloadUrlFn", code=_lambda.Code.from_asset("lambda/Functions/ProductDownloadUrl"), environment={"PRODUCT_TABLE": product_table.table_name, **s3_env}, **default_props)
        self.order_product_fn = _lambda.Function(self, "OrderProductFn", code=_lambda.Code.from_asset("lambda/Functions/OrderProduct"), environment={"ORDER_TABLE": order_table.table_name, "PRODUCT_TABLE": product_table.table_name, **sqs_env, **s3_env}, **default_props)
        self.order_processing_fn = _lambda.Function(self, "OrderProcessingFn", code=_lambda.Code.from_asset("lambda/Functions/OrderProcessing"), environment={"ORDER_TABLE": order_table.table_name}, **default_props)
        self.dashboard_fn = _lambda.Function(self, "DashboardFn", code=_lambda.Code.from_asset("lambda/Functions/Dashboard"), **default_props)
        self.pokemon_fn = _lambda.Function(self, "GetPokemonFn", code=_lambda.Code.from_asset("lambda/Functions/GetPokemon"), **default_props)
        self.poke_importer_fn = _lambda.Function(self, "PokeImporterFn", code=_lambda.Code.from_asset("lambda/Functions/PokeImporter"), environment={"PRODUCT_TABLE": product_table.table_name}, **default_props)

        # ---------- STEP FUNCTION ----------
        invoke_pokemon = tasks.LambdaInvoke(self, "InvokePokeAPI", lambda_function=self.pokemon_fn, payload=sfn.TaskInput.from_object({"name": sfn.JsonPath.string_at("$.name")}), result_path="$.result")
        invoke_pokemon.add_retry(errors=["ServerDown", "States.TaskFailed"], interval=Duration.seconds(2), max_attempts=5, backoff_rate=2.0)
        fail_state = sfn.Fail(self, "AllRetriesExhausted", error="ServerDown", cause="PokeAPI unavailable")
        invoke_pokemon.add_catch(fail_state, errors=["ServerDown", "States.TaskFailed"], result_path="$.error")
        self.poke_state_machine = sfn.StateMachine(self, "PokeRetryStateMachine", definition_body=sfn.DefinitionBody.from_chainable(invoke_pokemon), state_machine_type=sfn.StateMachineType.EXPRESS, timeout=Duration.seconds(60))

        # ---------- TRIGGERS & PERMISSIONS ----------
        report_bucket.grant_read_write(self.order_product_fn)
        product_table.grant_read_write_data(self.poke_importer_fn)
        self.stream_fn.add_event_source(lambda_events.DynamoEventSource(user_table, starting_position=_lambda.StartingPosition.LATEST))
        self.stream_fn.add_event_source(lambda_events.DynamoEventSource(product_table, starting_position=_lambda.StartingPosition.LATEST))
        self.order_processing_fn.add_event_source(lambda_events.SqsEventSource(order_queue))

        # ---------- COGNITO AUTHORIZER ----------
        auth = apigw.CognitoUserPoolsAuthorizer(self, "WilliamApiAuthorizer",
            cognito_user_pools=[user_pool]
        )

        # ---------- API GATEWAY ----------
        api = apigw.RestApi(self, "CrudApi",
            rest_api_name="CrudApi",
            deploy_options=apigw.StageOptions(stage_name="prod"),
            binary_media_types=["multipart/form-data", "image/jpeg", "image/png", "*/*"],
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=apigw.Cors.ALL_METHODS))

        # Helper for Protected Methods
        auth_props = {
            "authorizer": auth,
            "authorization_type": apigw.AuthorizationType.COGNITO
        }

        # /users
        users = api.root.add_resource("users")
        users.add_method("GET", apigw.LambdaIntegration(self.get_users_fn), **auth_props)
        users.add_method("POST", apigw.LambdaIntegration(self.main_fn)) # Public for signup

        user_id = users.add_resource("{id}")
        user_id.add_method("GET", apigw.LambdaIntegration(self.get_user_by_id_fn), **auth_props)
        user_id.add_method("PUT", apigw.LambdaIntegration(self.update_user_fn), **auth_props)
        user_id.add_method("DELETE", apigw.LambdaIntegration(self.delete_user_fn), **auth_props)

        # /products
        products = api.root.add_resource("products")
        products.add_method("GET", apigw.LambdaIntegration(self.get_product_fn)) # Public view
        products.add_method("POST", apigw.LambdaIntegration(self.create_product_fn), **auth_props)

        product_id = products.add_resource("{id}")
        product_id.add_method("GET", apigw.LambdaIntegration(self.get_product_by_id_fn))
        product_id.add_method("PUT", apigw.LambdaIntegration(self.update_product_fn), **auth_props)
        product_id.add_method("DELETE", apigw.LambdaIntegration(self.delete_product_fn), **auth_props)

        # /orders
        orders = api.root.add_resource("orders")
        orders.add_method("POST", apigw.LambdaIntegration(self.order_product_fn), **auth_props)
        orders.add_method("GET", apigw.LambdaIntegration(self.order_product_fn), **auth_props)

        # /dashboard & /pokemon
        api.root.add_resource("dashboard").add_method("GET", apigw.LambdaIntegration(self.dashboard_fn))
        api.root.add_resource("pokemon").add_method("GET", apigw.LambdaIntegration(self.pokemon_fn))

        # --- Pokemon Secure (Step Function Integration) ---
        apigw_role = iam.Role(self, "ApiGwSfnRole", assumed_by=iam.ServicePrincipal("apigateway.amazonaws.com"))
        apigw_role.add_to_policy(iam.PolicyStatement(actions=["states:StartSyncExecution"], resources=[self.poke_state_machine.state_machine_arn]))
        
        sfn_integration = apigw.AwsIntegration(
            service="states",
            action="StartSyncExecution",
            options=apigw.IntegrationOptions(
                credentials_role=apigw_role,
                request_templates={"application/json": f'{{"input": "$util.escapeJavaScript($input.body)", "stateMachineArn": "${{{self.poke_state_machine.state_machine_arn}}}"}}'},
                integration_responses=[apigw.IntegrationResponse(status_code="200", response_templates={"application/json": "#set($output = $util.parseJson($input.path('$.output')))\n$output.result.Payload.body"})]
            )
        )
        api.root.add_resource("pokemon-secure").add_method("POST", sfn_integration, method_responses=[apigw.MethodResponse(status_code="200")], **auth_props)