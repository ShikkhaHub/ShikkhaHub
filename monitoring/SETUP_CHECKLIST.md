# Production Monitoring Setup Checklist

## Pre-Launch (Before Day 1)

### Error Tracking - Sentry
- [ ] Create Sentry account and organization
- [ ] Create projects for backend, frontend, and mobile
- [ ] Get DSN keys for each project
- [ ] Install Sentry packages in each codebase
- [ ] Configure Sentry in code (see docs/MONITORING.md)
- [ ] Test error capture with test event
- [ ] Set up Slack integration in Sentry
- [ ] Create alert rules for critical errors
- [ ] Set release tracking (link to Git commits)

**Estimated Time**: 2 hours

### Analytics - Google Analytics 4
- [ ] Create GA4 property for shikkhahub.edu.bd
- [ ] Get measurement ID
- [ ] Install @react-google-analytics in frontend
- [ ] Configure in React app
- [ ] Create custom events for key actions
- [ ] Set up goals/conversions (search, save, review)
- [ ] Test event tracking
- [ ] Create dashboard for key metrics

**Estimated Time**: 1 hour

### Analytics - Vercel Analytics
- [ ] Enable Vercel Analytics in project settings
- [ ] Install @vercel/analytics in frontend
- [ ] Verify data collection
- [ ] Set up custom events

**Estimated Time**: 30 minutes

### Health Checks - Uptime Robot
- [ ] Create Uptime Robot account
- [ ] Add monitor for frontend (https://shikkhahub.edu.bd/)
- [ ] Add monitor for backend health (/health endpoint)
- [ ] Set check interval to 5 minutes
- [ ] Configure Slack notifications for downtime
- [ ] Test alerts by stopping a service
- [ ] Set response time thresholds

**Estimated Time**: 45 minutes

### Logging Setup
- [ ] Configure structured logging in backend (JSON format)
- [ ] Configure structured logging in frontend
- [ ] Send logs to CloudWatch or similar service
- [ ] Create dashboard for log aggregation
- [ ] Set up log retention policies

**Estimated Time**: 1.5 hours

### Database Monitoring
- [ ] Enable slow query log (> 1 second)
- [ ] Set up query performance tracking
- [ ] Monitor connection pool usage
- [ ] Create dashboard for DB metrics
- [ ] Set up alerts for connection pool > 90%

**Estimated Time**: 1 hour

### Real User Monitoring
- [ ] Install web-vitals library
- [ ] Implement Core Web Vitals tracking
- [ ] Send to analytics/Sentry
- [ ] Create dashboard for RUM metrics
- [ ] Set thresholds for alerts

**Estimated Time**: 1 hour

### Slack Integration
- [ ] Create Slack workspace #alerts channel
- [ ] Generate Slack webhook URLs
- [ ] Set up Slack integration in Sentry
- [ ] Set up Slack integration in Uptime Robot
- [ ] Test alerts by triggering each service

**Estimated Time**: 1 hour

### Environment Variables
- [ ] Add all monitoring env vars to production
- [ ] Add to Vercel project settings
- [ ] Add to backend configuration
- [ ] Test that all services can reach endpoints

**Estimated Time**: 30 minutes

**Total Estimated Time**: 9 hours (can be parallelized)

---

## First Week

### Day 1-2: Monitor Closely
- [ ] Watch Sentry for errors
- [ ] Check analytics data flow
- [ ] Verify uptime robot is checking correctly
- [ ] Monitor backend response times
- [ ] Monitor database performance

### Day 3-5: Tune Thresholds
- [ ] Review baseline metrics
- [ ] Adjust alert thresholds based on actual data
- [ ] Fine-tune log verbosity
- [ ] Create runbooks for common issues
- [ ] Set up on-call rotation

---

## Post-Launch (Week 2+)

### Week 2: Build Dashboard
- [ ] Create executive dashboard
  - Uptime (24h, 7d, 30d)
  - Error rate
  - Response times
  - User metrics
  - Search performance
- [ ] Create operational dashboard
  - Detailed error logs
  - Slow queries
  - API latency by endpoint
  - Database connections
  - Cache hit rates

### Week 3: Optimization
- [ ] Analyze performance bottlenecks
- [ ] Optimize slow endpoints
- [ ] Optimize database queries
- [ ] Improve cache strategy
- [ ] Document optimization decisions

### Week 4: Continuous Improvement
- [ ] Weekly metric review
- [ ] Monthly trend analysis
- [ ] Quarterly architecture review
- [ ] Plan for scaling

---

## Monitoring Configuration Summary

### Required Services
- Sentry (error tracking): $99-799/month
- Google Analytics (analytics): Free
- Vercel Analytics (performance): Included
- Uptime Robot (uptime): $10-20/month
- Slack (notifications): Free to paid

### Total Monthly Cost
- Sentry: ~$150
- Uptime Robot: ~$15
- Logging service: ~$50 (optional)
- **Total: ~$215/month**

### Data Retention
- Sentry events: 90 days (default)
- Google Analytics: 14 months (default)
- Logs: 30 days (configurable)
- Uptime history: 90 days (default)

---

## Critical Metrics to Track

### Frontend
- Page load time (LCP, FCP, TTFB)
- Interaction responsiveness (INP)
- Cumulative layout shift (CLS)
- Error rate
- Search latency

### Backend
- Response time by endpoint
- Error rate
- Database query time
- Cache hit rate
- Memory usage

### Database
- Query latency
- Connection pool usage
- Replication lag (if applicable)
- Disk usage
- Lock wait times

### Business
- User registrations (daily)
- Searches per user
- Institutions saved
- Reviews submitted
- App installs

---

## Alerts Setup

### Critical (Immediate Action Required)
```
- Error rate > 1% (5 min average)
- API response time > 5 seconds (2 min average)
- Backend service down (1 check failed)
- Database connection errors > 10 (1 min)
- SSL certificate expiring in < 7 days
```

### Warning (Investigate Within 1 Hour)
```
- Error rate > 0.1% (5 min average)
- API response time > 2 seconds (5 min average)
- Search latency p95 > 500ms (5 min average)
- Memory usage > 80% (10 min average)
- Rate limiting active (5 min average)
```

### Info (Daily Review)
```
- Low traffic periods
- High traffic spikes
- Unusual user behavior patterns
- Cache efficiency metrics
```

---

## On-Call Runbooks

### High Error Rate
1. Check Sentry for error patterns
2. Is it a recent deployment? → Rollback
3. Check for external service failures
4. Check database connectivity
5. Check rate limiting

### Slow API Response
1. Check database query performance
2. Check server CPU and memory
3. Check network latency
4. Look for N+1 queries
5. Review recent code changes

### Database Issues
1. Check connection pool status
2. Check for long-running queries
3. Check disk space
4. Check replication lag
5. Restart if necessary

### Search Performance Degradation
1. Check Elasticsearch status
2. Check query complexity
3. Check index size
4. Run index optimization
5. Consider scaling

---

## Success Metrics

After 1 month, you should have:
- ✅ Zero critical alert storms
- ✅ <0.1% error rate under normal load
- ✅ <500ms p95 response time
- ✅ >99.5% uptime
- ✅ Clear understanding of performance bottlenecks
- ✅ Documented runbooks for common issues

---

**Setup Start Date**: _________
**Setup Complete Date**: _________
**First Alert**: _________

---

**Owner**: DevOps Team
**Last Updated**: 2024
