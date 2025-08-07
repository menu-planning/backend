# Rollback Procedures

## Overview

Emergency rollback procedures for each phase of the Typeform API improvements implementation.

## General Rollback Process

### Immediate Emergency Rollback
```bash
# 1. Disable webhook processing
export WEBHOOK_PROCESSING_ENABLED=false
systemctl restart webhook-service

# 2. Rollback to previous stable version
git checkout <previous-stable-tag>
poetry install --only=main

# 3. Restart services
systemctl restart webhook-service
systemctl restart app-service
```

### Database Rollback
```bash
# Rollback to previous migration (if needed)
poetry run alembic downgrade -1

# Verify database state
poetry run alembic current
```

## Phase-Specific Rollback Procedures

### Phase 1: Security Implementation Rollback

**Risk Level**: HIGH - Affects webhook signature verification

**Rollback Steps**:
1. **Disable new security service**:
   ```bash
   # Revert to old webhook handler
   git checkout HEAD~1 -- src/contexts/client_onboarding/aws_lambda/webhook_handler.py
   ```

2. **Remove security configurations**:
   ```bash
   # Remove new security environment variables
   unset WEBHOOK_SIGNATURE_TOLERANCE_SECONDS
   unset WEBHOOK_SECURITY_LOGGING_ENABLED
   ```

3. **Validate rollback**:
   ```bash
   # Test webhook processing still works
   curl -X POST webhook-endpoint -d '{"test": "data"}'
   ```

### Phase 2: Webhook Management Rollback

**Risk Level**: MEDIUM - Affects webhook automation

**Rollback Steps**:
1. **Disable webhook manager**:
   ```bash
   export WEBHOOK_MANAGER_ENABLED=false
   ```

2. **Revert rate limiting changes**:
   ```bash
   # Restore original rate limit (4 req/sec)
   export TYPEFORM_RATE_LIMIT_REQUESTS_PER_SECOND=4
   ```

3. **Manual webhook management**:
   ```bash
   # Manually manage webhooks via Typeform UI
   # Document active webhooks for reference
   ```

### Phase 3: Retry Logic Rollback

**Risk Level**: LOW - Retry is enhancement, not critical

**Rollback Steps**:
1. **Disable retry manager**:
   ```bash
   export WEBHOOK_RETRY_ENABLED=false
   ```

2. **Clear retry queue**:
   ```bash
   poetry run python scripts/clear_retry_queue.py --confirm
   ```

3. **Fallback to manual retry**:
   ```bash
   # Manual webhook reprocessing if needed
   # Check logs for failed webhooks
   ```

### Phase 4: Testing & Documentation Rollback

**Risk Level**: MINIMAL - Documentation and tests don't affect production

**Rollback Steps**:
1. **Remove new test files** (if causing issues):
   ```bash
   rm -rf tests/contexts/client_onboarding/security/
   rm -rf tests/contexts/client_onboarding/performance/
   ```

2. **Revert documentation** (if needed):
   ```bash
   git checkout HEAD~1 -- docs/
   ```

## Validation After Rollback

### Critical Health Checks
```bash
# 1. Verify webhook processing
curl -X POST $WEBHOOK_ENDPOINT -H "Content-Type: application/json" -d '{"test": true}'

# 2. Check database connectivity
poetry run python -c "from src.db.database import get_session; print('DB OK')"

# 3. Verify rate limiting
poetry run python pytest tests/contexts/client_onboarding/core/services/test_rate_limit_validator.py -v

# 4. Check configuration
poetry run python -c "from src.contexts.client_onboarding.config import config; print(config.health_check())"
```

### Monitoring After Rollback
- Monitor webhook success rates for 2 hours
- Check error logs for any new issues
- Verify TypeForm API connectivity
- Confirm rate limiting compliance

## Emergency Contacts

### Escalation Path
1. **Technical Lead**: First point of contact for rollback decisions
2. **DevOps Team**: Infrastructure and deployment issues
3. **Security Team**: If security issues arise during rollback

### Communication
- **Internal**: Slack #incident-response channel
- **External**: Customer support team if user-facing impact
- **Documentation**: Record all rollback actions in incident log

## Recovery Procedures

### After Successful Rollback
1. **Document the incident**: Root cause, timeline, impact
2. **Plan fix deployment**: Address issues that caused rollback
3. **Update procedures**: Improve rollback documentation
4. **Test recovery**: Validate fix in staging environment

### Re-deployment Checklist
- [ ] Root cause identified and fixed
- [ ] Comprehensive testing in staging
- [ ] Rollback procedures updated
- [ ] Monitoring alerts configured
- [ ] Emergency contact list updated

## Prevention

### Deployment Safety
- Always deploy to staging first
- Use feature flags for major changes
- Implement gradual rollout strategies
- Maintain automated health checks

### Monitoring
- Set up alerts for key metrics
- Monitor webhook success rates
- Track performance degradation
- Alert on configuration issues

## Testing Rollback Procedures

### Monthly Rollback Drills
```bash
# Practice rollback in staging environment
git checkout production-backup
poetry install
# Validate functionality
# Document any issues with procedures
```

### Rollback Validation
- Test each phase rollback procedure quarterly
- Update procedures based on infrastructure changes
- Validate emergency contact information
- Review and update documentation