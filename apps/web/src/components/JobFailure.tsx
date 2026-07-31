'use client';

import { motion } from 'framer-motion';
import { XCircle, RefreshCw, MessageSquare } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { CopyButton } from './ui/CopyButton';
import styles from './JobFailure.module.css';

interface JobFailureProps {
  jobId: string;
  reason: string;
  logs: string[];
}

export function JobFailure({ jobId, reason, logs }: JobFailureProps) {
  const router = useRouter();

  const handleRetry = () => {
    // Navigate back to home to submit again for MVP
    router.push('/');
  };

  const logsText = logs.join('\n');

  return (
    <motion.div
      className={styles.container}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: 'easeOut' }}
    >
      <div className={styles.header}>
        <XCircle className={styles.errorIcon} size={48} />
        <h2 className={styles.title}>Pipeline Failed</h2>
        <p className={styles.subtitle}>Job #{jobId} terminated unexpectedly.</p>
      </div>

      <div className={styles.reasonCard}>
        <h3 className={styles.reasonTitle}>Failure Reason</h3>
        <p className={styles.reasonText}>{reason}</p>
      </div>

      <div className={styles.logsPanel}>
        <div className={styles.logsHeaderRow}>
          <h3 className={styles.logsTitle}>Last known logs:</h3>
          <CopyButton textToCopy={logsText} label="Copy Logs" />
        </div>
        <div className={styles.terminal}>
          {logs.length > 0 ? logs.map((log, i) => (
            <div key={i} className={styles.logLine}>&gt; {log}</div>
          )) : (
            <div className={styles.logLine}>No logs available.</div>
          )}
        </div>
      </div>

      <div className={styles.actionBar}>
        <button className={styles.primaryBtn} onClick={handleRetry}>
          <RefreshCw size={20} />
          Submit New Job
        </button>
        <button className={styles.secondaryBtn} onClick={() => alert('Support coming soon')}>
          <MessageSquare size={20} />
          Contact Support
        </button>
      </div>
    </motion.div>
  );
}
