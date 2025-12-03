# EFIR Budget Planning Application - Deployment Guide

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Docker Deployment](#docker-deployment)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [CI/CD Pipeline](#cicd-pipeline)
6. [Database Setup](#database-setup)
7. [Monitoring & Logging](#monitoring--logging)
8. [Security Checklist](#security-checklist)
9. [Backup & Recovery](#backup--recovery)
10. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software

- **Docker**: 24.x or later
- **Docker Compose**: 2.x or later
- **Node.js**: 20.x LTS (for local development)
- **Python**: 3.14.0 (for backend development - Free-threaded Python support)
- **PostgreSQL**: 17.x (via Supabase or self-hosted)
- **Redis**: 7.x (for caching and rate limiting)

### Required Accounts

- **Supabase**: Database and authentication (https://supabase.com)
- **Sentry**: Error tracking (https://sentry.io)
- **Container Registry**: Docker Hub, GitHub Container Registry, or private registry

## Environment Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/efir-budget-app.git
cd efir-budget-app
```

### 2. Configure Environment Variables

Copy the example environment file and configure it:

```bash
cp .env.production.example .env.production
```

**Critical environment variables to configure:**

```bash
# Database
DATABASE_URL=postgresql://user:password@host:5432/efir_budget
POSTGRES_PASSWORD=<strong-password>

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=<service-role-key>
SUPABASE_ANON_KEY=<anon-key>

# JWT & Security
JWT_SECRET=<64-character-random-string>

# CORS
ALLOWED_ORIGINS=https://budget.efir-school.com
PRODUCTION_FRONTEND_URL=https://budget.efir-school.com

# Sentry
SENTRY_DSN=https://xxx@sentry.io/project

# Rate Limiting
ENABLE_RATE_LIMITING=true
RATE_LIMIT_PER_MINUTE=300
REDIS_URL=redis://redis:6379/0
```

### 3. Generate Secure Secrets

```bash
# Generate JWT secret
openssl rand -hex 32

# Generate database password
openssl rand -base64 24
```

## Docker Deployment

### Development Environment

```bash
# Build and start all services
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f
```

### Production Environment

```bash
# Build production images
docker compose -f docker-compose.yml build

# Start with production configuration
docker compose -f docker-compose.yml up -d

# Verify health
curl http://localhost:8000/health
curl http://localhost:80/health
```

### Service Architecture

```
┌─────────────────┐     ┌─────────────────┐
│    Frontend     │     │     Backend     │
│    (nginx)      │────▶│   (FastAPI)     │
│   Port: 80      │     │   Port: 8000    │
└─────────────────┘     └─────────────────┘
         │                       │
         │              ┌────────┴────────┐
         │              │                 │
         │       ┌──────▼─────┐   ┌───────▼──────┐
         │       │ PostgreSQL │   │    Redis     │
         │       │ Port: 5432 │   │  Port: 6379  │
         │       └────────────┘   └──────────────┘
         │
         └──────────▶ Supabase (Auth, Realtime)
```

## Kubernetes Deployment

### Namespace Setup

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: efir-budget
```

### Secrets Configuration

```bash
kubectl create secret generic efir-secrets \
  --from-literal=postgres-password=<password> \
  --from-literal=jwt-secret=<secret> \
  --from-literal=supabase-key=<key> \
  -n efir-budget
```

### Deployment Configuration

```yaml
# backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: efir-backend
  namespace: efir-budget
spec:
  replicas: 3
  selector:
    matchLabels:
      app: efir-backend
  template:
    metadata:
      labels:
        app: efir-backend
    spec:
      containers:
        - name: backend
          image: efir/backend:latest
          ports:
            - containerPort: 8000
          envFrom:
            - secretRef:
                name: efir-secrets
          livenessProbe:
            httpGet:
              path: /health/live
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /health/ready
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 5
          resources:
            requests:
              memory: "256Mi"
              cpu: "250m"
            limits:
              memory: "512Mi"
              cpu: "500m"
```

## CI/CD Pipeline

### GitHub Actions Workflow

The application uses GitHub Actions for CI/CD. The pipeline is defined in `.github/workflows/ci-cd.yml`.

**Pipeline Stages:**

1. **Lint & Type Check**
   - Frontend: ESLint + TypeScript
   - Backend: Ruff + mypy

2. **Test**
   - Frontend: Vitest unit tests
   - Backend: pytest unit tests
   - E2E: Playwright tests

3. **Build**
   - Frontend: Vite production build
   - Backend: Docker image build

4. **Security Scan**
   - Dependency vulnerability scan
   - SAST (Static Application Security Testing)

5. **Deploy**
   - Staging: Automatic on `develop` branch
   - Production: Manual approval required

### Deployment Commands

```bash
# Deploy to staging
git push origin develop

# Deploy to production (requires approval)
git push origin main
```

## Database Setup

### Initial Migration

```bash
# Run migrations
cd backend
alembic upgrade head

# Verify migration status
alembic current
```

### Supabase Configuration

1. **Enable Row Level Security (RLS)**

```sql
-- Enable RLS on all tables
ALTER TABLE budget_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE enrollment_plans ENABLE ROW LEVEL SECURITY;
-- ... repeat for all tables
```

2. **Create RLS Policies**

```sql
-- Example: Users can only see their organization's data
CREATE POLICY "org_isolation" ON budget_versions
  FOR ALL USING (
    organization_id = auth.jwt()->>'organization_id'
  );
```

### Database Backup

```bash
# Automated backup via Supabase (recommended)
# Or manual backup:
pg_dump -h db-host -U postgres efir_budget > backup.sql
```

## Monitoring & Logging

### Health Checks

The application provides three health endpoints:

- `/health` - Basic health status
- `/health/live` - Liveness probe (is the app running?)
- `/health/ready` - Readiness probe (can the app serve requests?)

### Sentry Integration

Error tracking is configured via environment variables:

```bash
SENTRY_DSN_BACKEND=https://xxx@sentry.io/backend-project
SENTRY_DSN_FRONTEND=https://xxx@sentry.io/frontend-project
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1
```

### Structured Logging

Logs are output in JSON format for easy parsing:

```json
{
  "timestamp": "2025-01-15T10:30:00Z",
  "level": "INFO",
  "message": "Request processed",
  "correlation_id": "abc123",
  "path": "/api/v1/enrollment",
  "method": "GET",
  "status_code": 200,
  "duration_ms": 45
}
```

## Security Checklist

### Pre-Deployment

- [ ] All secrets stored in environment variables (not in code)
- [ ] JWT secret is at least 64 characters
- [ ] Database password is strong (24+ characters)
- [ ] CORS origins configured for production domain only
- [ ] Rate limiting enabled (`ENABLE_RATE_LIMITING=true`)
- [ ] SSL/TLS enabled for all connections
- [ ] Supabase RLS policies configured
- [ ] Security headers configured in nginx

### Post-Deployment

- [ ] Verify HTTPS is enforced
- [ ] Verify rate limiting is working
- [ ] Verify health endpoints are accessible
- [ ] Check Sentry for any initial errors
- [ ] Verify database backups are scheduled
- [ ] Test authentication flow

### Security Headers (nginx)

```nginx
# Already configured in frontend/nginx.conf
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
```

## Backup & Recovery

### Automated Backups

Configure via environment variables:

```bash
BACKUP_ENABLED=true
BACKUP_SCHEDULE=0 2 * * *  # Daily at 2 AM
BACKUP_RETENTION_DAYS=30
BACKUP_S3_BUCKET=efir-budget-backups
```

### Manual Backup

```bash
# Database backup
docker exec efir-db pg_dump -U postgres efir_budget | gzip > backup-$(date +%Y%m%d).sql.gz

# Upload to S3
aws s3 cp backup-$(date +%Y%m%d).sql.gz s3://efir-budget-backups/
```

### Recovery Procedure

1. Stop the application
2. Restore the database from backup
3. Run any pending migrations
4. Start the application
5. Verify data integrity

```bash
# Stop application
docker compose down

# Restore database
gunzip -c backup.sql.gz | docker exec -i efir-db psql -U postgres efir_budget

# Run migrations
cd backend && alembic upgrade head

# Start application
docker compose up -d
```

## Troubleshooting

### Common Issues

#### 1. Database Connection Failed

```bash
# Check database is running
docker compose ps db

# Check connection
docker exec efir-backend python -c "from app.database import engine; print('OK')"
```

#### 2. Redis Connection Failed

```bash
# Check Redis is running
docker compose ps redis

# Test connection
docker exec efir-redis redis-cli ping
```

#### 3. CORS Errors

Verify `ALLOWED_ORIGINS` environment variable includes your frontend domain.

#### 4. Rate Limit Exceeded

Increase limits or verify Redis is connected:

```bash
RATE_LIMIT_PER_MINUTE=500  # Increase limit
```

### Log Analysis

```bash
# View backend logs
docker compose logs -f backend

# View nginx access logs
docker compose logs -f frontend

# Filter by error level
docker compose logs backend 2>&1 | grep -i error
```

### Performance Issues

1. Check database query performance via Supabase dashboard
2. Review Sentry for slow transactions
3. Check Redis cache hit rate
4. Analyze bundle size: `cd frontend && ANALYZE=true npm run build`

## Version Information

- **Application Version**: 0.1.0
- **Last Updated**: December 2025
- **Supported Environments**: Development, Staging, Production
