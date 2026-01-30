# Runbook

## Deployment Prerequisites
- AWS credentials with ECS, ECR, S3, DynamoDB access
- Secrets configured (JWT, Vertex AI)
- Infrastructure provisioned (VPC, ECS, DynamoDB, S3, CloudFront)

## Environments
- `local` -> `http://localhost:3000`
- `staging` -> `https://bi-staging.internal.company.com`
- `production` -> `https://bi.internal.company.com`

## Deploy Procedure
1. Build and push images.
   - `docker build -t <ecr>/bi-api:<tag> ./backend`
   - `docker build -t <ecr>/bi-executor:<tag> ./executor`
   - `docker build -t <ecr>/bi-frontend:<tag> ./frontend`
2. Update ECS services.
   - `aws ecs update-service --cluster bi-<env> --service api --force-new-deployment`
   - `aws ecs update-service --cluster bi-<env> --service executor --force-new-deployment`
3. Sync frontend assets to S3 and invalidate CDN.
   - `aws s3 sync ./frontend/dist s3://bi-static-<env>/ --delete`
   - `aws cloudfront create-invalidation --distribution-id <id> --paths "/*"`
4. Wait for stability.
   - `aws ecs wait services-stable --cluster bi-<env> --services api executor`

## Monitoring
- Logs:
  - `aws logs tail /ecs/bi-<env>-api --follow`
  - `aws logs tail /ecs/bi-<env>-executor --follow`
- Metrics:
  - `aws cloudwatch get-metric-statistics --namespace AWS/ECS --metric-name CPUUtilization ...`

## Rollback
- Revert to previous task definition.
  - `aws ecs update-service --cluster bi-<env> --service api --task-definition bi-<env>-api:<rev>`
  - `aws ecs update-service --cluster bi-<env> --service executor --task-definition bi-<env>-executor:<rev>`

## Common Issues
- **Card execution timeouts**: reduce dataset size or optimize code.
- **Memory errors**: increase ECS task memory or add sampling.
- **Permissions errors**: verify task roles and secrets.
- **Connectivity errors**: verify VPC endpoints and security groups.

