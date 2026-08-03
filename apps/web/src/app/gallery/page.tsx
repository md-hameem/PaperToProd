"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { TopBar } from "@/components/layout/TopBar";
import { Sidebar } from "@/components/layout/Sidebar";
import { getGalleryJobs } from "@/lib/api";
import styles from "./gallery.module.css";
import { Search, Star, Clock, Globe, Zap, FileText } from "lucide-react";
import { formatDistanceToNow } from "date-fns";

export default function GalleryPage() {
  const router = useRouter();
  const [jobs, setJobs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [domainFilter, setDomainFilter] = useState("ALL");
  const [sortOrder, setSortOrder] = useState("score");

  useEffect(() => {
    loadGallery();
  }, [domainFilter, sortOrder]);

  const loadGallery = async () => {
    setLoading(true);
    try {
      const data = await getGalleryJobs(domainFilter, sortOrder);
      setJobs(data);
    } catch (err) {
      console.error("Failed to load gallery", err);
    } finally {
      setLoading(false);
    }
  };

  const getDomainIcon = (domain: string) => {
    switch (domain) {
      case "CV": return <Globe size={14} />;
      case "NLP": return <FileText size={14} />;
      case "RL": return <Zap size={14} />;
      default: return <Search size={14} />;
    }
  };

  return (
    <div className={styles.layout}>
      <Sidebar />
      <div className={styles.main}>
        <TopBar />
        <div className={styles.content}>
          <div className={styles.header}>
            <div>
              <h1 className={styles.title}>Public Gallery</h1>
              <p className={styles.subtitle}>Discover reproductions shared by the community.</p>
            </div>

            <div className={styles.filterBar}>
              <div className={styles.filterGroup}>
                {['ALL', 'CV', 'NLP', 'RL'].map(d => (
                  <button
                    key={d}
                    className={`${styles.filterBtn} ${domainFilter === d ? styles.active : ''}`}
                    onClick={() => setDomainFilter(d)}
                  >
                    {d}
                  </button>
                ))}
              </div>
              <div className={styles.filterGroup}>
                <button
                  className={`${styles.filterBtn} ${sortOrder === 'score' ? styles.active : ''}`}
                  onClick={() => setSortOrder('score')}
                >
                  <Star size={14} style={{ display: 'inline', marginRight: '4px' }}/> Top Rated
                </button>
                <button
                  className={`${styles.filterBtn} ${sortOrder === 'recency' ? styles.active : ''}`}
                  onClick={() => setSortOrder('recency')}
                >
                  <Clock size={14} style={{ display: 'inline', marginRight: '4px' }}/> Recent
                </button>
              </div>
            </div>
          </div>

          {loading ? (
            <div className={styles.loadingText}>Loading gallery...</div>
          ) : jobs.length === 0 ? (
            <div className={styles.emptyState}>
              <Globe size={48} color="var(--color-text-tertiary)" style={{ margin: '0 auto 16px' }} />
              <h3>No jobs found</h3>
              <p>Try adjusting your filters or be the first to publish a reproduction!</p>
            </div>
          ) : (
            <div className={styles.grid}>
              {jobs.map((job) => (
                <div
                  key={job.id}
                  className={styles.card}
                  onClick={() => router.push(`/jobs/${job.id}`)}
                >
                  <div className={styles.cardHeader}>
                    <div className={styles.domainBadge}>
                      {getDomainIcon(job.domain_classification)}
                      {job.domain_classification || "GENERAL"}
                    </div>
                  </div>

                  <h3 className={styles.cardTitle}>
                    {job.paper_title || "Untitled Paper"}
                  </h3>

                  <div className={styles.cardFooter}>
                    <div className={styles.submitter}>
                      <div style={{ width: '24px', height: '24px', borderRadius: '50%', background: 'var(--color-bg-tertiary)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '10px' }}>
                        {job.submitter_username.charAt(0).toUpperCase()}
                      </div>
                      {job.submitter_username}
                    </div>

                    <div className={styles.score}>
                      <Star size={14} fill="currentColor" />
                      {(job.fidelity_score * 100).toFixed(0)}%
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
