/**
 * ModelVault API Client
 * Built using native fetch (no axios) with centralized error handling,
 * response parsing, and optional mock data fallback for resilient demonstrations.
 */

import { mockData } from '../mockData';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const USE_MOCK_FALLBACK = import.meta.env.VITE_USE_MOCK_FALLBACK === 'true';

// In-memory mock review state storage for seamless offline fallback toggles
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
  const timeoutId = setTimeout(() => controller.abort(), 8000);
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
      throw new ApiError(`Connection timed out after 8000ms connecting to ${url}`, 408);
    }

    if (err instanceof ApiError) {
      throw err;
    }

    // Network error / CORS failure / Backend offline
    throw new ApiError(
      `Unable to reach backend at ${BASE_URL}. Verify backend service is running. (${err.message})`,
      0
    );
  }
}

/**
 * API Methods
 */
export const api = {
  /**
   * GET /dashboard/top-suspicious
   * Fetches top 3 anomalous models with threat scores and evidence summaries.
   */
  async getTopSuspicious() {
    try {
      const data = await request('/dashboard/top-suspicious');
      return Array.isArray(data) ? data : data?.topSuspicious || [];
    } catch (err) {
      if (USE_MOCK_FALLBACK) {
        console.warn('[ModelVault API] Backend offline, falling back to mockData.topSuspicious', err);
        return mockData.topSuspicious.map((m) => ({
          ...m,
          reviewed: localReviewedState[m.model_id] !== undefined ? localReviewedState[m.model_id] : m.reviewed,
        }));
      }
      throw err;
    }
  },

  /**
   * GET /dashboard/flagged-models?reviewed=&min_score=
   * Lists all flagged ML models with optional filtering.
   */
  async getFlaggedModels(filters = {}) {
    const params = new URLSearchParams();
    if (filters.reviewed !== undefined && filters.reviewed !== 'ALL') {
      params.append('reviewed', filters.reviewed === 'REVIEWED');
    }
    if (filters.min_score !== undefined && filters.min_score !== '') {
      params.append('min_score', filters.min_score);
    }
    if (filters.user_id) params.append('user_id', filters.user_id);
    if (filters.model_id) params.append('model_id', filters.model_id);
    if (filters.search) params.append('search', filters.search);

    const qs = params.toString() ? `?${params.toString()}` : '';
    try {
      const data = await request(`/dashboard/flagged-models${qs}`);
      return Array.isArray(data) ? data : data?.flaggedModels || [];
    } catch (err) {
      if (USE_MOCK_FALLBACK) {
        console.warn('[ModelVault API] Backend offline, falling back to mockData.flaggedModels', err);
        let list = mockData.flaggedModels.map((m) => ({
          ...m,
          reviewed: localReviewedState[m.model_id] !== undefined ? localReviewedState[m.model_id] : m.reviewed,
        }));

        if (filters.reviewed === 'REVIEWED') {
          list = list.filter((m) => m.reviewed);
        } else if (filters.reviewed === 'UNREVIEWED') {
          list = list.filter((m) => !m.reviewed);
        }
        return list;
      }
      throw err;
    }
  },

  /**
   * GET /events?user_id=&model_id=&start_time=&end_time=&limit=&offset=
   * Fetches raw access audit logs.
   */
  async getEvents(filters = {}) {
    const params = new URLSearchParams();
    if (filters.user_id && filters.user_id !== 'ALL') params.append('user_id', filters.user_id);
    if (filters.model_id && filters.model_id !== 'ALL') params.append('model_id', filters.model_id);
    if (filters.start_time) params.append('start_time', filters.start_time);
    if (filters.end_time) params.append('end_time', filters.end_time);
    if (filters.limit) params.append('limit', filters.limit);
    if (filters.offset !== undefined) params.append('offset', filters.offset);

    const qs = params.toString() ? `?${params.toString()}` : '';
    try {
      return await request(`/events${qs}`);
    } catch (err) {
      if (USE_MOCK_FALLBACK) {
        console.warn('[ModelVault API] Backend offline, mock events fallback', err);
        // Gather evidence events from mockData
        const allEvts = mockData.flaggedModels.flatMap((m) => m.evidence || []);
        return allEvts;
      }
      throw err;
    }
  },

  /**
   * On-demand evidence fetcher for a specific model
   * Fetches full evidence events list on row click.
   */
  async getModelEvidence(modelId) {
    try {
      const data = await request(`/flagged-models/${modelId}/evidence`);
      return Array.isArray(data) ? data : data?.evidence || [];
    } catch (err) {
      if (USE_MOCK_FALLBACK) {
        console.warn(`[ModelVault API] Falling back to mock evidence for ${modelId}`);
        const found = mockData.flaggedModels.find((m) => m.model_id === modelId);
        return found?.evidence || [];
      }
      throw err;
    }
  },

  /**
   * GET /models — List all registered ML models
   */
  async getModels() {
    try {
      return await request('/models');
    } catch (err) {
      if (USE_MOCK_FALLBACK) {
        return mockData.flaggedModels.map((m) => ({
          id: m.model_id,
          name: m.model_name,
          owner: m.owner,
        }));
      }
      throw err;
    }
  },

  /**
   * GET /users — List all system users / owners
   */
  async getUsers() {
    try {
      return await request('/users');
    } catch (err) {
      if (USE_MOCK_FALLBACK) {
        const owners = Array.from(new Set(mockData.flaggedModels.map((m) => m.owner)));
        return owners.map((o, idx) => ({ id: `usr-${idx}`, username: o, email: `${o}@modelvault.io` }));
      }
      throw err;
    }
  },

  /**
   * GET /dashboard/stats — Telemetry stats
   */
  async getStats() {
    try {
      return await request('/dashboard/stats');
    } catch (err) {
      if (USE_MOCK_FALLBACK) {
        const unreviewedCount = mockData.flaggedModels.filter((m) => {
          const isRev = localReviewedState[m.model_id] !== undefined ? localReviewedState[m.model_id] : m.reviewed;
          return !isRev;
        }).length;
        return {
          total_models: mockData.stats.total_models,
          flagged_count: mockData.stats.flagged_count,
          active_anomalies: unreviewedCount,
        };
      }
      throw err;
    }
  },

  /**
   * PATCH /flagged-models/{id}/review
   * Marks a model as reviewed or unreviewed.
   */
  async reviewFlaggedModel(modelId, reviewed = true) {
    try {
      return await request(`/flagged-models/${modelId}/review`, {
        method: 'PATCH',
        body: JSON.stringify({ reviewed }),
      });
    } catch (err) {
      if (USE_MOCK_FALLBACK) {
        localReviewedState[modelId] = reviewed;
        return { model_id: modelId, reviewed, status: 'success' };
      }
      throw err;
    }
  },

  /**
   * POST /auth/signup or POST /users
   * Creates a new SecOps operator account.
   */
  async signUp(userData) {
    try {
      return await request('/users', {
        method: 'POST',
        body: JSON.stringify(userData),
      });
    } catch (err) {
      if (USE_MOCK_FALLBACK) {
        return {
          id: `usr-${Date.now()}`,
          username: userData.username,
          email: userData.email,
          role: userData.role || 'SecOps Analyst',
          department: userData.department || 'Threat Intel',
          created_at: new Date().toISOString(),
        };
      }
      throw err;
    }
  },
};
