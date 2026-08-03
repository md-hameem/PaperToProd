'use client';

import { useEffect, useState, use } from 'react';
import { useRouter } from 'next/navigation';
import { getJob } from '@/lib/api';
import { CheckCircle2, XCircle, AlertTriangle, ShieldCheck, ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import styles from './fidelity.module.css';

interface CoverageItem {
  component_name: string;
  has_code: boolean;
  reason_if_missing: string;
}

interface StructuralCheck {
  check_name: string;
  status: 'pass' | 'fail' | 'warning';
  details: string;
}

interface Assumption {
  description: string;
  rationale: string;
}

interface BenchmarkMetric {
  metric_name: string;
  paper_baseline: number;
  reproduced_value: number;
  delta: number;
  status: 'pass' | 'warning' | 'fail';
}

interface BenchmarkResult {
  dataset_name: string;
  metrics: BenchmarkMetric[];
  summary: string;
}

interface FidelityReport {
  coverage: CoverageItem[];
  structural_checks: StructuralCheck[];
  execution: { success: boolean; summary: string };
  assumptions: Assumption[];
  license: { source_repo_url: string; license_type: string; disclosure_text: string };
}

export default function FidelityReportPage({ params }: { params: Promise<{ id: string }> }) {
  const router = useRouter();
  const { id } = use(params);
  const [report, setReport] = useState<FidelityReport | null>(null);
  const [benchmarkResults, setBenchmarkResults] = useState<BenchmarkResult | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    getJob(id)
      .then(data => {
        const doc = data.state?.documentation as any;
        if (doc && doc.fidelity_report) {
          setReport(doc.fidelity_report);
        } else {
          setError('Fidelity report not found for this job.');
        }

        if (data.benchmark_results) {
          setBenchmarkResults(data.benchmark_results);
        } else if (data.state?.benchmark_results) {
          setBenchmarkResults(data.state.benchmark_results);
        }
      })
      .catch(err => {
        console.error(err);
        setError('Failed to load fidelity report.');
      })
      .finally(() => setIsLoading(false));
  }, [id]);

  if (isLoading) {
    return <div className={styles.container}>Loading Fidelity Report...</div>;
  }

  if (error || !report) {
    return <div className={styles.container}>{error || 'Report not found.'}</div>;
  }

  const getStatusIcon = (status: string) => {
    if (status === 'pass') return <CheckCircle2 size={16} />;
    if (status === 'fail') return <XCircle size={16} />;
    return <AlertTriangle size={16} />;
  };

  const getStatusClass = (status: string) => {
    if (status === 'pass') return styles.statusPass;
    if (status === 'fail') return styles.statusFail;
    return styles.statusWarn;
  };

  const getBadgeClass = (status: string) => {
    if (status === 'pass') return `${styles.badge} ${styles.pass}`;
    if (status === 'fail') return `${styles.badge} ${styles.fail}`;
    return `${styles.badge} ${styles.warn}`;
  };

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <Link href={`/jobs/${id}`} className="text-secondary hover:text-primary flex items-center gap-2 mb-6" style={{ textDecoration: 'none', color: 'var(--color-text-secondary)', display: 'inline-flex', alignItems: 'center', gap: '8px', marginBottom: '24px' }}>
          <ArrowLeft size={16} /> Back to Job Results
        </Link>
        <h1 className={styles.title}>Fidelity Report</h1>
        <p className={styles.subtitle}>Detailed analysis of generated code adherence to the original paper.</p>
      </header>

      {/* Execution Summary */}
      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>
          <ShieldCheck size={24} className={styles.statusPass} /> Execution Validation
        </h2>
        <div className={styles.card}>
          <h3 className={styles.cardTitle}>
            Status: <span className={getBadgeClass(report.execution.success ? 'pass' : 'fail')}>
              {report.execution.success ? 'Success' : 'Failed'}
            </span>
          </h3>
          <p className={styles.cardDesc}>{report.execution.summary}</p>
        </div>
      </section>

      {/* Coverage Breakdown Table */}
      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>Methodology Coverage</h2>
        <table className={styles.table}>
          <thead>
            <tr>
              <th className={styles.th}>Component</th>
              <th className={styles.th}>Status</th>
              <th className={styles.th}>Notes</th>
            </tr>
          </thead>
          <tbody>
            {report.coverage.map((item, idx) => (
              <tr key={idx}>
                <td className={styles.td}><strong>{item.component_name}</strong></td>
                <td className={styles.td}>
                  <span className={getStatusClass(item.has_code ? 'pass' : 'fail')}>
                    {getStatusIcon(item.has_code ? 'pass' : 'fail')}
                    {item.has_code ? 'Implemented' : 'Missing'}
                  </span>
                </td>
                <td className={styles.td}>{item.reason_if_missing || '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {/* Benchmark Results */}
      {benchmarkResults && (
        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Quantitative Benchmarks</h2>
          <div className={styles.card}>
            <h3 className={styles.cardTitle}>Dataset: {benchmarkResults.dataset_name}</h3>
            <p className={styles.cardDesc} style={{ marginBottom: '16px' }}>{benchmarkResults.summary}</p>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th className={styles.th}>Metric</th>
                  <th className={styles.th}>Paper Baseline</th>
                  <th className={styles.th}>Reproduced</th>
                  <th className={styles.th}>Delta</th>
                  <th className={styles.th}>Status</th>
                </tr>
              </thead>
              <tbody>
                {benchmarkResults.metrics.map((m, idx) => (
                  <tr key={idx}>
                    <td className={styles.td}><strong>{m.metric_name}</strong></td>
                    <td className={styles.td}>{m.paper_baseline}</td>
                    <td className={styles.td}>{m.reproduced_value}</td>
                    <td className={styles.td}>{m.delta > 0 ? `+${m.delta.toFixed(2)}` : m.delta.toFixed(2)}</td>
                    <td className={styles.td}>
                      <span className={getBadgeClass(m.status)}>{m.status.toUpperCase()}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {/* Structural Checks */}
      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>Structural Validation</h2>
        <div className={styles.list}>
          {report.structural_checks.map((check, idx) => (
            <div key={idx} className={styles.listItem}>
              <div style={{ marginTop: '2px' }} className={getStatusClass(check.status)}>
                {getStatusIcon(check.status)}
              </div>
              <div className={styles.listContent}>
                <h4 className={styles.listTitle}>{check.check_name}</h4>
                <p className={styles.listDesc}>{check.details}</p>
              </div>
              <div>
                <span className={getBadgeClass(check.status)}>{check.status.toUpperCase()}</span>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Assumptions */}
      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>Assumptions & Gaps</h2>
        <div className={styles.list}>
          {report.assumptions.length === 0 ? (
            <div className={styles.card}>
              <p className={styles.cardDesc}>No major assumptions were required.</p>
            </div>
          ) : (
            report.assumptions.map((assumption, idx) => (
              <div key={idx} className={styles.listItem}>
                <div style={{ marginTop: '2px' }} className={styles.statusWarn}>
                  <AlertTriangle size={16} />
                </div>
                <div className={styles.listContent}>
                  <h4 className={styles.listTitle}>{assumption.description}</h4>
                  <p className={styles.listDesc}><strong>Rationale:</strong> {assumption.rationale}</p>
                </div>
              </div>
            ))
          )}
        </div>
      </section>

      {/* License Panel */}
      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>License & Attribution</h2>
        <div className={styles.card}>
          <h3 className={styles.cardTitle}>Source: <a href={report.license.source_repo_url} target="_blank" rel="noreferrer" style={{ color: 'var(--color-accent)' }}>{report.license.source_repo_url}</a></h3>
          <p className={styles.cardDesc}><strong>License Type:</strong> {report.license.license_type}</p>
          <div style={{ marginTop: '16px', padding: '16px', background: 'var(--color-background)', borderRadius: 'var(--radius-md)', fontSize: 'var(--type-ui-sm)', color: 'var(--color-text-secondary)' }}>
            {report.license.disclosure_text}
          </div>
        </div>
      </section>
    </div>
  );
}
