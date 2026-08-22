/**
 * ModelVault API Client
 * Consumes FastAPI REST endpoints under /api/v1 with centralized error handling,
 * response normalization, filter parameter formatting, and mock fallback option.
 */

import { mockData } from '../mockData';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
const USE_MOCK_FALLBACK = import.meta.env.VITE_USE_MOCK_FALLBACK === 'true';

// Local triage state storage
let localReviewedState = {};

/**
 * Custom API Error class with status code and error details.
 */
export class ApiError extends Error {
  constructor(message, status, details = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.details = details;
  }
}

/**
 * Shared fetch helper for JSON parsing, HTTP error checks, and timeouts.
 */
async function request(endpoint, options = {}) {
  const url = `${BASE_URL.replace(/\/$/, '')}/${endpoint.replace(/^\//, '')}`;
  const config = {
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      ...options.headers,
    },
    ...options,
  };

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 10000);
  config.signal = controller.signal;

  try {
    const response = await fetch(url, config);
    clearTimeout(timeoutId);

    // Handle non-JSON or empty responses
    const contentType = response.headers.get('content-type');
    let data = null;
    if (contentType && contentType.includes('application/json')) {
      data = await response.json().catch(() => null);
    } else {
      const text = await response.text().catch(() => '');
      data = text ? { message: text } : null;
    }

    if (!response.ok) {
      const errorMessage =
        data?.detail || data?.message || `Request failed with HTTP status ${response.status}`;
      throw new ApiError(errorMessage, response.status, data);
    }

    return data;
  } catch (err) {
    clearTimeout(timeoutId);

    if (err.name === 'AbortError') {
      throw new ApiError(`Connection timed out after 10000ms connecting to ${url}`, 408);
    }

    if (err instanceof ApiError) {
      throw err;
    }

    if (USE_MOCK_FALLBACK) {
      console.warn(`[ModelVault API] Network issue for ${url}, falling back to mock mode.`, err);
      return null; // Signals fallback to caller
    }

    throw new ApiError(
      `Unable to reach backend at ${BASE_URL}. Verify backend service is running. (${err.message})`,
      0
    );
  }
}

/**
 * Helper to normalize backend SuspiciousEvent response objects
 * into the unified UI structure expected by frontend components.
 */
function normalizeSuspiciousEvent(item) {
  if (!item) return null;
  const itemKey = item.event_id || item.model_id || item.id;
  const isReviewed = localReviewedState[itemKey] !== undefined ? localReviewedState[itemKey] : (item.reviewed || false);

  // Parse evidence array into standard event objects if strings are returned
  const formattedEvidence = Array.isArray(item.evidence)
    ? item.evidence.map((ev, idx) => {
        if (typeof ev === 'string') {
          return {
            event_id: `ev-${idx + 1}`,
            source: item.model_id?.includes('s3') ? 'S3' : 'MODEL_ACCESS',
            event_name: 'SuspiciousActivity',
            ip_address: item.ip_address || '198.51.100.42',
            event_time_reconciled: item.timestamp || new Date().toISOString(),
            extra: { detail: ev }
          };
        }
        return ev;
      })
    : [];

  return {
    ...item,
    id: item.id || item.event_id,
    model_id: item.model_id || 'mdl-unknown',
    model_name: item.model_name || item.model_id || 'Unknown Model',
    owner: item.owner || item.user_id || 'usr-unknown',
    user_id: item.user_id || item.owner || 'usr-unknown',
    flagged_at: item.timestamp || item.flagged_at || new Date().toISOString(),
    timestamp: item.timestamp || item.flagged_at || new Date().toISOString(),
    anomaly_score: item.anomaly_score !== undefined ? item.anomaly_score : (item.risk_score ? item.risk_score / 100 : 0.85),
    risk_score: item.risk_score !== undefined ? item.risk_score : 85.0,
    severity: item.severity || 'CRITICAL',
    reason: item.reason || 'Suspicious access pattern detected by ModelVault engine.',
    evidence: formattedEvidence,
    reviewed: isReviewed,
  };
}

/**
 * API Service Contract
 */
