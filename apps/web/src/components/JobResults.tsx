import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Download, Code2, CheckCircle, AlertTriangle, FileText, X } from 'lucide-react';
import { FidelityRing } from './ui/FidelityRing';
import styles from './JobResults.module.css';
import Link from 'next/link';
import { useWorkspace } from '@/contexts/WorkspaceContext';
import { pushJobToGitHub } from '@/lib/api';

interface JobResultsProps {
  jobId: string;
  score: number;
  stats: {
    loc: number;
    files: number;
    tests: number;
  };
  gaps: string[];
  advancedOptions?: Record<string, any> | null;
}

export function JobResults({ jobId, score, stats, gaps, advancedOptions }: JobResultsProps) {
  const { activeWorkspace } = useWorkspace();
  const [showGithubModal, setShowGithubModal] = useState(false);
  const [repoName, setRepoName] = useState(`papertoprod-${jobId}`);
  const [isPushing, setIsPushing] = useState(false);

  const handleDownload = () => {
    alert(`Downloading repository archive for Job #${jobId}...`);
  };

  const handlePushToGithub = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeWorkspace) return;

    setIsPushing(true);
    try {
      const result = await pushJobToGitHub(activeWorkspace.id.toString(), jobId, repoName);
      alert(`Success: ${result.message}\nRepository: ${result.repository_url}`);
      setShowGithubModal(false);
    } catch (err: any) {
      alert(`Failed to push to GitHub: ${err.message}`);
    } finally {
      setIsPushing(false);
    }
  };

  return (
    <>
      <motion.div
        className={styles.container}
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.6, type: "spring", bounce: 0.4 }}
      >
        <div className={styles.header}>
          <CheckCircle className={styles.successIcon} size={48} />
          <h2 className={styles.title}>Pipeline Complete</h2>
          <p className={styles.subtitle}>Your codebase has been successfully generated and validated.</p>
          {advancedOptions && (
            <div className={styles.advancedOptionsPill}>
              {advancedOptions.framework_override && (
                <span className={styles.optionBadge}>
                  Framework: {advancedOptions.framework_override}
                </span>
              )}
              {advancedOptions.focus_scope && (
                <span className={styles.optionBadge}>
                  Scope: {advancedOptions.focus_scope}
                </span>
              )}
              {advancedOptions.github_auto_push === 'true' && (
                <span className={styles.optionBadge}>Auto-Push: Enabled</span>
              )}
            </div>
          )}
        </div>

        <div className={styles.grid}>
          {/* Fidelity Score Card */}
          <div className={`glass ${styles.card}`}>
            <h3 className={styles.cardTitle}>Fidelity Score</h3>
            <div className={styles.cardContentCentered}>
              <FidelityRing score={score} />
              <p className={styles.cardDesc}>
                Measures adherence to the paper&apos;s original architecture and math.
              </p>
            </div>
            <Link href={`/jobs/${jobId}/fidelity`} className={styles.fidelityLinkBtn}>
              <FileText size={16} />
              View Full Fidelity Report
            </Link>
          </div>

          {/* Repository Stats Card */}
          <div className={`glass ${styles.card}`}>
            <h3 className={styles.cardTitle}>Repository Summary</h3>
            <div className={styles.statsGrid}>
              <div className={styles.statItem}>
                <Code2 size={20} className={styles.statIcon} />
                <div className={styles.statInfo}>
                  <span className={styles.statValue}>{stats.files}</span>
                  <span className={styles.statLabel}>Generated Files</span>
                </div>
              </div>
              <div className={styles.statItem}>
                <div className={styles.statIconPlaceholder}>{"{ }"}</div>
                <div className={styles.statInfo}>
                  <span className={styles.statValue}>{stats.loc}</span>
                  <span className={styles.statLabel}>Lines of Code</span>
                </div>
              </div>
              <div className={styles.statItem}>
                <CheckCircle size={20} className={styles.statIconSuccess} />
                <div className={styles.statInfo}>
                  <span className={styles.statValue}>{stats.tests}</span>
                  <span className={styles.statLabel}>Passing Tests</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Assumptions / Gaps Panel */}
        {gaps.length > 0 && (
          <div className={styles.gapsPanel}>
            <div className={styles.gapsHeader}>
              <AlertTriangle size={20} className={styles.warningIcon} />
              <h3 className={styles.gapsTitle}>Flagged Assumptions</h3>
            </div>
            <ul className={styles.gapsList}>
              {gaps.map((gap, i) => (
                <li key={i}>{gap}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Action Bar */}
        <div className={styles.actionBar}>
          <button className={styles.primaryBtn} onClick={handleDownload}>
            <Download size={20} />
            Download Repository (.zip)
          </button>

          <Link href={`/jobs/${jobId}/explorer`} className={styles.secondaryBtn}>
            <Code2 size={20} />
            Open Explorer
          </Link>

          <button className={styles.secondaryBtn} onClick={() => setShowGithubModal(true)}>
            <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.865 8.166 6.839 9.489.5.092.682-.217.682-.482 0-.237-.008-.866-.013-1.7-2.782.603-3.369-1.34-3.369-1.34-.454-1.156-1.11-1.462-1.11-1.462-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.087 2.91.831.092-.646.35-1.086.636-1.336-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.578 9.578 0 0112 6.836c.85.004 1.705.114 2.504.336 1.909-1.294 2.747-1.025 2.747-1.025.546 1.379.203 2.394.1 2.647.64.699 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.935.359.309.678.919.678 1.852 0 1.336-.012 2.415-.012 2.743 0 .267.18.578.688.48C19.138 20.161 22 16.418 22 12c0-5.523-4.477-10-10-10z"/>
            </svg>
            Push to GitHub
          </button>
        </div>
      </motion.div>

      <AnimatePresence>
        {showGithubModal && (
          <div className={styles.modalOverlay}>
            <motion.div
              className={styles.modalContent}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 20 }}
            >
              <button className={styles.modalClose} onClick={() => setShowGithubModal(false)}>
                <X size={20} />
              </button>
              <h2>Push to GitHub</h2>
              <p>Specify a repository name for your artifact.</p>

              <form onSubmit={handlePushToGithub} className={styles.githubForm}>
                <div className={styles.formGroup}>
                  <label>Repository Name</label>
                  <input
                    type="text"
                    value={repoName}
                    onChange={e => setRepoName(e.target.value)}
                    required
                    placeholder="papertoprod-artifact"
                  />
                </div>

                <button type="submit" className={styles.primaryBtn} disabled={isPushing}>
                  {isPushing ? 'Pushing...' : 'Push Repository'}
                </button>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </>
  );
}
