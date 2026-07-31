'use client';

import { useState, FormEvent, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { createJob, getToken } from '@/lib/api';
import styles from './dashboard.module.css';

import { TopBar } from '@/components/layout/TopBar';

export default function DashboardPage() {
  const router = useRouter();
  const [url, setUrl] = useState('');
  const [isValid, setIsValid] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Protect route
  useEffect(() => {
    if (!getToken()) {
      router.replace('/login');
    }
  }, [router]);

  // ArXiv URL validation
  const validateArxiv = (val: string) => {
    const arxivRegex = /(?:arxiv\.org\/(?:abs|pdf)\/|arxiv:)(\d{4}\.\d{4,5}(?:v\d+)?)/i;
    return arxivRegex.test(val);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setUrl(val);
    setError(null);
    setIsValid(validateArxiv(val));
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!isValid || isSubmitting) return;

    setIsSubmitting(true);
    setError(null);

    try {
      const job = await createJob(url);
      router.push(`/jobs/${job.id}`);
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to submit job.';
      setError(errorMessage);
      setIsSubmitting(false);
    }
  };

  return (
    <div className={styles.container}>
      <TopBar title="PaperToProd" />
      <motion.div
        className={styles.hero}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
      >
        <h1 className={styles.title}>What would you like to build?</h1>
        <p className={styles.subtitle}>Paste an arXiv paper URL to generate a full repository.</p>

        <form className={styles.form} onSubmit={handleSubmit}>
          <div className={`${styles.inputWrapper} ${isValid ? styles.valid : ''} ${error ? styles.error : ''}`}>
            <input
              type="text"
              className={styles.input}
              placeholder="https://arxiv.org/abs/..."
              value={url}
              onChange={handleInputChange}
              disabled={isSubmitting}
              autoFocus
            />

            <AnimatePresence>
              {isValid && (
                <motion.svg
                  initial={{ opacity: 0, scale: 0.5, rotate: -90 }}
                  animate={{ opacity: 1, scale: 1, rotate: 0 }}
                  exit={{ opacity: 0, scale: 0.5 }}
                  className={styles.checkIcon}
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="3"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <polyline points="20 6 9 17 4 12"></polyline>
                </motion.svg>
              )}
            </AnimatePresence>

            <button
              type="submit"
              className={styles.submitBtn}
              disabled={!isValid || isSubmitting}
            >
              {isSubmitting ? <span className={styles.spinner}></span> : 'Run Pipeline'}
            </button>
          </div>

          <AnimatePresence>
            {error && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className={styles.errorMessage}
              >
                {error}
              </motion.div>
            )}
          </AnimatePresence>
        </form>

        <div style={{ marginTop: '3rem' }}>
          <button className={styles.historyBtn} onClick={() => router.push('/history')}>
            View Job History &rarr;
          </button>
        </div>
      </motion.div>
    </div>
  );
}
