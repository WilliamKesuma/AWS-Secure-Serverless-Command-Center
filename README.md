# 🚀 AWS Secure Serverless Command Center

**Developer:** William Kesuma  

This project is a high-performance, serverless backend architecture built using **AWS CDK**. It manages secure user authentication, product catalogs, and automated order processing with real-time search indexing.

---

## 🏗️ Architecture Overview

### 🔐 Security & Identity
* **AWS Cognito**: Secure User Pool for authentication and email-based sign-up.
* **IAM Stacks**: Fine-grained permissions for Lambda, S3, and DynamoDB.

### 📦 Data & Storage
* **DynamoDB**: NoSQL storage for Users and Products.
* **DynamoDB Streams**: Triggers automated indexing of data into OpenSearch.
* **S3 Buckets**: Dedicated storage for secure file uploads and reporting.

### 📁 Repository Structure
* **stack_cdk/**: Modular infrastructure definitions (Cognito, DynamoDB, etc.).
* **lambda/**: Business logic for API handlers and background workers.
* **lambda/Layer/**: Shared utils_layer containing common dependencies.
* **tests/**: Comprehensive test cases for the serverless components.

### ⚙️ Automation & Workflows
* **Step Functions**: Orchestrates the order processing state machine with retry logic.
* **EventBridge**: Scheduled batch jobs for automated reporting.
* **SNS**: Real-time email notifications for order updates.

### 🔍 Search
* **OpenSearch Service**: Full-text search capabilities for the product dashboard.

---

## 🛠️ Setup & Deployment

### 1. Environment Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

#Synthesize CloudFormation template
cdk synth

# Deploy all stacks to AWS
cdk deploy --all

# Run all unit tests
pytest tests/unit

