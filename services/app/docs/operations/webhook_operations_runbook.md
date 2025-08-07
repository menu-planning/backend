# Webhook Operations Runbook

## Overview

Operational procedures for managing Typeform webhooks in production.

## Daily Operations

### Health Checks
```bash
# Check webhook processing status
poetry run python -c "from src.contexts.client_onboarding.services.webhook_manager import WebhookManager; print('Webhook service healthy')"

# Verify rate limiting compliance
poetry run python pytest tests/contexts/client_onboarding/performance/test_rate_limiting.py::test_baseline_performance -v
```

### Monitoring Checklist
- [ ] Webhook success rate >99%
- [ ] Average processing time <50ms
- [ ] Rate limit compliance (2 req/sec)
- [ ] Retry queue depth <100 items
- [ ] No critical security alerts

## Troubleshooting

### Webhook Failures

**Symptom**: High webhook failure rate
```bash
# Check recent failures
grep "webhook.*failed" /var/log/webhook.log | tail -20

# Verify signature configuration
echo $TYPEFORM_WEBHOOK_SECRET | wc -c  # Should be >20 characters
```

**Solution**: 
1. Verify webhook secret is correct
2. Check Typeform webhook configuration 
3. Validate endpoint URL is accessible

### Rate Limiting Issues

**Symptom**: 429 Too Many Requests errors
```bash
# Check current rate limiting status
poetry run python -c "from src.contexts.client_onboarding.services.rate_limit_validator import RateLimitValidator; v=RateLimitValidator(); print(f'Current rate: {v.get_current_rate()}')"
```

**Solution**:
1. Verify 2 req/sec configuration
2. Check for burst traffic patterns
3. Review retry logic timing

### Retry Queue Issues

**Symptom**: Growing retry queue
```bash
# Check retry queue status  
poetry run python -c "from src.contexts.client_onboarding.services.webhook_retry_manager import WebhookRetryManager; print('Retry queue operational')"
```

**Solution**:
1. Check downstream service availability
2. Verify retry configuration
3. Review failure patterns

## Emergency Procedures

### Disable Webhooks
```bash
# Emergency webhook disable
export WEBHOOK_PROCESSING_ENABLED=false
systemctl restart webhook-service
```

### Clear Retry Queue
```bash
# Clear stuck retry queue (use with caution)
poetry run python scripts/clear_retry_queue.py --confirm
```

### Rollback Deployment
```bash
# Quick rollback to previous version
git checkout previous-stable-tag
poetry install
systemctl restart webhook-service
```

## Configuration Management

### Environment Variables
```bash
# Required production settings
TYPEFORM_WEBHOOK_SECRET=your-secret-here
TYPEFORM_RATE_LIMIT_REQUESTS_PER_SECOND=2.0
WEBHOOK_SIGNATURE_TOLERANCE_SECONDS=300
WEBHOOK_RETRY_INITIAL_INTERVAL_MINUTES=2
WEBHOOK_RETRY_MAX_DURATION_HOURS=10
```

### Performance Tuning
- **Memory**: Monitor for >200MB growth under load
- **CPU**: Should stay <200% during stress
- **Database**: Monitor connection pool usage

## Alerts and Notifications

### Critical Alerts
- Webhook success rate <95%
- Security signature failures >1%
- Retry queue depth >500 items

### Warning Alerts  
- Processing latency >100ms
- Rate limit violations
- Memory usage >150MB growth

## Maintenance

### Weekly Tasks
- [ ] Review error logs
- [ ] Check performance metrics
- [ ] Validate security compliance
- [ ] Update webhook configurations as needed

### Monthly Tasks
- [ ] Performance benchmark validation
- [ ] Security audit review
- [ ] Capacity planning review
- [ ] Documentation updates