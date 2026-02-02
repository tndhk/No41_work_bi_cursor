# Runbook

## Deployment Prerequisites

Before deploying, ensure you have:

- **AWS Credentials**: Configured with appropriate permissions for:
  - ECS (Elastic Container Service)
  - ECR (Elastic Container Registry)
  - S3 (Simple Storage Service)
  - DynamoDB
  - CloudWatch Logs
  - Secrets Manager
- **Secrets Configured**: 
  - JWT secret key in Secrets Manager
  - Vertex AI service account credentials (if using Chatbot)
- **Infrastructure Provisioned**:
  - VPC with public/private subnets
  - ECS cluster and services
  - DynamoDB tables
  - S3 buckets (datasets and static assets)
  - CloudFront distribution
  - VPC endpoints for S3 and DynamoDB

## Environments

| Environment | URL | Purpose |
| --- | --- | --- |
| `local` | `http://localhost:3000` | Local development |
| `staging` | `https://bi-staging.internal.company.com` | Pre-production testing |
| `production` | `https://bi.internal.company.com` | Production |

## Deployment Procedure

### 1. Build and Push Docker Images

Build and tag images:

```bash
# Set variables
ECR_REGISTRY="<your-ecr-registry>"
IMAGE_TAG="$(git rev-parse --short HEAD)"  # or use semantic version

# Build API image
docker build -t ${ECR_REGISTRY}/bi-api:${IMAGE_TAG} ./backend
docker build -t ${ECR_REGISTRY}/bi-api:latest ./backend

# Build Executor image
docker build -t ${ECR_REGISTRY}/bi-executor:${IMAGE_TAG} ./executor
docker build -t ${ECR_REGISTRY}/bi-executor:latest ./executor

# Build Frontend image
docker build -t ${ECR_REGISTRY}/bi-frontend:${IMAGE_TAG} ./frontend
docker build -t ${ECR_REGISTRY}/bi-frontend:latest ./frontend
```

Push to ECR:

```bash
# Login to ECR
aws ecr get-login-password --region ap-northeast-1 | \
  docker login --username AWS --password-stdin ${ECR_REGISTRY}

# Push images
docker push ${ECR_REGISTRY}/bi-api:${IMAGE_TAG}
docker push ${ECR_REGISTRY}/bi-api:latest
docker push ${ECR_REGISTRY}/bi-executor:${IMAGE_TAG}
docker push ${ECR_REGISTRY}/bi-executor:latest
docker push ${ECR_REGISTRY}/bi-frontend:${IMAGE_TAG}
docker push ${ECR_REGISTRY}/bi-frontend:latest
```

### 2. Update ECS Services

Update API service:

```bash
ENV="staging"  # or "production"
CLUSTER_NAME="bi-${ENV}"

# Force new deployment with latest image
aws ecs update-service \
  --cluster ${CLUSTER_NAME} \
  --service api \
  --force-new-deployment \
  --region ap-northeast-1
```

Update Executor service:

```bash
aws ecs update-service \
  --cluster ${CLUSTER_NAME} \
  --service executor \
  --force-new-deployment \
  --region ap-northeast-1
```

### 3. Deploy Frontend Assets

Build frontend:

```bash
cd frontend
npm ci
npm run build
```

Sync to S3:

```bash
ENV="staging"  # or "production"
S3_BUCKET="bi-static-${ENV}"

aws s3 sync ./dist s3://${S3_BUCKET}/ --delete \
  --cache-control "public, max-age=31536000, immutable" \
  --exclude "index.html" \
  --region ap-northeast-1

# Upload index.html with shorter cache
aws s3 cp ./dist/index.html s3://${S3_BUCKET}/index.html \
  --cache-control "public, max-age=0, must-revalidate" \
  --region ap-northeast-1
```

Invalidate CloudFront cache:

```bash
CLOUDFRONT_DIST_ID="<your-distribution-id>"

aws cloudfront create-invalidation \
  --distribution-id ${CLOUDFRONT_DIST_ID} \
  --paths "/*" \
  --region ap-northeast-1
```

### 4. Wait for Deployment Stability

Wait for services to stabilize:

```bash
aws ecs wait services-stable \
  --cluster ${CLUSTER_NAME} \
  --services api executor \
  --region ap-northeast-1
```

### 5. Verify Deployment

Check service health:

