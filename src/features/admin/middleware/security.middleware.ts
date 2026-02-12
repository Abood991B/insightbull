import { securityConfig } from '../config/security.config';

// Rate limiting implementation
interface RateLimitEntry {
  count: number;
  resetTime: number;
}

const rateLimitMap = new Map<string, RateLimitEntry>();

export const checkRateLimit = (identifier: string): boolean => {
  const now = Date.now();
  const entry = rateLimitMap.get(identifier);
  
  if (!entry || now > entry.resetTime) {
    // New window or expired window
    rateLimitMap.set(identifier, {
      count: 1,
      resetTime: now + securityConfig.rateLimit.windowMs
    });
    return true;
  }
  
  if (entry.count >= securityConfig.rateLimit.maxAttempts) {
    return false;
  }
  
  entry.count++;
  return true;
};

// Security headers middleware
export const applySecurityHeaders = () => {
  if (typeof window !== 'undefined') {
    // Apply CSP meta tag
    const meta = document.createElement('meta');
    meta.httpEquiv = 'Content-Security-Policy';
    meta.content = securityConfig.headers['Content-Security-Policy'];
    document.head.appendChild(meta);
  }
};

// XSS Protection
export const sanitizeInput = (input: string): string => {
  return input
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;')
    .replace(/\//g, '&#x2F;');
};

// CSRF Token generation
export const generateCSRFToken = (): string => {
  const array = new Uint8Array(32);
  crypto.getRandomValues(array);
  return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
};

// Session validation
export const validateSession = (sessionData: any): boolean => {
  if (!sessionData) return false;
  
  const now = Date.now();
  
  // Check expiration
  if (sessionData.expiresAt && now > sessionData.expiresAt) {
    return false;
  }
  
  // Check last activity
  if (sessionData.lastActivity) {
    const inactiveTime = now - sessionData.lastActivity;
    if (inactiveTime > securityConfig.admin.sessionTimeout) {
      return false;
    }
  }
  
  return true;
};

// Audit logging
export interface AuditLog {
  timestamp: string;
  event: string;
  userId?: string;
  email?: string;
  ip?: string;
  userAgent?: string;
  details?: any;
  severity: 'info' | 'warning' | 'error' | 'critical';
}

const auditLogs: AuditLog[] = [];

export const logAuditEvent = (
  event: string,
  severity: AuditLog['severity'] = 'info',
  details?: any
): void => {
  const log: AuditLog = {
    timestamp: new Date().toISOString(),
    event,
    severity,
    userAgent: navigator.userAgent,
    details
  };
  
  auditLogs.push(log);
  
  // Keep only last 1000 logs in memory
  if (auditLogs.length > 1000) {
    auditLogs.shift();
  }
  
  // Log audit events only in development
  if (import.meta.env.DEV) {
    console.log('[AUDIT]', log);
  }
};

export const getAuditLogs = (
  filter?: { 
    severity?: AuditLog['severity']; 
    startDate?: Date; 
    endDate?: Date;
    event?: string;
  }
): AuditLog[] => {
  let logs = [...auditLogs];
  
  if (filter) {
    if (filter.severity) {
      logs = logs.filter(log => log.severity === filter.severity);
    }
    
    if (filter.startDate) {
      logs = logs.filter(log => new Date(log.timestamp) >= filter.startDate!);
    }
    
    if (filter.endDate) {
      logs = logs.filter(log => new Date(log.timestamp) <= filter.endDate!);
    }
    
    if (filter.event) {
      logs = logs.filter(log => log.event.includes(filter.event!));
    }
  }
  
  return logs.reverse(); // Most recent first
};

// Initialize security middleware
export const initializeSecurity = (): void => {
  applySecurityHeaders();
  
  // Set up global error handler
  window.addEventListener('error', (event) => {
    logAuditEvent('GLOBAL_ERROR', 'error', {
      message: event.message,
      filename: event.filename,
      lineno: event.lineno,
      colno: event.colno
    });
  });
  
  // Set up unhandled promise rejection handler
  window.addEventListener('unhandledrejection', (event) => {
    logAuditEvent('UNHANDLED_PROMISE_REJECTION', 'error', {
      reason: event.reason
    });
  });
  
  // Detect potential XSS attempts
  const originalSetAttribute = Element.prototype.setAttribute;
  Element.prototype.setAttribute = function(name: string, value: string) {
    if (name === 'href' || name === 'src') {
      if (value.includes('javascript:') || value.includes('data:text/html')) {
        logAuditEvent('POTENTIAL_XSS_ATTEMPT', 'critical', {
          attribute: name,
          value: value
        });
        return;
      }
    }
    originalSetAttribute.call(this, name, value);
  };
};
