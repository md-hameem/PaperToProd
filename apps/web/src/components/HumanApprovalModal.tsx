'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Github, Star, Clock, FileCode, CheckCircle, SearchCode } from 'lucide-react';
import styles from './HumanApprovalModal.module.css';

interface CandidateRepo {
  url: string;
  stars: number;
  last_commit: string;
  similarity_score: number;
  license: string | null;
}

interface HumanApprovalModalProps {
  candidates: CandidateRepo[];
  onApprove: (url: string) => void;
}

export function HumanApprovalModal({ candidates, onApprove }: HumanApprovalModalProps) {
  const [selectedIdx, setSelectedIdx] = useState<number>(0);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleConfirm = () => {
    setIsSubmitting(true);
    if (selectedIdx >= 0 && selectedIdx < candidates.length) {
      onApprove(candidates[selectedIdx].url);
    } else {
      onApprove(''); // Indicates generate fresh
    }
  };

  return (
    <div className={styles.overlay}>
      <motion.div
        className={`glass ${styles.modal}`}
        initial={{ opacity: 0, scale: 0.95, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: 0.3, ease: 'easeOut' }}
      >
        <div className={styles.header}>
          <SearchCode className={styles.icon} size={32} />
          <h2 className={styles.title}>Candidate Repositories Found</h2>
          <p className={styles.subtitle}>
            The Finder Agent has located potential GitHub repositories matching your paper.
            Choose one to adapt, or generate a fresh scaffold from scratch.
          </p>
        </div>

        <div className={styles.list}>
          {candidates.map((repo, idx) => {
            const isSelected = selectedIdx === idx;
            return (
              <div
                key={repo.url}
                className={`${styles.card} ${isSelected ? styles.selectedCard : ''}`}
                onClick={() => setSelectedIdx(idx)}
              >
                <div className={styles.cardHeader}>
                  <div className={styles.repoName}>
                    <Github size={16} />
                    <span>{repo.url.replace('https://github.com/', '')}</span>
                  </div>
                  {isSelected && <CheckCircle size={18} className={styles.checkIcon} />}
                </div>
                <div className={styles.metaRow}>
                  <span className={styles.metaBadge}><Star size={12} /> {repo.stars}</span>
                  <span className={styles.metaBadge}><Clock size={12} /> {repo.last_commit.substring(0, 10) || 'N/A'}</span>
                  <span className={styles.metaBadge}><FileCode size={12} /> {(repo.similarity_score * 100).toFixed(0)}% Match</span>
                  {repo.license && <span className={styles.metaBadge}>{repo.license}</span>}
                </div>
              </div>
            );
          })}

          <div
            className={`${styles.card} ${styles.freshCard} ${selectedIdx === -1 ? styles.selectedCard : ''}`}
            onClick={() => setSelectedIdx(-1)}
          >
            <div className={styles.cardHeader}>
              <div className={styles.repoName}>
                <FileCode size={16} />
                <span>Generate Fresh Scaffold</span>
              </div>
              {selectedIdx === -1 && <CheckCircle size={18} className={styles.checkIcon} />}
            </div>
            <p className={styles.freshDesc}>Build architecture entirely from scratch using the Extractor's methodology.</p>
          </div>
        </div>

        <div className={styles.footer}>
          <button
            className={styles.confirmBtn}
            onClick={handleConfirm}
            disabled={isSubmitting}
          >
            {isSubmitting ? 'Resuming Pipeline...' : 'Confirm & Resume Pipeline'}
          </button>
        </div>
      </motion.div>
    </div>
  );
}