export const api = {
  /**
   * GET /dashboard/summary
   * Returns complete telemetry stats and top suspicious incidents.
   */
  async getDashboardSummary() {
    try {
      const data = await request('/dashboard/summary');
      if (data) {
        return {
          total_models: data.total_models,
          total_users: data.total_users,
          total_events: data.total_events,
          flagged_count: data.suspicious_events || data.anomalous_events,
          active_anomalies: data.critical_events || data.anomalous_events,
          models_at_risk: data.models_at_risk,
          exfiltration_events: data.exfiltration_suspected_events,
          production_usage_events: data.production_usage_events,
          top_suspicious: (data.top_suspicious_events || []).map(normalizeSuspiciousEvent),
        };
      }
    } catch (err) {
      if (!USE_MOCK_FALLBACK) throw err;
    }
    // Fallback if configured
    return {
      total_models: mockData.stats.total_models,
      flagged_count: mockData.stats.flagged_count,
      active_anomalies: mockData.stats.active_anomalies,
      top_suspicious: mockData.topSuspicious.map(normalizeSuspiciousEvent),
    };
  },

  /**
   * GET /dashboard/stats — Telemetry stats
   */
  async getStats() {
    try {
      const summary = await this.getDashboardSummary();
      return summary;
    } catch (err) {
      if (USE_MOCK_FALLBACK) {
        return {
          total_models: mockData.stats.total_models,
          flagged_count: mockData.stats.flagged_count,
          active_anomalies: mockData.stats.active_anomalies,
        };
      }
      throw err;
    }
  },

  /**
   * GET /dashboard/top-suspicious
   * Returns top 3 anomalous/suspicious incidents.
   */
  async getTopSuspicious() {
    try {
      const data = await request('/dashboard/top-suspicious');
      if (Array.isArray(data)) {
        return data.map(normalizeSuspiciousEvent);
      }
    } catch (err) {
      if (!USE_MOCK_FALLBACK) throw err;
    }
    return mockData.topSuspicious.map(normalizeSuspiciousEvent);
  },

  /**
   * GET /suspicious-events?user_id=&model_id=&severity=&start_time=&end_time=&skip=&limit=
   * Lists all flagged suspicious model incidents with filtering.
   */
  async getFlaggedModels(filters = {}) {
    const params = new URLSearchParams();
    if (filters.user_id && filters.user_id !== 'ALL') params.append('user_id', filters.user_id);
    if (filters.model_id && filters.model_id !== 'ALL') params.append('model_id', filters.model_id);
    if (filters.severity && filters.severity !== 'ALL') params.append('severity', filters.severity);
    if (filters.start_time) params.append('start_time', filters.start_time);
    if (filters.end_time) params.append('end_time', filters.end_time);
    if (filters.limit) params.append('limit', filters.limit);
    if (filters.skip !== undefined) params.append('skip', filters.skip);

    const qs = params.toString() ? `?${params.toString()}` : '';
    try {
      const data = await request(`/suspicious-events${qs}`);
      if (Array.isArray(data)) {
        return data.map(normalizeSuspiciousEvent);
      }
    } catch (err) {
      if (!USE_MOCK_FALLBACK) throw err;
    }

    // Mock fallback logic
    let list = mockData.flaggedModels.map(normalizeSuspiciousEvent);
    if (filters.reviewed === 'REVIEWED') {
      list = list.filter((m) => m.reviewed);
    } else if (filters.reviewed === 'UNREVIEWED') {
      list = list.filter((m) => !m.reviewed);
    }
    return list;
  },

  /**
   * GET /suspicious-events
   */
  async getSuspiciousEvents(filters = {}) {
    return this.getFlaggedModels(filters);
  },

  /**
   * GET /suspicious-events/{id}
   */
  async getSuspiciousEventById(id) {
    try {
      const data = await request(`/suspicious-events/${id}`);
      return normalizeSuspiciousEvent(data);
    } catch (err) {
      if (!USE_MOCK_FALLBACK) throw err;
      const found = mockData.flaggedModels.find((m) => m.model_id === id || m.id === id);
      return normalizeSuspiciousEvent(found);
    }
  },

  /**
   * On-demand evidence and investigation timeline fetcher for a specific model or event
   */
  async getModelEvidence(modelId) {
    try {
      // 1. Try model investigation timeline
      const timelineData = await request(`/investigations/model/${modelId}`);
      if (timelineData && Array.isArray(timelineData.timeline)) {
        return timelineData.timeline.map((step) => ({
          event_id: step.event_id || `evt-${step.step}`,
          source: step.source || 'CLOUD',
          event_name: step.event_name || 'SecurityEvent',
          user_id: step.user_id || 'usr-unknown',
          ip_address: step.ip_address || '198.51.100.42',
          event_time_reconciled: step.timestamp || new Date().toISOString(),
          extra: {
            description: step.description,
            resource_type: step.resource_type,
            details: step.details,
          },
        }));
      }
      // 2. Try suspicious event detail fallback
      const se = await request(`/suspicious-events/${modelId}`);
      if (se && Array.isArray(se.evidence)) {
        return normalizeSuspiciousEvent(se).evidence;
      }
    } catch (err) {
      if (!USE_MOCK_FALLBACK) throw err;
    }
    const found = mockData.flaggedModels.find((m) => m.model_id === modelId);
    return found?.evidence || [];
  },

  /**
   * GET /models — List all registered ML models
   */
  async getModels() {
    try {
      const data = await request('/models');
      if (Array.isArray(data)) return data;
    } catch (err) {
      if (!USE_MOCK_FALLBACK) throw err;
    }
    return mockData.flaggedModels.map((m) => ({
      id: m.model_id,
      model_id: m.model_id,
      name: m.model_name,
      model_name: m.model_name,
      owner: m.owner,
    }));
  },

  /**
   * GET /models/{id} — Detailed model metadata
   */
  async getModelById(id) {
    try {
      return await request(`/models/${id}`);
    } catch (err) {
      if (!USE_MOCK_FALLBACK) throw err;
      return { id, model_id: id, name: id };
    }
  },

  /**
   * GET /users — List all system users / owners
   */
  async getUsers() {
    try {
      const data = await request('/users');
      if (Array.isArray(data)) return data;
    } catch (err) {
      if (!USE_MOCK_FALLBACK) throw err;
    }
    const owners = Array.from(new Set(mockData.flaggedModels.map((m) => m.owner)));
    return owners.map((o, idx) => ({
      id: `usr-00${idx + 1}`,
      user_id: `usr-00${idx + 1}`,
      name: o,
      username: o,
      email: `${o}@modelvault.io`,
    }));
  },

  /**
   * GET /users/{id}/investigation
   */
  async getUserInvestigation(userId) {
    try {
      return await request(`/investigations/user/${userId}`);
    } catch (err) {
      if (!USE_MOCK_FALLBACK) throw err;
      return { user_id: userId, timeline: [] };
    }
  },

  /**
   * GET /events — Raw/Normalized log events stream
   */
  async getEvents(filters = {}) {
    const params = new URLSearchParams();
    if (filters.user_id && filters.user_id !== 'ALL') params.append('user_id', filters.user_id);
    if (filters.model_id && filters.model_id !== 'ALL') params.append('model_id', filters.model_id);
    if (filters.source && filters.source !== 'ALL') params.append('source', filters.source);
    if (filters.start_time) params.append('start_time', filters.start_time);
    if (filters.end_time) params.append('end_time', filters.end_time);
    if (filters.anomaly_only) params.append('anomaly_only', true);
    if (filters.limit) params.append('limit', filters.limit);
    if (filters.skip !== undefined) params.append('skip', filters.skip);

    const qs = params.toString() ? `?${params.toString()}` : '';
    try {
      return await request(`/events${qs}`);
    } catch (err) {
      if (!USE_MOCK_FALLBACK) throw err;
      return mockData.flaggedModels.flatMap((m) => m.evidence || []);
    }
  },

  /**
   * GET /events/{id}
   */
  async getEventById(id) {
    try {
      return await request(`/events/${id}`);
    } catch (err) {
      if (!USE_MOCK_FALLBACK) throw err;
      return null;
    }
  },

  /**
   * GET /anomalies
   */
  async getAnomalies(filters = {}) {
    const params = new URLSearchParams();
    if (filters.anomalous_only) params.append('anomalous_only', true);
    if (filters.limit) params.append('limit', filters.limit);
    if (filters.skip !== undefined) params.append('skip', filters.skip);
    const qs = params.toString() ? `?${params.toString()}` : '';

    try {
      return await request(`/anomalies${qs}`);
    } catch (err) {
      if (!USE_MOCK_FALLBACK) throw err;
      return [];
    }
  },

  /**
   * GET /anomalies/top
   */
  async getTopAnomalies(limit = 3) {
    try {
      return await request(`/anomalies/top?limit=${limit}`);
    } catch (err) {
      if (!USE_MOCK_FALLBACK) throw err;
      return [];
    }
  },

  /**
   * GET /investigations/event/{id}
   */
  async getEventInvestigation(eventId) {
    try {
      return await request(`/investigations/event/${eventId}`);
    } catch (err) {
      if (!USE_MOCK_FALLBACK) throw err;
      return { event_id: eventId, timeline: [] };
    }
  },

  /**
   * GET /investigations/model/{id}
   */
  async getModelInvestigation(modelId) {
    try {
      return await request(`/investigations/model/${modelId}`);
    } catch (err) {
      if (!USE_MOCK_FALLBACK) throw err;
      return { model_id: modelId, timeline: [] };
    }
  },

  /**
   * Local triage mark / review
   */
  async reviewFlaggedModel(modelId, reviewed = true) {
    localReviewedState[modelId] = reviewed;
    return { model_id: modelId, reviewed, status: 'success' };
  },

  /**
   * POST /users
   */
  async signUp(userData) {
    try {
      return await request('/users', {
        method: 'POST',
        body: JSON.stringify(userData),
      });
    } catch (err) {
      if (!USE_MOCK_FALLBACK) throw err;
      return {
        id: `usr-${Date.now()}`,
        username: userData.username,
        email: userData.email,
        role: userData.role || 'SecOps Analyst',
        department: userData.department || 'Threat Intel',
        created_at: new Date().toISOString(),
      };
    }
  },
};
