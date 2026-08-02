"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { TopBar } from "@/components/layout/TopBar";
import { Sidebar } from "@/components/layout/Sidebar";
import { getProfile, updateProfile, getApiKeys, createApiKey, revokeApiKey } from "@/lib/api";
import styles from "./profile-settings.module.css";
import { User, Key, Plus, X, Settings as SettingsIcon, Copy, Check } from "lucide-react";

export default function ProfileSettingsPage() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState("profile");

  // Profile State
  const [profile, setProfile] = useState<any>(null);
  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [savingProfile, setSavingProfile] = useState(false);
  const [profileMessage, setProfileMessage] = useState("");

  // API Keys State
  const [apiKeys, setApiKeys] = useState<any[]>([]);
  const [loadingKeys, setLoadingKeys] = useState(false);
  const [showKeyModal, setShowKeyModal] = useState(false);
  const [newKeyName, setNewKeyName] = useState("");
  const [generatedKey, setGeneratedKey] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    loadProfile();
    loadApiKeys();
  }, []);

  const loadProfile = async () => {
    try {
      const data = await getProfile();
      setProfile(data);
      setDisplayName(data.display_name || "");
      setEmail(data.email || "");
    } catch (err) {
      console.error("Failed to load profile", err);
      // Maybe not logged in
      router.replace("/login");
    }
  };

  const loadApiKeys = async () => {
    setLoadingKeys(true);
    try {
      const data = await getApiKeys();
      setApiKeys(data);
    } catch (err) {
      console.error("Failed to load API keys", err);
    } finally {
      setLoadingKeys(false);
    }
  };

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingProfile(true);
    try {
      const data = await updateProfile({ display_name: displayName, email });
      setProfile(data);
      setProfileMessage("Profile updated successfully!");
      setTimeout(() => setProfileMessage(""), 3000);
    } catch (err: any) {
      alert(err.message || "Failed to update profile");
    } finally {
      setSavingProfile(false);
    }
  };

  const handleCreateApiKey = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const data = await createApiKey(newKeyName);
      setGeneratedKey(data.key);
      setNewKeyName("");
      loadApiKeys(); // Refresh list
    } catch (err: any) {
      alert(err.message || "Failed to create API key");
    }
  };

  const handleRevokeApiKey = async (id: number) => {
    if (!confirm("Are you sure you want to revoke this API key? This action cannot be undone.")) return;
    try {
      await revokeApiKey(id);
      loadApiKeys();
    } catch (err: any) {
      alert(err.message || "Failed to revoke API key");
    }
  };

  const copyToClipboard = () => {
    if (generatedKey) {
      navigator.clipboard.writeText(generatedKey);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (!profile) {
    return <div className={styles.layout}>Loading...</div>;
  }

  return (
    <div className={styles.layout}>
      <Sidebar activeItem="settings/profile" onNavigate={(id) => router.push(`/${id === 'dashboard' ? '' : id}`)} />
      <div className={styles.main}>
        <TopBar title="Personal Settings" />
        <div className={styles.content}>
          <div className={styles.header}>
            <div className={styles.headerIcon}><User size={32} /></div>
            <div>
              <h1 className={styles.title}>Personal Settings</h1>
              <p className={styles.subtitle}>Manage your profile, preferences, and developer API keys.</p>
            </div>
          </div>

          <div className={styles.tabs}>
            <button
              className={`${styles.tabBtn} ${activeTab === 'profile' ? styles.activeTab : ''}`}
              onClick={() => setActiveTab('profile')}
            >
              Profile
            </button>
            <button
              className={`${styles.tabBtn} ${activeTab === 'api-keys' ? styles.activeTab : ''}`}
              onClick={() => setActiveTab('api-keys')}
            >
              Developer API Keys
            </button>
          </div>

          {activeTab === 'profile' && (
            <div className={styles.card}>
              <div className={styles.cardHeader}>
                <h2 className={styles.cardTitle}>Profile Information</h2>
              </div>
              <form onSubmit={handleUpdateProfile}>
                <div className={styles.formGroup}>
                  <label>Display Name</label>
                  <input
                    type="text"
                    className={styles.input}
                    value={displayName}
                    onChange={(e) => setDisplayName(e.target.value)}
                    required
                  />
                </div>
                <div className={styles.formGroup}>
                  <label>Email Address</label>
                  <input
                    type="email"
                    className={styles.input}
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    disabled={true} // Usually disabled for OAuth
                  />
                </div>

                <button type="submit" className={styles.btnPrimary} disabled={savingProfile}>
                  {savingProfile ? "Saving..." : "Save Changes"}
                </button>
                {profileMessage && <p style={{ color: "var(--color-status-success)", marginTop: "10px" }}>{profileMessage}</p>}
              </form>
            </div>
          )}

          {activeTab === 'api-keys' && (
            <div className={styles.card}>
              <div className={styles.cardHeader}>
                <h2 className={styles.cardTitle}>API Keys</h2>
                <button className={styles.btnPrimary} onClick={() => { setShowKeyModal(true); setGeneratedKey(null); }}>
                  <Plus size={16} /> Generate New Key
                </button>
              </div>
              <p style={{ color: "var(--color-text-secondary)", marginBottom: "20px" }}>
                API keys allow you to programmatically access the PaperToProd API. Do not share your API keys in publicly accessible areas such as GitHub, client-side code, etc.
              </p>

              {loadingKeys ? (
                <p>Loading...</p>
              ) : apiKeys.length === 0 ? (
                <p>You haven't generated any API keys yet.</p>
              ) : (
                <div className={styles.tableWrapper}>
                  <table className={styles.table}>
                    <thead>
                      <tr>
                        <th>Name</th>
                        <th>Prefix</th>
                        <th>Created</th>
                        <th>Last Used</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {apiKeys.map(key => (
                        <tr key={key.id}>
                          <td>{key.name}</td>
                          <td><span className={styles.badge}>{key.prefix}••••••••</span></td>
                          <td>{new Date(key.created_at).toLocaleDateString()}</td>
                          <td>{key.last_used_at ? new Date(key.last_used_at).toLocaleDateString() : "Never"}</td>
                          <td>
                            <button
                              className={styles.btnDestructive}
                              onClick={() => handleRevokeApiKey(key.id)}
                            >
                              <X size={16} /> Revoke
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
        </div>
      </div>

      {showKeyModal && (
        <div className={styles.modalOverlay}>
          <div className={styles.modalContent}>
            <button className={styles.modalClose} onClick={() => setShowKeyModal(false)}>
              <X size={20} />
            </button>

            {!generatedKey ? (
              <>
                <h2>Generate API Key</h2>
                <p>Give this API key a name to help you identify it later.</p>
                <form onSubmit={handleCreateApiKey} className={styles.formGroup}>
                  <label>Key Name</label>
                  <input
                    type="text"
                    className={styles.input}
                    value={newKeyName}
                    onChange={(e) => setNewKeyName(e.target.value)}
                    placeholder="e.g., CI/CD Pipeline"
                    required
                  />
                  <button type="submit" className={styles.btnPrimary} style={{ marginTop: "16px" }}>
                    Generate Key
                  </button>
                </form>
              </>
            ) : (
              <>
                <h2>Save your API Key</h2>
                <div className={styles.warningBox}>
                  Please copy this API key and save it somewhere safe. For security reasons, <strong>we cannot show it to you again</strong>.
                </div>

                <div className={styles.apiKeyDisplay}>
                  <code>{generatedKey}</code>
                  <button
                    onClick={copyToClipboard}
                    style={{ background: 'none', border: 'none', color: 'var(--color-accent)', cursor: 'pointer' }}
                  >
                    {copied ? <Check size={20} /> : <Copy size={20} />}
                  </button>
                </div>

                <button className={styles.btnPrimary} onClick={() => setShowKeyModal(false)} style={{ width: '100%', justifyContent: 'center' }}>
                  I have saved my key
                </button>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
