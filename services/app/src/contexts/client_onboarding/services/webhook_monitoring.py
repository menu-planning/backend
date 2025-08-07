"""
Webhook Monitoring Service

Production monitoring and alerting for webhook operations.
"""

import time
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class WebhookMetrics:
    """Webhook performance metrics."""
    total_processed: int = 0
    total_successful: int = 0
    total_failed: int = 0
    average_latency_ms: float = 0.0
    signature_verifications: int = 0
    signature_failures: int = 0
    rate_limit_violations: int = 0
    retry_queue_depth: int = 0
    last_updated: datetime = field(default_factory=datetime.now)
    
    @property
    def success_rate(self) -> float:
        """Calculate webhook success rate percentage."""
        if self.total_processed == 0:
            return 0.0
        return (self.total_successful / self.total_processed) * 100
    
    @property 
    def signature_success_rate(self) -> float:
        """Calculate signature verification success rate percentage."""
        if self.signature_verifications == 0:
            return 0.0
        successful_sigs = self.signature_verifications - self.signature_failures
        return (successful_sigs / self.signature_verifications) * 100


class WebhookMonitoring:
    """Production webhook monitoring service."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.metrics = WebhookMetrics()
        self.alert_thresholds = {
            'success_rate_critical': 95.0,  # Alert if success rate drops below 95%
            'success_rate_warning': 98.0,   # Warning if below 98%
            'signature_failure_critical': 5.0,  # Alert if signature failure rate > 5%
            'latency_warning_ms': 100.0,    # Warning if latency > 100ms
            'latency_critical_ms': 500.0,   # Critical if latency > 500ms
            'retry_queue_warning': 100,     # Warning if queue depth > 100
            'retry_queue_critical': 500     # Critical if queue depth > 500
        }
    
    def record_webhook_processed(self, success: bool, latency_ms: float) -> None:
        """Record webhook processing result."""
        self.metrics.total_processed += 1
        if success:
            self.metrics.total_successful += 1
        else:
            self.metrics.total_failed += 1
            
        # Update average latency (simple moving average)
        total_latency = self.metrics.average_latency_ms * (self.metrics.total_processed - 1)
        self.metrics.average_latency_ms = (total_latency + latency_ms) / self.metrics.total_processed
        self.metrics.last_updated = datetime.now()
        
        # Check for alerts
        self._check_performance_alerts()
    
    def record_signature_verification(self, success: bool) -> None:
        """Record signature verification result."""
        self.metrics.signature_verifications += 1
        if not success:
            self.metrics.signature_failures += 1
            
        self._check_security_alerts()
    
    def record_rate_limit_violation(self) -> None:
        """Record rate limit violation."""
        self.metrics.rate_limit_violations += 1
        self.logger.warning("Rate limit violation detected")
    
    def update_retry_queue_depth(self, depth: int) -> None:
        """Update retry queue depth."""
        self.metrics.retry_queue_depth = depth
        self._check_queue_alerts()
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get current webhook health status."""
        status = {
            "healthy": True,
            "timestamp": datetime.now().isoformat(),
            "metrics": {
                "total_processed": self.metrics.total_processed,
                "success_rate": round(self.metrics.success_rate, 2),
                "average_latency_ms": round(self.metrics.average_latency_ms, 2),
                "signature_success_rate": round(self.metrics.signature_success_rate, 2),
                "rate_limit_violations": self.metrics.rate_limit_violations,
                "retry_queue_depth": self.metrics.retry_queue_depth
            },
            "alerts": []
        }
        
        # Check health thresholds
        if self.metrics.success_rate < self.alert_thresholds['success_rate_critical']:
            status["healthy"] = False
            status["alerts"].append(f"CRITICAL: Success rate {self.metrics.success_rate:.1f}% below threshold")
            
        if self.metrics.signature_success_rate < (100 - self.alert_thresholds['signature_failure_critical']):
            status["healthy"] = False
            status["alerts"].append(f"CRITICAL: High signature failure rate")
            
        if self.metrics.average_latency_ms > self.alert_thresholds['latency_critical_ms']:
            status["healthy"] = False
            status["alerts"].append(f"CRITICAL: High latency {self.metrics.average_latency_ms:.1f}ms")
            
        if self.metrics.retry_queue_depth > self.alert_thresholds['retry_queue_critical']:
            status["healthy"] = False
            status["alerts"].append(f"CRITICAL: High retry queue depth {self.metrics.retry_queue_depth}")
        
        return status
    
    def reset_metrics(self) -> None:
        """Reset metrics (for testing or periodic reset)."""
        self.metrics = WebhookMetrics()
        self.logger.info("Webhook metrics reset")
    
    def _check_performance_alerts(self) -> None:
        """Check for performance-related alerts."""
        if self.metrics.success_rate < self.alert_thresholds['success_rate_critical']:
            self.logger.critical(f"Webhook success rate critically low: {self.metrics.success_rate:.1f}%")
        elif self.metrics.success_rate < self.alert_thresholds['success_rate_warning']:
            self.logger.warning(f"Webhook success rate below warning threshold: {self.metrics.success_rate:.1f}%")
            
        if self.metrics.average_latency_ms > self.alert_thresholds['latency_critical_ms']:
            self.logger.critical(f"Webhook latency critically high: {self.metrics.average_latency_ms:.1f}ms")
        elif self.metrics.average_latency_ms > self.alert_thresholds['latency_warning_ms']:
            self.logger.warning(f"Webhook latency elevated: {self.metrics.average_latency_ms:.1f}ms")
    
    def _check_security_alerts(self) -> None:
        """Check for security-related alerts."""
        failure_rate = (self.metrics.signature_failures / self.metrics.signature_verifications) * 100
        if failure_rate > self.alert_thresholds['signature_failure_critical']:
            self.logger.critical(f"High signature verification failure rate: {failure_rate:.1f}%")
    
    def _check_queue_alerts(self) -> None:
        """Check for retry queue alerts."""
        if self.metrics.retry_queue_depth > self.alert_thresholds['retry_queue_critical']:
            self.logger.critical(f"Retry queue depth critically high: {self.metrics.retry_queue_depth}")
        elif self.metrics.retry_queue_depth > self.alert_thresholds['retry_queue_warning']:
            self.logger.warning(f"Retry queue depth elevated: {self.metrics.retry_queue_depth}")


# Global monitoring instance
monitoring = WebhookMonitoring()