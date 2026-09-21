# AWS Deployment Infrastructure

This directory contains AWS-specific deployment configurations (e.g. ECS Fargate, ECR, RDS PostgreSQL, ElastiCache).

## Target Architecture

- **ECS Fargate**: Container execution for the FastAPI service using immutable container tags (`financial-platform:<git-sha>`).
- **Amazon RDS for PostgreSQL**: Managed database with separate roles for application mutations and read-only queries.
- **Amazon ElastiCache for Redis**: Managed Redis service.
- **AWS Secrets Manager**: Runtime credential and API key injection.

All AWS-specific behavior is isolated to this directory; core application code remains cloud-provider agnostic.
