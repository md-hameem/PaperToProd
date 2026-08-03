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

export function saveWorkspaceId(workspaceId: string) {
  if (typeof window !== 'undefined') {
    localStorage.setItem('papertoprod_workspace_id', workspaceId);
  }
}

export function getWorkspaceId(): string | null {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('papertoprod_workspace_id');
  }
  return null;
}

/**
 * Perform an authenticated fetch request to the backend.
 */
export async function apiFetch(path: string, options: RequestInit = {}) {
  const token = getToken();
  const workspaceId = getWorkspaceId();

  // If body is FormData, do NOT set Content-Type header so the browser sets the multipart boundary.
  const isFormData = options.body instanceof FormData;
  const headers: HeadersInit = {
    ...(!isFormData && { 'Content-Type': 'application/json' }),
    ...options.headers,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  if (workspaceId) {
    headers['X-Workspace-ID'] = workspaceId;
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
 * Creates a new job using FormData (supports files).
 */
export async function createJob(formData: FormData) {
  const response = await apiFetch('/jobs', {
    method: 'POST',
    body: formData,
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

/**
 * Lists all workspaces for the authenticated user.
 */
export async function listWorkspaces() {
  const response = await apiFetch('/workspaces');
  if (!response.ok) {
    throw new Error('Failed to list workspaces');
  }
  return response.json();
}

/**
 * Lists members for a given workspace.
 */
export async function getWorkspaceMembers(workspaceId: string) {
  const response = await apiFetch(`/workspaces/${workspaceId}/members`);
  if (!response.ok) {
    throw new Error('Failed to fetch workspace members');
  }
  return response.json();
}

/**
 * Invites a member to a workspace.
 */
export async function inviteWorkspaceMember(workspaceId: string, email: string, role: string) {
  const response = await apiFetch(`/workspaces/${workspaceId}/members`, {
    method: 'POST',
    body: JSON.stringify({ email, role })
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to invite member');
  }
  return response.json();
}

/**
 * Changes a member's role.
 */
export async function changeWorkspaceRole(workspaceId: string, targetUserId: string, role: string) {
  const response = await apiFetch(`/workspaces/${workspaceId}/members/${targetUserId}`, {
    method: 'PATCH',
    body: JSON.stringify({ role })
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to change role');
  }
  return response.json();
}

// Workspace Billing API

export async function getWorkspaceUsage(workspaceId: string) {
  return apiFetch(`/workspaces/${workspaceId}/billing/usage`);
}

export async function createCheckoutSession(workspaceId: string) {
  return apiFetch(`/workspaces/${workspaceId}/billing/checkout-session`, {
    method: 'POST',
  });
}

// GitHub Integrations

export async function getGitHubIntegration(workspaceId: string) {
  return apiFetch(`/workspaces/${workspaceId}/integrations/github`);
}

export async function installGitHub(workspaceId: string) {
  return apiFetch(`/workspaces/${workspaceId}/integrations/github/install`, {
    method: 'POST',
  });
}

export async function disconnectGitHub(workspaceId: string) {
  return apiFetch(`/workspaces/${workspaceId}/integrations/github`, {
    method: 'DELETE',
  });
}

export async function pushJobToGitHub(workspaceId: string, jobId: string, repositoryName: string) {
  return apiFetch(`/workspaces/${workspaceId}/jobs/${jobId}/artifacts/push-to-github`, {
    method: 'POST',
    body: JSON.stringify({ repository_name: repositoryName }),
  });
}

export async function getArtifactTree(workspaceId: string, jobId: string) {
  return apiFetch(`/workspaces/${workspaceId}/jobs/${jobId}/artifacts/tree`, {
    headers: {
      'X-Workspace-ID': workspaceId,
    }
  });
}

export async function getArtifactFile(workspaceId: string, jobId: string, path: string) {
  return apiFetch(`/workspaces/${workspaceId}/jobs/${jobId}/artifacts/file?path=${encodeURIComponent(path)}`, {
    headers: {
      'X-Workspace-ID': workspaceId,
    }
  });
}

// User & API Keys

export async function getProfile() {
  return apiFetch('/users/me');
}

export async function updateProfile(data: { display_name?: string, email?: string }) {
  return apiFetch('/users/me', {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export async function getApiKeys() {
  return apiFetch('/users/me/api-keys');
}

export async function createApiKey(name: string) {
  return apiFetch('/users/me/api-keys', {
    method: 'POST',
    body: JSON.stringify({ name }),
  });
}

export async function revokeApiKey(id: number) {
  return apiFetch(`/users/me/api-keys/${id}`, {
    method: 'DELETE',
  });
}

/**
 * Removes a member.
 */
export async function removeWorkspaceMember(workspaceId: string, targetUserId: string) {
  const response = await apiFetch(`/workspaces/${workspaceId}/members/${targetUserId}`, {
    method: 'DELETE'
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to remove member');
  }
  return true;
}

// ── Notifications ───────────────────────────────────────────

export async function getNotifications() {
  const response = await apiFetch('/notifications');
  if (!response.ok) throw new Error('Failed to fetch notifications');
  return response.json();
}

export async function markNotificationRead(id: number) {
  const response = await apiFetch(`/notifications/${id}/read`, {
    method: 'PUT'
  });
  if (!response.ok) throw new Error('Failed to mark notification as read');
  return response.json();
}

// ── Webhooks ────────────────────────────────────────────────

export async function getWebhooks(workspaceId: string) {
  const response = await apiFetch(`/workspaces/${workspaceId}/webhooks`);
  if (!response.ok) throw new Error('Failed to fetch webhooks');
  return response.json();
}

export async function createWebhook(workspaceId: string, url: string) {
  const response = await apiFetch(`/workspaces/${workspaceId}/webhooks`, {
    method: 'POST',
    body: JSON.stringify({ url })
  });
  if (!response.ok) throw new Error('Failed to create webhook');
  return response.json();
}

export async function deleteWebhook(workspaceId: string, webhookId: number) {
  const response = await apiFetch(`/workspaces/${workspaceId}/webhooks/${webhookId}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error('Failed to delete webhook');
  }
  return response.json();
}

/**
 * Lists API keys for the authenticated user.
 */
export async function getApiKeys() {
  const response = await apiFetch('/auth/api-keys');
  if (!response.ok) {
    throw new Error('Failed to list API keys');
  }
  return response.json();
}

/**
 * Creates a new API key.
 */
export async function createApiKey(name: string) {
  const response = await apiFetch('/auth/api-keys', {
    method: 'POST',
    body: JSON.stringify({ name }),
  });
  if (!response.ok) {
    throw new Error('Failed to create API key');
  }
  return response.json();
}

/**
 * Revokes an API key.
 */
export async function revokeApiKey(keyId: number) {
  const response = await apiFetch(`/auth/api-keys/${keyId}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error('Failed to revoke API key');
  }
  return response.json();
}
