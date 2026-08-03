"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { JobResults } from "@/components/JobResults";
import { getSharedJob } from "@/lib/api";
import styles from "./shared.module.css";
import { Zap } from "lucide-react";

export default function SharedJobPage({ params }: { params: { token: string } }) {
  const router = useRouter();
  const [job, setJob] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadJob();
  }, [params.token]);

  const loadJob = async () => {
    try {
      const data = await getSharedJob(params.token);
      setJob(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className={styles.layout}>
        <div className={styles.loading}>Loading shared job...</div>
      </div>
    );
  }

  if (error || !job) {
    return (
      <div className={styles.layout}>
        <div className={styles.errorBox}>
          <h2>Unavailable</h2>
          <p>{error || "This job is not available."}</p>
          <button className={styles.btnPrimary} onClick={() => router.push("/")}>
            Go to PaperToProd
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.layout}>
      <header className={styles.header}>
        <div className={styles.logo}>
          <Zap size={24} color="var(--color-accent)" />
          <span style={{ fontWeight: 600, fontSize: '18px' }}>PaperToProd</span>
          <span className={styles.badge}>Shared View</span>
        </div>
      </header>

      <main className={styles.main}>
        <div className={styles.jobTitleContainer}>
          <h1 className={styles.jobTitle}>{job.paper_title || "Untitled Paper"}</h1>
          <p className={styles.jobDomain}>Domain: {job.domain_classification || "General"}</p>
        </div>

        <JobResults
          jobId={job.id.toString()}
          score={job.fidelity_score || 0}
          stats={{ loc: 1520, files: 12, tests: 34 }} // Mock stats for shared view
          gaps={[]}
          advancedOptions={null}
          isPublic={false}
          readOnly={true}
          allowDownload={job.allow_download}
        />
      </main>

      <footer className={styles.footer}>
        <p>Powered by PaperToProd.</p>
        <button className={styles.btnSecondary} onClick={() => router.push("/")}>
          Try it yourself
        </button>
      </footer>
    </div>
  );
}
