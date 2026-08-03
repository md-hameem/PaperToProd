'use client';

import { useState, FormEvent, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { createJob, getToken } from '@/lib/api';
import { useWorkspace } from '@/contexts/WorkspaceContext';
import styles from './dashboard.module.css';

import { TopBar } from '@/components/layout/TopBar';
import { UploadCloud, FileText, ChevronDown, ChevronUp, X } from 'lucide-react';

const MAX_FILE_SIZE = 25 * 1024 * 1024; // 25MB

export default function DashboardPage() {
  const router = useRouter();
  const [url, setUrl] = useState('');
  const [file, setFile] = useState<File | null>(null);

  // Advanced options
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [focusScope, setFocusScope] = useState('');
  const [frameworkOverride, setFrameworkOverride] = useState('');
  const [autoPushGithub, setAutoPushGithub] = useState(false);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Protect route
  useEffect(() => {
    if (!getToken()) {
      router.replace('/login');
    }
  }, [router]);

  // ArXiv URL validation
  const validateArxiv = (val: string) => {
    const arxivRegex = /(?:arxiv\.org\/(?:abs|pdf)\/|arxiv:)(\d{4}\.\d{4,5}(?:v\d+)?)/i;
    const arxivIdRegex = /^(\d{4}\.\d{4,5}(?:v\d+)?)$/i;
    return arxivRegex.test(val) || arxivIdRegex.test(val);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setUrl(val);
    setError(null);
  };

  const validateFile = (selectedFile: File) => {
    if (selectedFile.type !== 'application/pdf') {
      setError('Only PDF files are supported.');
      return false;
    }
    if (selectedFile.size > MAX_FILE_SIZE) {
      setError('File size exceeds the 25MB limit.');
      return false;
    }
    setError(null);
    return true;
  };

  const handleFileDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const droppedFile = e.dataTransfer.files[0];
      if (validateFile(droppedFile)) {
        setFile(droppedFile);
        setUrl(''); // clear url if file is uploaded
      }
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const selectedFile = e.target.files[0];
      if (validateFile(selectedFile)) {
        setFile(selectedFile);
        setUrl('');
      }
    }
  };

  const clearFile = () => {
    setFile(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const isValid = () => {
    if (file) return true;
    if (url && validateArxiv(url)) return true;
    return false;
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!isValid() || isSubmitting) return;

    setIsSubmitting(true);
    setError(null);

    try {
      const formData = new FormData();
      if (file) {
        formData.append('file', file);
      } else if (url) {
        formData.append('arxiv_url', url);
      }

      if (focusScope) formData.append('focus_scope', focusScope);
      if (frameworkOverride) formData.append('framework_override', frameworkOverride);
      if (autoPushGithub) formData.append('github_auto_push', 'true');

      const job = await createJob(formData);
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
        <p className={styles.subtitle}>Paste an arXiv paper URL or ID, or upload a PDF to generate a full repository.</p>

        <form className={styles.form} onSubmit={handleSubmit}>

          {/* Drag & Drop Zone */}
          {!file && (
            <div
              className={`${styles.dropzone} ${isDragging ? styles.dragging : ''}`}
              onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={handleFileDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              <UploadCloud size={32} className={styles.dropIcon} />
              <p>Drag & drop a PDF here, or click to browse</p>
              <span className={styles.dropLimit}>Max 25MB. Text-extractable PDFs only.</span>
              <input
                type="file"
                ref={fileInputRef}
                className={styles.hiddenInput}
                accept="application/pdf"
                onChange={handleFileChange}
              />
            </div>
          )}

          {/* File Selected View */}
          {file && (
            <div className={styles.fileSelected}>
              <div className={styles.fileInfo}>
                <FileText size={24} className={styles.fileIcon} />
                <div>
                  <div className={styles.fileName}>{file.name}</div>
                  <div className={styles.fileSize}>{(file.size / 1024 / 1024).toFixed(2)} MB</div>
                </div>
              </div>
              <button type="button" onClick={clearFile} className={styles.clearFileBtn}>
                <X size={16} />
              </button>
            </div>
          )}

          <div className={styles.orDivider}>OR</div>

          {/* URL Input */}
          <div className={`${styles.inputWrapper} ${(isValid() && !file) ? styles.valid : ''} ${error && !file ? styles.error : ''}`}>
            <input
              type="text"
              className={styles.input}
              placeholder="https://arxiv.org/abs/2301.12345 or 2301.12345"
              value={url}
              onChange={handleInputChange}
              disabled={isSubmitting || file !== null}
            />

            <AnimatePresence>
              {isValid() && !file && (
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
          </div>

          {/* Advanced Options Toggle */}
          <div className={styles.advancedToggle} onClick={() => setShowAdvanced(!showAdvanced)}>
            <span>Advanced Options</span>
            {showAdvanced ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </div>

          <AnimatePresence>
            {showAdvanced && (
              <motion.div
                className={styles.advancedPanel}
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
              >
                <div className={styles.advancedField}>
                  <label>Focus Scope</label>
                  <textarea
                    placeholder="E.g., Implement only the Vision Transformer backbone, ignore the decoder."
                    value={focusScope}
                    onChange={e => setFocusScope(e.target.value)}
                    disabled={isSubmitting}
                  />
                </div>
                <div className={styles.advancedField}>
                  <label>Framework Override</label>
                  <select
                    value={frameworkOverride}
                    onChange={e => setFrameworkOverride(e.target.value)}
                    disabled={isSubmitting}
                  >
                    <option value="">Auto-detect from paper</option>
                    <option value="PyTorch">PyTorch</option>
                    <option value="TensorFlow">TensorFlow</option>
                    <option value="JAX">JAX</option>
                  </select>
                </div>
                <div className={styles.advancedFieldCheckbox}>
                  <label>
                    <input
                      type="checkbox"
                      disabled={isSubmitting}
                      checked={autoPushGithub}
                      onChange={e => setAutoPushGithub(e.target.checked)}
                    />
                    Automatically push to GitHub upon completion (Requires Integration)
                  </label>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          <button
            type="submit"
            className={styles.submitBtn}
            disabled={!isValid() || isSubmitting}
          >
            {isSubmitting ? <span className={styles.spinner}></span> : 'Run Pipeline'}
          </button>

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

        <UsageWidget />
      </motion.div>
    </div>
  );
}

function UsageWidget() {
  const { activeWorkspace } = useWorkspace();
  const [usage, setUsage] = useState<any>(null);

  useEffect(() => {
    if (activeWorkspace) {
      import('@/lib/api').then(({ getWorkspaceUsage }) => {
        getWorkspaceUsage(activeWorkspace.id.toString())
          .then(setUsage)
          .catch(() => {});
      });
    }
  }, [activeWorkspace]);

  if (!usage || usage.subscription_tier !== 'free') return null;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className={styles.usageWidget}
    >
      <div className={styles.usageWidgetText}>
        Free Tier: {usage.usage?.total_jobs || 0}/3 Jobs Used This Month
      </div>
    </motion.div>
  );
}
