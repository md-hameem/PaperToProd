/**
 * Utility functions for API communication and token management.
 */

// We assume the FastAPI backend runs on localhost:8000 for local dev
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export function getApiUrl(path: string): string {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${API_BASE_URL}${normalizedPath}`;
}

export function saveToken(token: string) {
  if (typeof window !== 'undefined') {
    localStorage.setItem('papertoprod_token', token);
  }
}

export function getToken(): string | null {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('papertoprod_token');
  }
  return null;
}

export function removeToken() {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('papertoprod_token');
  }
}

/**
 * Perform an authenticated fetch request to the backend.
 */
export async function apiFetch(path: string, options: RequestInit = {}) {
  const token = getToken();

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(getApiUrl(path), {
    ...options,
    headers,
  });

  if (response.status === 401) {
    // Unauthorized: clear token and optionally redirect to login
    removeToken();
    if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/login')) {
      window.location.href = '/login';
    }
  }

  return response;
}

/**
 * Creates a new job with the given arXiv URL.
 */
export async function createJob(paperUrl: string) {
  const response = await apiFetch('/jobs', {
    method: 'POST',
    body: JSON.stringify({ paper_url: paperUrl }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to submit job');
  }

  return response.json();
}

/**
 * Fetches a specific job by ID.
 */
export async function getJob(jobId: string) {
  const response = await apiFetch(`/jobs/${jobId}`);
  if (!response.ok) {
    throw new Error('Failed to fetch job details');
  }
  return response.json();
}

/**
 * Lists all jobs for the authenticated user.
 */
export async function listJobs(skip: number = 0, limit: number = 20) {
  const response = await apiFetch(`/jobs?skip=${skip}&limit=${limit}`);
  if (!response.ok) {
    throw new Error('Failed to list jobs');
  }
  return response.json();
}

/**
 * Approve a job's repository to resume execution.
 */
export async function approveJob(jobId: string, repoUrl: string) {
  const response = await apiFetch(`/jobs/${jobId}/approve`, {
    method: 'POST',
    body: JSON.stringify({ repo_url: repoUrl }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to approve job');
  }

  return response.json();
}
