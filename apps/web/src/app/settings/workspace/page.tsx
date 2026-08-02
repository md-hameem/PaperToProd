"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { TopBar } from "@/components/layout/TopBar";
import { Sidebar } from "@/components/layout/Sidebar";
import { useWorkspace } from "@/contexts/WorkspaceContext";
import { getWorkspaceMembers, inviteWorkspaceMember, changeWorkspaceRole, removeWorkspaceMember } from "@/lib/api";
import styles from "./workspace-settings.module.css";
import { Users, Shield, Plus, X, Settings as SettingsIcon } from "lucide-react";

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

import { getWorkspaceUsage, createCheckoutSession, getGitHubIntegration, installGitHub, disconnectGitHub } from "@/lib/api";

// ... existing code ...
  const [activeTab, setActiveTab] = useState("members");
  const [usage, setUsage] = useState<any>(null);
  const [loadingUsage, setLoadingUsage] = useState(false);
  const [githubIntegration, setGithubIntegration] = useState<any>(null);
  const [loadingGithub, setLoadingGithub] = useState(false);

  useEffect(() => {
    if (activeWorkspace) {
      loadMembers();
      loadUsage();
      loadGithub();
    }
  }, [activeWorkspace]);

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
        </div>
      </div>
    </div>
  );
}
