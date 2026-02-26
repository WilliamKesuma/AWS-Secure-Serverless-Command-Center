from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as _lambda,
    aws_lambda_event_sources as lambda_events,
    aws_apigateway as apigw,
    aws_iam as iam
)
from constructs import Construct

class LambdaStack(Stack):

    def __init__(self, scope: Construct, construct_id: str,
                 user_table, product_table, order_table, iam_role,
                 os_endpoint: str,
                 bucket_name: str,
                 report_bucket, # S3 Bucket object passed from app.py
                 order_queue_url: str,
                 order_queue,
                 **kwargs):

        super().__init__(scope, construct_id, **kwargs)

        # Environment bundles
        os_env = {"OS_ENDPOINT": os_endpoint}
        s3_env = {"BUCKET_NAME": bucket_name}
        sqs_env = {"ORDER_QUEUE_URL": order_queue_url}

        # ---------- LAMBDA LAYER ----------
        self.utils_layer = _lambda.LayerVersion(
            self, "AppUtilsLayer",
            code=_lambda.Code.from_asset("lambda/Layer/utils_layer"),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_12],
            description="Shared utils for logging and tracing"
        )

        # Default properties for all Lambda functions
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
            environment={"USER_TABLE": user_table.table_name, **os_env},
            **default_props)

        self.get_users_fn = _lambda.Function(self, "GetUsersFn",
            code=_lambda.Code.from_asset("lambda/Functions/GetUsers"),
            environment={"USER_TABLE": user_table.table_name, **os_env},
            **default_props)

        self.get_user_by_id_fn = _lambda.Function(self, "GetUserByIdFn",
            code=_lambda.Code.from_asset("lambda/Functions/GetUserById"),
            environment={"USER_TABLE": user_table.table_name, **os_env},
            **default_props)

        self.update_user_fn = _lambda.Function(self, "UpdateUserFn",
            code=_lambda.Code.from_asset("lambda/Functions/UpdateUser"),
            environment={"USER_TABLE": user_table.table_name, **os_env},
            **default_props)

        self.delete_user_fn = _lambda.Function(self, "DeleteUserFn",
            code=_lambda.Code.from_asset("lambda/Functions/DeleteUser"),
            environment={"USER_TABLE": user_table.table_name, **os_env},
            **default_props)

        # ---------- PRODUCT FUNCTIONS ----------
        self.create_product_fn = _lambda.Function(self, "CreateProductFn",
            code=_lambda.Code.from_asset("lambda/Functions/CreateProduct"),
            environment={"PRODUCT_TABLE": product_table.table_name, **os_env},
            **default_props)

        self.get_product_fn = _lambda.Function(self, "GetProductFn",
            code=_lambda.Code.from_asset("lambda/Functions/GetProduct"),
            environment={"PRODUCT_TABLE": product_table.table_name, **os_env},
            **default_props)

        self.get_product_by_id_fn = _lambda.Function(self, "GetProductByIdFn",
            code=_lambda.Code.from_asset("lambda/Functions/GetProductById"),
            environment={"PRODUCT_TABLE": product_table.table_name, **os_env},
            **default_props)

        self.update_product_fn = _lambda.Function(self, "UpdateProductFn",
            code=_lambda.Code.from_asset("lambda/Functions/UpdateProduct"),
            environment={"PRODUCT_TABLE": product_table.table_name, **os_env},
            **default_props)

        self.delete_product_fn = _lambda.Function(self, "DeleteProductFn",
            code=_lambda.Code.from_asset("lambda/Functions/DeleteProduct"),
            environment={"PRODUCT_TABLE": product_table.table_name, **os_env},
            **default_props)

        # ---------- SEARCH & STREAM ----------
        self.search_user_fn = _lambda.Function(self, "SearchUserFn",
            code=_lambda.Code.from_asset("lambda/Functions/Search User"),
            environment={"USER_TABLE": user_table.table_name, **os_env},
            **default_props)

        self.search_product_fn = _lambda.Function(self, "SearchProductFn",
            code=_lambda.Code.from_asset("lambda/Functions/Search Product"),
            environment={"PRODUCT_TABLE": product_table.table_name, **os_env},
            **default_props)

        self.stream_fn = _lambda.Function(self, "StreamToOpenSearchFn",
            code=_lambda.Code.from_asset("lambda/Functions/StreamToOpenSearch"),
            environment={**os_env},
            **default_props)

        # ---------- S3 & ORDER FUNCTIONS ----------
        self.user_upload_url_fn = _lambda.Function(self, "UserUploadUrlFn",
            code=_lambda.Code.from_asset("lambda/Functions/UserUploadUrl"),
            environment={"USER_TABLE": user_table.table_name, **s3_env},
            **default_props)

        self.user_download_url_fn = _lambda.Function(self, "UserDownloadUrlFn",
            code=_lambda.Code.from_asset("lambda/Functions/UserDownloadUrl"),
            environment={"USER_TABLE": user_table.table_name, **s3_env},
            **default_props)

        self.product_upload_url_fn = _lambda.Function(self, "ProductUploadUrlFn",
            code=_lambda.Code.from_asset("lambda/Functions/ProductUploadUrl"),
            environment={"PRODUCT_TABLE": product_table.table_name, **s3_env},
            **default_props)

        self.product_download_url_fn = _lambda.Function(self, "ProductDownloadUrlFn",
            code=_lambda.Code.from_asset("lambda/Functions/ProductDownloadUrl"),
            environment={"PRODUCT_TABLE": product_table.table_name, **s3_env},
            **default_props)

        # Unified Order Lambda (POST: Create, GET: List, GET: Export)
        self.order_product_fn = _lambda.Function(self, "OrderProductFn",
            code=_lambda.Code.from_asset("lambda/Functions/OrderProduct"),
            environment={
                "ORDER_TABLE": order_table.table_name, 
                "PRODUCT_TABLE": product_table.table_name, 
                **sqs_env,
                **s3_env
            },
            **default_props)

        # NEW: Dashboard Lambda to serve the HTML UI
        self.dashboard_fn = _lambda.Function(self, "DashboardFn",
            code=_lambda.Code.from_asset("lambda/Functions/Dashboard"),
            **default_props)

        self.order_processing_fn = _lambda.Function(self, "OrderProcessingFn",
            code=_lambda.Code.from_asset("lambda/Functions/OrderProcessing"),
            environment={"ORDER_TABLE": order_table.table_name},
            **default_props)
        
        self.pokemon_fn = _lambda.Function(self, "GetPokemonFn",
        code=_lambda.Code.from_asset("lambda/Functions/GetPokemon"),
        **default_props)

        # ---------- PERMISSIONS ----------
        # Grant read/write to the report bucket
        report_bucket.grant_read_write(self.order_product_fn)
        
        # Explicit S3:GetObject policy to prevent 403 errors on presigned URLs
        self.order_product_fn.add_to_role_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["s3:GetObject"],
            resources=[f"{report_bucket.bucket_arn}/*"]
        ))
        
        # ---------- TRIGGERS ----------
        self.stream_fn.add_event_source(lambda_events.DynamoEventSource(user_table, starting_position=_lambda.StartingPosition.LATEST))
        self.stream_fn.add_event_source(lambda_events.DynamoEventSource(product_table, starting_position=_lambda.StartingPosition.LATEST))
        self.order_processing_fn.add_event_source(lambda_events.SqsEventSource(order_queue))
        

        # ---------- API GATEWAY ----------
        api = apigw.RestApi(self, "CrudApi",
            rest_api_name="CrudApi",
            deploy_options=apigw.StageOptions(stage_name="prod"),
            binary_media_types=["multipart/form-data", "image/jpeg", "image/png", "*/*"],
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=apigw.Cors.ALL_METHODS
            )
        )

        # Users resource tree
        users = api.root.add_resource("users")
        users.add_method("GET", apigw.LambdaIntegration(self.get_users_fn))
        users.add_method("POST", apigw.LambdaIntegration(self.main_fn))
        
        user_id = users.add_resource("{id}")
        user_id.add_method("GET", apigw.LambdaIntegration(self.get_user_by_id_fn))
        user_id.add_method("PUT", apigw.LambdaIntegration(self.update_user_fn))
        user_id.add_method("DELETE", apigw.LambdaIntegration(self.delete_user_fn))
        user_id.add_resource("upload-url").add_method("POST", apigw.LambdaIntegration(self.user_upload_url_fn))
        user_id.add_resource("download-url").add_method("GET", apigw.LambdaIntegration(self.user_download_url_fn))

        # Products resource tree
        products = api.root.add_resource("products")
        products.add_method("GET", apigw.LambdaIntegration(self.get_product_fn))
        products.add_method("POST", apigw.LambdaIntegration(self.create_product_fn))

        product_id = products.add_resource("{id}")
        product_id.add_method("GET", apigw.LambdaIntegration(self.get_product_by_id_fn))
        product_id.add_method("PUT", apigw.LambdaIntegration(self.update_product_fn))
        product_id.add_method("DELETE", apigw.LambdaIntegration(self.delete_product_fn))
        product_id.add_resource("upload-url").add_method("POST", apigw.LambdaIntegration(self.product_upload_url_fn))
        product_id.add_resource("download-url").add_method("GET", apigw.LambdaIntegration(self.product_download_url_fn))

        # Search
        api.root.add_resource("search-users").add_method("GET", apigw.LambdaIntegration(self.search_user_fn))
        api.root.add_resource("search-products").add_method("GET", apigw.LambdaIntegration(self.search_product_fn))
        api.root.add_resource("pokemon").add_method("GET", apigw.LambdaIntegration(self.pokemon_fn))
        
        # Orders resource tree
        orders = api.root.add_resource("orders")
        orders.add_method("POST", apigw.LambdaIntegration(self.order_product_fn))
        orders.add_method("GET", apigw.LambdaIntegration(self.order_product_fn))
        
        # Export sub-resource
        export = orders.add_resource("export")
        export.add_method("GET", apigw.LambdaIntegration(self.order_product_fn))

        # NEW: Dashboard resource tree
        dashboard = api.root.add_resource("dashboard")
        dashboard.add_method("GET", apigw.LambdaIntegration(self.dashboard_fn))