```bash
# Check API health endpoint
curl https://bi-${ENV}.internal.company.com/api/health

# Check service status
aws ecs describe-services \
  --cluster ${CLUSTER_NAME} \
  --services api executor \
  --region ap-northeast-1 \
  --query 'services[*].[serviceName,runningCount,desiredCount,status]' \
  --output table
```

## Monitoring

### Logs

**View API logs:**

```bash
ENV="staging"  # or "production"
LOG_GROUP="/ecs/bi-${ENV}-api"

# Tail logs
aws logs tail ${LOG_GROUP} --follow --region ap-northeast-1

# Search logs
aws logs filter-log-events \
  --log-group-name ${LOG_GROUP} \
  --start-time $(date -d '1 hour ago' +%s)000 \
  --filter-pattern "ERROR" \
  --region ap-northeast-1
```

**View Executor logs:**

```bash
LOG_GROUP="/ecs/bi-${ENV}-executor"
aws logs tail ${LOG_GROUP} --follow --region ap-northeast-1
```

### Metrics

**Check ECS service metrics:**

```bash
ENV="staging"
CLUSTER_NAME="bi-${ENV}"

# CPU utilization
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name CPUUtilization \
  --dimensions Name=ClusterName,Value=${CLUSTER_NAME} Name=ServiceName,Value=api \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 300 \
  --statistics Average,Maximum \
  --region ap-northeast-1

# Memory utilization
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name MemoryUtilization \
  --dimensions Name=ClusterName,Value=${CLUSTER_NAME} Name=ServiceName,Value=api \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 300 \
  --statistics Average,Maximum \
  --region ap-northeast-1
```

**Key metrics to monitor:**

- API response time (p95, p99)
- API error rate
- Card execution timeout rate
- Transform execution success rate
- ECS task CPU/Memory utilization
- DynamoDB throttled requests
- S3 request errors

### Alerts

Configure CloudWatch alarms for:

- API error rate > 5%
- Card execution timeout rate > 10%
- ECS service running count < desired count
- DynamoDB throttled requests > 0
- API response time p95 > 3 seconds

## Rollback Procedure

### Rollback ECS Services

1. **Identify previous task definition:**

```bash
ENV="staging"
CLUSTER_NAME="bi-${ENV}"

# List task definitions
aws ecs list-task-definitions \
  --family-prefix bi-${ENV}-api \
  --sort DESC \
  --region ap-northeast-1

# Get previous revision
PREV_REVISION="<previous-revision-number>"
```

2. **Update service to previous revision:**

```bash
# Rollback API service
aws ecs update-service \
  --cluster ${CLUSTER_NAME} \
  --service api \
  --task-definition bi-${ENV}-api:${PREV_REVISION} \
  --region ap-northeast-1

# Rollback Executor service
aws ecs update-service \
  --cluster ${CLUSTER_NAME} \
  --service executor \
  --task-definition bi-${ENV}-executor:${PREV_REVISION} \
  --region ap-northeast-1
```

3. **Wait for rollback to complete:**

```bash
aws ecs wait services-stable \
  --cluster ${CLUSTER_NAME} \
  --services api executor \
  --region ap-northeast-1
```

### Rollback Frontend

If frontend deployment fails, restore from S3 versioning:

```bash
ENV="staging"
S3_BUCKET="bi-static-${ENV}"

# List object versions
aws s3api list-object-versions \
  --bucket ${S3_BUCKET} \
  --prefix index.html \
  --region ap-northeast-1

# Restore previous version
PREV_VERSION_ID="<version-id>"
aws s3api get-object \
  --bucket ${S3_BUCKET} \
  --key index.html \
  --version-id ${PREV_VERSION_ID} \
  index.html \
  --region ap-northeast-1

# Upload restored version
aws s3 cp index.html s3://${S3_BUCKET}/index.html \
  --region ap-northeast-1

# Invalidate CloudFront
aws cloudfront create-invalidation \
  --distribution-id ${CLOUDFRONT_DIST_ID} \
  --paths "/*" \
  --region ap-northeast-1
```

## Common Issues and Troubleshooting

### Card Execution Timeouts

**Symptoms:**
- Cards fail to render
- Timeout errors in logs
- High executor service CPU usage

**Solutions:**
- Reduce dataset size (use sampling or filtering)
- Optimize card Python code
- Increase `EXECUTOR_TIMEOUT_CARD` (not recommended)
- Check executor service resource limits

**Investigation:**
```bash
# Check executor logs for timeout errors
aws logs tail /ecs/bi-${ENV}-executor --follow --filter-pattern "timeout"
```

### Memory Errors

