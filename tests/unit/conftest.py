import sys
import os


# Add Lambda Layer to path so 'utils' can be found
LAYER_PATH = os.path.join(os.path.dirname(__file__), "../../lambda/Layer/utils_layer/python")
if LAYER_PATH not in sys.path:
    sys.path.insert(0, LAYER_PATH)

class MockLambdaContext:
    def __init__(self):
        self.function_name = "test-function"
        self.memory_limit_in_mb = 128
        self.invoked_function_arn = "arn:aws:lambda:ap-southeast-1:123456789:function:test"
        self.aws_request_id = "test-request-id"
    
    