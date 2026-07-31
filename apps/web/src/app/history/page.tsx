'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { TopBar } from '@/components/layout/TopBar';
import { listJobs, getToken } from '@/lib/api';
import { Play, Download, Search, FileText } from 'lucide-react';
import styles from './history.module.css';

interface JobSummary {
  id: string;
  paper_url: string;
  status: string;
  created_at: string;
  fidelity_score?: number;
}

export default function HistoryPage() {
  const router = useRouter();
  const [jobs, setJobs] = useState<JobSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!getToken()) {
      router.replace('/login');
      return;
    }

    listJobs()
      .then(data => setJobs(data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [router]);

  return (
    <div className={styles.container}>
      <TopBar
        title="Job History"
        onSearchClick={() => {}}
      />

      <main className={styles.main}>
        <div className={styles.headerRow}>
          <div>
            <h2 className={styles.pageTitle}>Recent Generations</h2>
            <p className={styles.pageSubtitle}>View and manage your previously generated repositories.</p>
          </div>
          <button className={styles.newJobBtn} onClick={() => router.push('/')}>
            <Play size={16} /> New Job
          </button>
        </div>

        {loading ? (
          <div className={styles.tableWrapper}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Job ID</th><th>Paper</th><th>Status</th><th>Fidelity</th><th>Date</th><th className={styles.actionHeader}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {[1, 2, 3, 4, 5].map(i => (
                  <tr key={i} className={styles.row}>
                    <td><div className="skeleton" style={{ height: 20, width: 80 }} /></td>
                    <td><div className="skeleton" style={{ height: 20, width: '100%' }} /></td>
                    <td><div className="skeleton" style={{ height: 24, width: 60, borderRadius: 12 }} /></td>
                    <td><div className="skeleton" style={{ height: 20, width: 40 }} /></td>
                    <td><div className="skeleton" style={{ height: 20, width: 80 }} /></td>
                    <td><div className="skeleton" style={{ height: 20, width: 60, float: 'right' }} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : jobs.length === 0 ? (
          <div className={styles.emptyState}>
            <div className={styles.emptyIconWrapper}>
              <FileText size={48} className={styles.emptyIcon} />
            </div>
            <h3 className={styles.emptyTitle}>No jobs yet</h3>
            <p className={styles.emptyDesc}>Submit your first arXiv paper to generate a repository.</p>
            <button className={styles.emptyBtn} onClick={() => router.push('/')}>
              Submit a Paper
            </button>
          </div>
        ) : (
          <div className={styles.tableWrapper}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Job ID</th>
                  <th>Paper</th>
                  <th>Status</th>
                  <th>Fidelity</th>
                  <th>Date</th>
                  <th className={styles.actionHeader}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {jobs.map(job => (
                  <tr key={job.id} onClick={() => router.push(`/jobs/${job.id}`)} className={styles.row}>
                    <td className={styles.cellId}>#{job.id.slice(0, 8)}</td>
                    <td className={styles.cellPaper}>
                      <a href={job.paper_url} target="_blank" rel="noreferrer" onClick={e => e.stopPropagation()}>
                        {job.paper_url.split('/').pop()}
                      </a>
                    </td>
                    <td>
                      <span className={`${styles.statusChip} ${styles[job.status] || styles.pending}`}>
                        {job.status}
                      </span>
                    </td>
                    <td>
                      {job.fidelity_score !== undefined ? (
                        <div className={styles.scoreBadge}>
                          {job.fidelity_score}/100
                        </div>
                      ) : '-'}
                    </td>
                    <td className={styles.cellDate}>
                      {new Date(job.created_at).toLocaleDateString()}
                    </td>
                    <td className={styles.cellActions} onClick={e => e.stopPropagation()}>
                      <button className={styles.iconBtn} aria-label="View Job" onClick={() => router.push(`/jobs/${job.id}`)}>
                        <Search size={18} />
                      </button>
                      <button className={styles.iconBtn} aria-label="Download" disabled={job.status !== 'completed'}>
                        <Download size={18} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  );
}
