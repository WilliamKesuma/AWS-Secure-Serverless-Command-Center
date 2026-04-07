# AWS Secure Serverless Command Center

A fully serverless web application built on AWS using CDK (Python). It provides a secure REST API for managing users, products, and orders — with Cognito authentication, full-text search via OpenSearch, file uploads through S3 presigned URLs, asynchronous order processing with SQS, and automated reporting via SES.

## Architecture Overview

```
Client
  │
  ▼
API Gateway (REST, Cognito Authorizer)
  │
  ├── /users          → CRUD Lambdas → DynamoDB (UserTable)
  ├── /products       → CRUD Lambdas → DynamoDB (ProductTable)
  ├── /orders         → Order Lambda → SQS FIFO → Order Processing Lambda → DynamoDB (OrderTable)
  ├── /dashboard      → Dashboard Lambda (serves HTML)
  ├── /pokemon        → PokeAPI Lambda
  └── /pokemon-secure → API GW → Step Functions (Express) → PokeAPI Lambda (with retry)
                                        │
DynamoDB Streams ──► StreamToOpenSearch Lambda ──► OpenSearch
                                        │
S3 Bucket ◄── Presigned URL Lambdas (upload/download for users & products)
                                        │
CloudWatch Metric Filters ──► Alarm ──► SNS (email alerts)
                                        │
Reporting Lambda ──► Generates order report ──► S3 + SES email
```

## AWS Services Used

| Service | Purpose |
|---|---|
| API Gateway | REST API with CORS and Cognito authorization |
| Lambda (Python 3.12) | All business logic, 25+ functions with X-Ray tracing |
| DynamoDB | User, Product, and Order tables with streams enabled |
| Cognito | User pool with email sign-up/sign-in and post-confirmation sync |
| OpenSearch | Full-text search for users and products |
| S3 | Profile images and product file uploads via presigned URLs |
| SQS (FIFO) | Asynchronous order processing with deduplication |
| Step Functions | Express workflow for PokeAPI calls with retry/error handling |
| SNS | Email alerts on Lambda errors via CloudWatch alarms |
| SES | Automated order report emails |
| CloudWatch | Metric filters, alarms, and centralized logging |
| X-Ray | Distributed tracing across all Lambda functions |
| IAM | Least-privilege roles for Lambda and API Gateway |

## API Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/users` | Public | Create a new user |
| GET | `/users` | Cognito | List all users |
| GET | `/users/{id}` | Cognito | Get user by ID |
| PUT | `/users/{id}` | Cognito | Update user |
| DELETE | `/users/{id}` | Cognito | Delete user |
| GET | `/products` | Public | List all products |
| POST | `/products` | Cognito | Create a product |
| GET | `/products/{id}` | Public | Get product by ID |
| PUT | `/products/{id}` | Cognito | Update product |
| DELETE | `/products/{id}` | Cognito | Delete product |
| POST | `/orders` | Cognito | Place an order |
| GET | `/orders` | Cognito | List orders |
| GET | `/dashboard` | Public | HTML dashboard |
| GET | `/pokemon` | Public | Fetch Pokémon data |
| POST | `/pokemon-secure` | Cognito | Pokémon fetch via Step Functions with retry |

## Prerequisites

- Python 3.12+
- Node.js (for AWS CDK CLI)
- AWS CLI configured with credentials
- AWS CDK CLI (`npm install -g aws-cdk`)

## Project Structure

```
.
├── app.py                      # CDK app entry point
├── cdk.json                    # CDK configuration
├── requirements.txt            # Python dependencies
├── stack_cdk/                  # CDK stack definitions
│   ├── cognito_stack.py        #   Cognito user pool + post-confirm trigger
│   ├── dynamodb_stack.py       #   DynamoDB tables (User, Product, Order)
│   ├── iam_stack.py            #   IAM roles and policies
│   ├── lambda_stack.py         #   Lambda functions + API Gateway + Step Functions
│   ├── opensearch_stack.py     #   OpenSearch domain
│   ├── reporting_stack.py      #   Order report generation + SES
│   ├── s3_stack.py             #   S3 bucket for file uploads
│   ├── sns_stack.py            #   SNS alerts + CloudWatch alarms
│   └── sqs_stack.py            #   SQS FIFO queue for orders
└── lambda/
    ├── Functions/              # Lambda function source code
    │   ├── CreateUser/
    │   ├── GetUsers/
    │   ├── CreateProduct/
    │   ├── OrderProduct/
    │   ├── StreamToOpenSearch/
    │   ├── Dashboard/
    │   └── ... (25+ functions)
    └── Layer/
        └── utils_layer/        # Shared Lambda layer (aws-lambda-powertools)
```

## Deployment

### 1. Clone the repository

```bash
git clone https://github.com/WilliamKesuma/AWS-Secure-Serverless-Command-Center.git
cd AWS-Secure-Serverless-Command-Center
```

### 2. Set up the Python virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Bootstrap CDK (first time only)

If this is your first CDK deployment in the target AWS account/region:

```bash
cdk bootstrap
```

### 4. Verify the stacks

```bash
cdk synth
```

This synthesizes all 9 CloudFormation stacks:
`IamStack`, `DynamodbStack`, `S3Stack`, `SqsStack`, `CognitoStack`, `OpenSearchStack`, `LambdaStack`, `ReportingStack`, `SnsStack`

### 5. Deploy

```bash
cdk deploy --all
```

You will be prompted to confirm IAM changes. Use `--require-approval never` to skip prompts in CI/CD.

### 6. Post-deployment

After deployment, CDK outputs the API Gateway endpoint URL. Use it to interact with the API.

To authenticate, sign up a user through Cognito, confirm via email, then use the ID token in the `Authorization` header for protected endpoints.

## Cleanup

To tear down all resources:

```bash
cdk destroy --all
```

## License

This project is for educational and demonstration purposes.
