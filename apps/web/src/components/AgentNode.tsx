'use client';

import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, Circle, Loader2, AlertCircle, TerminalSquare } from 'lucide-react';
import styles from './AgentNode.module.css';

export type AgentStatus = 'pending' | 'started' | 'completed' | 'error' | 'pending_approval';

interface AgentNodeProps {
  name: string;
  label: string;
  status: AgentStatus;
  logs: string[];
  isActive?: boolean;
}

export function AgentNode({ label, status, logs, isActive }: AgentNodeProps) {
  const [showLogs, setShowLogs] = useState(false);
  const logsEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll logs
  useEffect(() => {
    if (showLogs && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, showLogs]);

  // Expand logs automatically if error or if actively generating lots of logs
  useEffect(() => {
    if (status === 'error' || (status === 'started' && logs.length > 0)) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setShowLogs(true);
    }
  }, [status, logs.length]);

  const getStatusIcon = () => {
    switch (status) {
      case 'completed': return <CheckCircle2 className={styles.iconSuccess} size={24} />;
      case 'error': return <AlertCircle className={styles.iconError} size={24} />;
      case 'started': return <Loader2 className={`${styles.iconActive} ${styles.spin}`} size={24} />;
      default: return <Circle className={styles.iconPending} size={24} />;
    }
  };

  return (
    <div className={`${styles.nodeContainer} ${isActive ? styles.activeContainer : ''}`}>

      {/* Hidden ARIA region for screen readers */}
      <div className="sr-only" aria-live="polite" aria-atomic="true">
        {label} is {status}
      </div>

      {/* Node Header */}
      <div className={styles.header} onClick={() => setShowLogs(!showLogs)}>
        <div className={styles.statusIndicator}>
          {getStatusIcon()}
          {isActive && (
            <motion.div
              className={styles.pulse}
              animate={{ scale: [1, 1.5, 1], opacity: [0.5, 0, 0.5] }}
              transition={{ duration: 2, repeat: Infinity }}
            />
          )}
        </div>

        <div className={styles.meta}>
          <h3 className={styles.label}>{label}</h3>
          <p className={styles.statusText}>{status.charAt(0).toUpperCase() + status.slice(1)}</p>
        </div>

        <button className={styles.toggleBtn} aria-label="Toggle Logs">
          <TerminalSquare size={20} />
          <span className={styles.logCount}>{logs.length}</span>
        </button>
      </div>

      {/* Expandable Log Terminal */}
      <AnimatePresence>
        {showLogs && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className={styles.logWrapper}
          >
            <div className={styles.terminal}>
              {logs.length === 0 ? (
                <div className={styles.emptyLog}>Waiting for agent output...</div>
              ) : (
                logs.map((log, i) => (
                  <div key={i} className={styles.logLine}>
                    <span className={styles.logPrefix}>&gt;</span> {log}
                  </div>
                ))
              )}
              <div ref={logsEndRef} />
            </div>
          </motion.div>
        )}
      </AnimatePresence>

    </div>
  );
}
