"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { TopBar } from "@/components/layout/TopBar";
import { Sidebar } from "@/components/layout/Sidebar";
import { useWorkspace } from "@/contexts/WorkspaceContext";
import { getWorkspaceMembers, inviteWorkspaceMember, changeWorkspaceRole, removeWorkspaceMember, getWebhooks, createWebhook, deleteWebhook, getWorkspaceUsage, createCheckoutSession, getGitHubIntegration, installGitHub, disconnectGitHub, getApiKeys, createApiKey, revokeApiKey } from "@/lib/api";
import styles from "./workspace-settings.module.css";
import { Users, Shield, Plus, X, Settings as SettingsIcon, Link as LinkIcon, Trash, Key } from "lucide-react";

export default function WorkspaceSettingsPage() {
  const router = useRouter();
  const { activeWorkspace, isLoading: workspaceLoading } = useWorkspace();
  const [members, setMembers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState("member");
  const [inviteError, setInviteError] = useState<string | null>(null);

  useEffect(() => {
    if (!workspaceLoading && !activeWorkspace) {
      router.replace("/login");
    }
  }, [workspaceLoading, activeWorkspace, router]);

  useEffect(() => {
    if (activeWorkspace) {
      loadMembers();
    }
  }, [activeWorkspace]);

  const [activeTab, setActiveTab] = useState("members");
  const [usage, setUsage] = useState<any>(null);
  const [loadingUsage, setLoadingUsage] = useState(false);
  const [githubIntegration, setGithubIntegration] = useState<any>(null);
  const [loadingGithub, setLoadingGithub] = useState(false);
  const [webhooks, setWebhooks] = useState<any[]>([]);
  const [loadingWebhooks, setLoadingWebhooks] = useState(false);
  const [newWebhookUrl, setNewWebhookUrl] = useState("");
  const [apiKeys, setApiKeys] = useState<any[]>([]);
  const [loadingApiKeys, setLoadingApiKeys] = useState(false);
  const [newApiKeyName, setNewApiKeyName] = useState("");
  const [generatedKey, setGeneratedKey] = useState<{name: string, raw_key: string} | null>(null);

  useEffect(() => {
    if (activeWorkspace) {
      loadMembers();
      loadUsage();
      loadGithub();
      loadWebhooks();
      loadApiKeys();
    }
  }, [activeWorkspace]);

  const loadWebhooks = async () => {
    if (!activeWorkspace) return;
    setLoadingWebhooks(true);
    try {
      const data = await getWebhooks(activeWorkspace.id.toString());
      setWebhooks(data);
    } catch (err) {
      console.error("Failed to load webhooks", err);
    } finally {
      setLoadingWebhooks(false);
    }
  };

  const handleCreateWebhook = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeWorkspace || !newWebhookUrl) return;
    try {
      await createWebhook(activeWorkspace.id.toString(), newWebhookUrl);
      setNewWebhookUrl("");
      loadWebhooks();
    } catch (err: any) {
      alert(err.message || "Failed to create webhook");
    }
  };

  const handleDeleteWebhook = async (id: number) => {
    if (!activeWorkspace) return;
    if (!confirm("Are you sure you want to delete this webhook?")) return;
    try {
      await deleteWebhook(activeWorkspace.id.toString(), id);
      loadWebhooks();
    } catch (err: any) {
      alert(err.message || "Failed to delete webhook");
    }
  };

  const loadUsage = async () => {
    if (!activeWorkspace) return;
    setLoadingUsage(true);
    try {
      const data = await getWorkspaceUsage(activeWorkspace.id.toString());
      setUsage(data);
    } catch (err) {
      console.error("Failed to load usage", err);
    } finally {
      setLoadingUsage(false);
    }
  };

  const loadGithub = async () => {
    if (!activeWorkspace) return;
    setLoadingGithub(true);
    try {
      const data = await getGitHubIntegration(activeWorkspace.id.toString());
      setGithubIntegration(data);
    } catch (err) {
      console.error("Failed to load github integration", err);
    } finally {
      setLoadingGithub(false);
    }
  };

  const handleUpgrade = async () => {
    if (!activeWorkspace) return;
    try {
      const session = await createCheckoutSession(activeWorkspace.id.toString());
      alert("Redirecting to Stripe checkout... (Mocked)");

      await fetch(`http://localhost:8000/api/v1/workspaces/${activeWorkspace.id}/billing/webhook`, {
        method: 'POST'
      });
      alert("Payment successful! You are now on PRO tier.");
      window.location.reload();
    } catch (err: any) {
      alert(err.message || "Failed to create checkout session");
    }
  };

  const handleInstallGithub = async () => {
    if (!activeWorkspace) return;
    try {
      await installGitHub(activeWorkspace.id.toString());
      alert("GitHub App successfully connected! (Mocked)");
      loadGithub();
    } catch (err: any) {
      alert(err.message || "Failed to connect GitHub");
    }
  };

  const handleDisconnectGithub = async () => {
    if (!activeWorkspace) return;
    if (!confirm("Are you sure you want to disconnect GitHub?")) return;
    try {
      await disconnectGitHub(activeWorkspace.id.toString());
      loadGithub();
    } catch (err: any) {
      alert(err.message || "Failed to disconnect GitHub");
    }
  };

  const loadApiKeys = async () => {
    setLoadingApiKeys(true);
    try {
      const data = await getApiKeys();
      setApiKeys(data);
    } catch (err) {
      console.error("Failed to load API keys", err);
    } finally {
      setLoadingApiKeys(false);
    }
  };

  const handleCreateApiKey = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newApiKeyName) return;
    try {
      const data = await createApiKey(newApiKeyName);
      setGeneratedKey(data);
      setNewApiKeyName("");
      loadApiKeys();
    } catch (err: any) {
      alert(err.message || "Failed to create API key");
    }
  };

  const handleRevokeApiKey = async (keyId: number) => {
    if (!confirm("Are you sure you want to revoke this API key? This action cannot be undone.")) return;
    try {
      await revokeApiKey(keyId);
      loadApiKeys();
    } catch (err: any) {
      alert(err.message || "Failed to revoke API key");
    }
  };

  if (workspaceLoading || !activeWorkspace) {
    return <div className={styles.container}>Loading...</div>;
  }

  return (
    <div className={styles.layout}>
      <Sidebar activeItem="settings/workspace" onNavigate={(id) => router.push(`/${id === 'dashboard' ? '' : id}`)} />
      <div className={styles.main}>
        <TopBar title="Workspace Settings" />
        <div className={styles.content}>
          <div className={styles.header}>
            <div className={styles.headerIcon}><SettingsIcon size={32} /></div>
            <div>
              <h1 className={styles.title}>{activeWorkspace.name}</h1>
              <p className={styles.subtitle}>Manage members, roles, and workspace settings.</p>
            </div>
          </div>

          <div className={styles.tabs}>
            <button
              className={`${styles.tabBtn} ${activeTab === 'members' ? styles.activeTab : ''}`}
              onClick={() => setActiveTab('members')}
            >
              Members
            </button>
            <button
              className={`${styles.tabBtn} ${activeTab === 'billing' ? styles.activeTab : ''}`}
              onClick={() => setActiveTab('billing')}
            >
              Billing & Usage
            </button>
            <button
              className={`${styles.tabBtn} ${activeTab === 'integrations' ? styles.activeTab : ''}`}
              onClick={() => setActiveTab('integrations')}
            >
              Integrations
            </button>
            <button
              className={`${styles.tabBtn} ${activeTab === 'webhooks' ? styles.activeTab : ''}`}
              onClick={() => setActiveTab('webhooks')}
            >
              Webhooks
            </button>
            <button
              className={`${styles.tabBtn} ${activeTab === 'apikeys' ? styles.activeTab : ''}`}
              onClick={() => setActiveTab('apikeys')}
            >
              API Keys
            </button>
          </div>

          {activeTab === 'members' && (
            <>
              <div className={styles.card}>
                <div className={styles.cardHeader}>
                  <h2 className={styles.cardTitle}>Invite Member</h2>
                </div>
                <form className={styles.inviteForm} onSubmit={handleInvite}>
                  <input
                    type="email"
                    placeholder="Email address"
                    value={inviteEmail}
                    onChange={e => setInviteEmail(e.target.value)}
                    required
                    className={styles.input}
                  />
                  <select value={inviteRole} onChange={e => setInviteRole(e.target.value)} className={styles.select}>
                    <option value="owner">Owner</option>
                    <option value="admin">Admin</option>
                    <option value="member">Member</option>
                    <option value="billing">Billing</option>
                  </select>
                  <button type="submit" className={styles.btnPrimary}>
                    <Plus size={16} /> Invite
                  </button>
                </form>
                {inviteError && <p className={styles.errorText}>{inviteError}</p>}
              </div>

              <div className={styles.card}>
                <div className={styles.cardHeader}>
                  <h2 className={styles.cardTitle}>Members</h2>
                  <span className={styles.badge}>{members.length}</span>
                </div>
                {loading ? (
                  <p className={styles.loadingText}>Loading members...</p>
                ) : (
                  <div className={styles.tableWrapper}>
                    <table className={styles.table}>
                      <thead>
                        <tr>
                          <th>User</th>
                          <th>Role</th>
                          <th>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {members.map(member => (
                          <tr key={member.user_id}>
                            <td>
                              <div className={styles.userInfo}>
                                <div className={styles.avatar}>{member.display_name?.charAt(0) || "U"}</div>
                                <div>
                                  <div className={styles.userName}>{member.display_name}</div>
                                  <div className={styles.userEmail}>{member.email}</div>
                                </div>
                              </div>
                            </td>
                            <td>
                              <select
                                value={member.role}
                                onChange={(e) => handleChangeRole(member.user_id, e.target.value)}
                                className={styles.roleSelect}
                              >
                                <option value="owner">Owner</option>
                                <option value="admin">Admin</option>
                                <option value="member">Member</option>
                                <option value="billing">Billing</option>
                              </select>
                            </td>
                            <td>
                              <button
                                className={styles.btnDestructive}
                                onClick={() => handleRemove(member.user_id)}
                              >
                                <X size={16} /> Remove
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </>
          )}

          {activeTab === 'billing' && (
            <div className={styles.card}>
              <div className={styles.cardHeader}>
                <h2 className={styles.cardTitle}>Current Plan: {usage?.subscription_tier?.toUpperCase() || 'Loading...'}</h2>
              </div>

              {loadingUsage ? (
                <p className={styles.loadingText}>Loading usage data...</p>
              ) : (
                <div className={styles.usageContainer}>
                  <div className={styles.usageStats}>
                    <div className={styles.statBox}>
                      <span className={styles.statLabel}>Jobs Run This Month</span>
                      <span className={styles.statValue}>{usage?.usage?.total_jobs || 0} / {usage?.subscription_tier === 'free' ? '3' : '∞'}</span>
                    </div>
                    <div className={styles.statBox}>
                      <span className={styles.statLabel}>Total Cost Cents</span>
                      <span className={styles.statValue}>{(usage?.usage?.total_cost_cents || 0)}¢</span>
                    </div>
                  </div>

                  {usage?.subscription_tier === 'free' && (
                    <div className={styles.upgradePanel}>
                      <h3>Upgrade to Pro</h3>
                      <p>Get unlimited jobs, high-priority queuing, and faster models.</p>
                      <button onClick={handleUpgrade} className={styles.btnPrimary}>
                        Upgrade Now
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {activeTab === 'integrations' && (
            <div className={styles.card}>
              <div className={styles.cardHeader}>
                <h2 className={styles.cardTitle}>GitHub Integration</h2>
              </div>

              <div className={styles.integrationPanel}>
                <div className={styles.integrationInfo}>
                  <h3>Push to GitHub</h3>
                  <p>Automatically push generated repositories and artifacts to your GitHub account or organization.</p>
                </div>

                {loadingGithub ? (
                  <p className={styles.loadingText}>Loading status...</p>
                ) : githubIntegration?.installed ? (
                  <div className={styles.integrationActive}>
                    <p className={styles.successText}>✓ Connected to <strong>{githubIntegration.account_name}</strong></p>
                    <button onClick={handleDisconnectGithub} className={styles.btnDestructive}>
                      Disconnect
                    </button>
                  </div>
                ) : (
                  <button onClick={handleInstallGithub} className={styles.btnPrimary}>
                    Connect GitHub App
                  </button>
                )}
              </div>
            </div>
          )}

          {activeTab === 'webhooks' && (
            <div className={styles.card}>
              <div className={styles.cardHeader}>
                <h2 className={styles.cardTitle}>Programmatic Webhooks</h2>
              </div>
              <p style={{ color: "var(--color-text-secondary)", marginBottom: "20px" }}>
                Webhooks allow you to receive HTTP POST requests when events occur in your workspace, such as a Job completing.
              </p>

              <form className={styles.inviteForm} onSubmit={handleCreateWebhook} style={{ marginBottom: "20px" }}>
                <input
                  type="url"
                  placeholder="https://your-api.com/webhooks"
                  value={newWebhookUrl}
                  onChange={e => setNewWebhookUrl(e.target.value)}
                  required
                  className={styles.input}
                />
                <button type="submit" className={styles.btnPrimary}>
                  <Plus size={16} /> Add Webhook
                </button>
              </form>

              {loadingWebhooks ? (
                <p className={styles.loadingText}>Loading webhooks...</p>
              ) : webhooks.length === 0 ? (
                <p>No webhooks configured yet.</p>
              ) : (
                <div className={styles.tableWrapper}>
                  <table className={styles.table}>
                    <thead>
                      <tr>
                        <th>URL</th>
                        <th>Secret</th>
                        <th>Created</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {webhooks.map(wh => (
                        <tr key={wh.id}>
                          <td>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                              <LinkIcon size={14} color="var(--color-text-tertiary)" />
                              {wh.url}
                            </div>
                          </td>
                          <td><span className={styles.badge}>whsec_••••••••</span></td>
                          <td>{new Date(wh.created_at).toLocaleDateString()}</td>
                          <td>
                            <button
                              className={styles.btnDestructive}
                              onClick={() => handleDeleteWebhook(wh.id)}
                            >
                              <Trash size={16} /> Remove
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {activeTab === 'apikeys' && (
            <>
              {generatedKey && (
                <div className={styles.card} style={{ borderColor: 'var(--color-success)', background: 'var(--color-bg-primary)' }}>
                  <div className={styles.cardHeader}>
                    <h2 className={styles.cardTitle}>Save Your API Key</h2>
                  </div>
                  <p className={styles.subtitle} style={{ marginBottom: '16px', color: 'var(--color-warning)' }}>
                    Please copy this API key now. You will not be able to see it again!
                  </p>
                  <div className={styles.input} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontFamily: 'monospace', fontSize: '1.2em' }}>
                    <span>{generatedKey.raw_key}</span>
                    <button
                      className={styles.btnPrimary}
                      onClick={() => {
                        navigator.clipboard.writeText(generatedKey.raw_key);
                        alert('Copied to clipboard!');
                      }}
                    >
                      Copy
                    </button>
                  </div>
                  <button className={styles.btnSecondary} onClick={() => setGeneratedKey(null)} style={{ marginTop: '16px' }}>
                    I have saved it
                  </button>
                </div>
              )}

              <div className={styles.card}>
                <div className={styles.cardHeader}>
                  <h2 className={styles.cardTitle}>Create API Key</h2>
                </div>
                <form className={styles.inviteForm} onSubmit={handleCreateApiKey}>
                  <input
                    type="text"
                    placeholder="Key Name (e.g. CI/CD Script)"
                    value={newApiKeyName}
                    onChange={e => setNewApiKeyName(e.target.value)}
                    required
                    className={styles.input}
                  />
                  <button type="submit" className={styles.btnPrimary}>
                    <Plus size={16} /> Create
                  </button>
                </form>
              </div>

              <div className={styles.card}>
                <div className={styles.cardHeader}>
                  <h2 className={styles.cardTitle}>Active API Keys</h2>
                  <span className={styles.badge}>{apiKeys.length}</span>
                </div>
                {loadingApiKeys ? (
                  <p className={styles.loadingText}>Loading API keys...</p>
                ) : (
                  <div className={styles.tableWrapper}>
                    <table className={styles.table}>
                      <thead>
                        <tr>
                          <th>Name</th>
                          <th>Prefix</th>
                          <th>Created</th>
                          <th>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {apiKeys.length === 0 ? (
                          <tr>
                            <td colSpan={4} style={{ textAlign: 'center', color: 'var(--color-text-secondary)', padding: '24px' }}>
                              No API keys active.
                            </td>
                          </tr>
                        ) : (
                          apiKeys.map((key: any) => (
                            <tr key={key.id}>
                              <td><div className={styles.userName}>{key.name}</div></td>
                              <td><code style={{ background: 'var(--color-bg-tertiary)', padding: '4px 8px', borderRadius: '4px' }}>{key.prefix}...</code></td>
                              <td>{new Date(key.created_at).toLocaleDateString()}</td>
                              <td>
                                <button
                                  className={styles.btnDestructive}
                                  onClick={() => handleRevokeApiKey(key.id)}
                                >
                                  <Trash size={16} /> Revoke
                                </button>
                              </td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </>
          )}

        </div>
      </div>
    </div>
  );
}