**Symptoms:**
- OOM (Out of Memory) errors
- ECS tasks being killed
- High memory utilization metrics

**Solutions:**
- Increase ECS task memory allocation
- Add data sampling for large datasets
- Optimize data processing code
- Use Parquet partitioning more effectively

**Investigation:**
```bash
# Check memory metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name MemoryUtilization \
  --dimensions Name=ClusterName,Value=bi-${ENV} Name=ServiceName,Value=executor \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 300 \
  --statistics Maximum \
  --region ap-northeast-1
```

### Permission Errors

**Symptoms:**
- 403 Forbidden errors
- Access denied messages
- IAM policy errors in logs

**Solutions:**
- Verify ECS task role has required permissions
- Check Secrets Manager access
- Verify S3 bucket policies
- Check DynamoDB table policies

**Investigation:**
```bash
# Check task role
aws ecs describe-task-definition \
  --task-definition bi-${ENV}-api \
  --query 'taskDefinition.taskRoleArn' \
  --region ap-northeast-1

# Check attached policies
aws iam list-attached-role-policies \
  --role-name <task-role-name> \
  --region ap-northeast-1
```

### Connectivity Errors

**Symptoms:**
- Connection timeout errors
- Network unreachable errors
- VPC endpoint errors

**Solutions:**
- Verify VPC endpoints are configured
- Check security group rules
- Verify route tables
- Check NAT gateway (if needed)

**Investigation:**
```bash
# Check VPC endpoints
aws ec2 describe-vpc-endpoints \
  --filters "Name=vpc-id,Values=<vpc-id>" \
  --region ap-northeast-1

# Check security groups
aws ec2 describe-security-groups \
  --group-ids <security-group-id> \
  --region ap-northeast-1
```

### Database Connection Issues

**Symptoms:**
- DynamoDB throttling errors
- Connection timeout to DynamoDB
- High read/write capacity usage

**Solutions:**
- Check DynamoDB capacity settings
- Verify VPC endpoint configuration
- Review query patterns for optimization
- Consider using GSI for better query performance

**Investigation:**
```bash
# Check DynamoDB throttled requests
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name UserErrors \
  --dimensions Name=TableName,Value=bi_datasets \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 300 \
  --statistics Sum \
  --region ap-northeast-1
```

## Emergency Procedures

### Service Unavailable

If the service becomes completely unavailable:

1. **Check service status:**
   ```bash
   aws ecs describe-services \
     --cluster bi-${ENV} \
     --services api executor \
     --region ap-northeast-1
   ```

2. **Check for recent deployments:**
   ```bash
   aws ecs describe-services \
     --cluster bi-${ENV} \
     --services api \
     --query 'services[0].events[:5]' \
     --region ap-northeast-1
   ```

3. **Rollback if recent deployment:**
   - Follow rollback procedure above

4. **Scale up services if needed:**
   ```bash
   aws ecs update-service \
     --cluster bi-${ENV} \
     --service api \
     --desired-count 2 \
     --region ap-northeast-1
   ```

### Data Corruption

If data corruption is suspected:

1. **Stop writes immediately** (if possible)
2. **Check DynamoDB point-in-time recovery:**
   ```bash
   aws dynamodb describe-continuous-backups \
     --table-name bi_datasets \
     --region ap-northeast-1
   ```

3. **Restore from backup:**
   ```bash
   aws dynamodb restore-table-to-point-in-time \
     --source-table-name bi_datasets \
     --target-table-name bi_datasets_restored \
     --restore-date-time <timestamp> \
     --region ap-northeast-1
   ```

### Security Incident

If a security incident is detected:

1. **Immediately rotate secrets:**
   - JWT secret key
   - Database credentials
   - API keys

2. **Review audit logs:**
   ```bash
   # Check audit logs for suspicious activity
   aws dynamodb query \
     --table-name bi_audit_logs \
     --index-name LogsByTimestamp \
     --key-condition-expression "timestamp = :ts" \
     --expression-attribute-values '{":ts":{"N":"<timestamp>"}}' \
     --region ap-northeast-1
   ```

3. **Notify security team**
4. **Document incident**

## Maintenance Windows

Schedule maintenance during low-traffic periods:

- **Staging**: Anytime (no production impact)
- **Production**: Weekends or off-hours (notify users in advance)

During maintenance:

1. Put CloudFront distribution in maintenance mode
2. Scale down services if needed
3. Perform maintenance tasks
4. Verify functionality
5. Scale back up
6. Remove maintenance mode
