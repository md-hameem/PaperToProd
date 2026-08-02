'use client';

import { useEffect, useState, use } from 'react';
import { useRouter } from 'next/navigation';
import { AgentNode, AgentStatus } from '@/components/AgentNode';
import { getToken } from '@/lib/api';
import styles from './progress.module.css';

interface JobEventPayload {
  event_type: 'agent_transition' | 'log_line';
  agent_name?: string;
  status?: string;
  payload?: Record<string, unknown>;
}

interface AgentState {
  name: string;
  label: string;
  status: AgentStatus;
  logs: string[];
}

const INITIAL_AGENTS: AgentState[] = [
  { name: 'extractor', label: 'Extractor Agent', status: 'pending', logs: [] },
  { name: 'finder', label: 'Finder Agent', status: 'pending', logs: [] },
  { name: 'scaffolder', label: 'Scaffolder Agent', status: 'pending', logs: [] },
  { name: 'devops', label: 'DevOps Agent', status: 'pending', logs: [] },
  { name: 'reviewer', label: 'Reviewer Agent', status: 'pending', logs: [] },
  { name: 'docgen', label: 'DocGen Agent', status: 'pending', logs: [] },
];

import { JobResults } from '@/components/JobResults';
import { JobFailure } from '@/components/JobFailure';
import { HumanApprovalModal } from '@/components/HumanApprovalModal';
import { getJob, approveJob } from '@/lib/api';
import { motion, AnimatePresence } from 'framer-motion';

export default function JobProgressPage({ params }: { params: Promise<{ id: string }> }) {
  const router = useRouter();
  const { id } = use(params);
  const [agents, setAgents] = useState<AgentState[]>(INITIAL_AGENTS);
  const [candidates, setCandidates] = useState<any[]>([]);

  // State for final results payload
  const [jobData, setJobData] = useState<Record<string, unknown> | null>(null);

  // Check overall state
  const hasError = agents.some(a => a.status === 'error');
  const isFinished = agents.every(a => a.status === 'completed');

  // Fetch final job data when pipeline finishes
  useEffect(() => {
    if (isFinished && !jobData) {
      getJob(id).then(data => setJobData(data)).catch(console.error);
    }
  }, [isFinished, id, jobData]);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      router.replace('/login');
      return;
    }

    // Connect to WebSocket
    const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
    const ws = new WebSocket(`${WS_URL}/ws/jobs/${id}/events?token=${token}`);

    ws.onmessage = (event) => {
      try {
        const data: JobEventPayload = JSON.parse(event.data);
        if (!data.agent_name) return;

        setAgents(prev => prev.map(agent => {
          if (agent.name !== data.agent_name) return agent;

          let newStatus = agent.status;
          const newLogs = [...agent.logs];

          if (data.event_type === 'agent_transition') {
            if (data.status === 'started') newStatus = 'started';
            if (data.status === 'completed') newStatus = 'completed';
            if (data.status === 'error') newStatus = 'error';
            if (data.status === 'pending_approval') {
              newStatus = 'pending_approval';
              // Note: the payload has candidates
              if (data.payload && data.payload.candidates) {
                setCandidates(data.payload.candidates as any);
              }
            }
          } else if (data.event_type === 'log_line' && data.payload?.message) {
            newLogs.push(data.payload.message as string);
          }

          return { ...agent, status: newStatus, logs: newLogs };
        }));
      } catch (e) {
        console.error('Failed to parse WebSocket message', e);
      }
    };

    return () => {
      ws.close();
    };
  }, [id, router]);

  const errorAgent = agents.find(a => a.status === 'error');

  const isPendingApproval = agents.some(a => a.status === 'pending_approval');

  const handleApprove = async (url: string) => {
    try {
      await approveJob(id, url);
      // Optimistically update the UI to avoid flash
      setAgents(prev => prev.map(a => a.name === 'finder' ? { ...a, status: 'completed' } : a));
    } catch (e) {
      console.error(e);
      alert('Failed to approve repository.');
    }
  };

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <h1 className={styles.title}>Pipeline Execution</h1>
        <p className={styles.subtitle}>Job #{id}</p>
      </header>

      <div className={styles.contentWrapper}>
        <AnimatePresence mode="wait">
          {hasError ? (
            <motion.div key="error" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <JobFailure
                jobId={id}
                reason={`The ${errorAgent?.label} failed during execution.`}
                logs={errorAgent?.logs || []}
              />
            </motion.div>
          ) : (isFinished && jobData) ? (
            <motion.div key="results" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <JobResults
                jobId={id}
                score={85} // Mock score or derive from jobData.score if available
                stats={{ loc: 1204, files: 15, tests: 24 }} // Mock stats
                gaps={['GPU memory constraint assumed 16GB', 'Batch size reduced to 8 for stability']} // Mock gaps
                advancedOptions={(jobData as any)?.advanced_options}
              />
            </motion.div>
          ) : (
            <motion.div key="pipeline" className={styles.pipeline} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0, scale: 0.95, filter: 'blur(4px)' }} transition={{ duration: 0.5 }}>
              {agents.map(agent => (
                <AgentNode
                  key={agent.name}
                  name={agent.name}
                  label={agent.label}
                  status={agent.status}
                  logs={agent.logs}
                  isActive={agent.status === 'started'}
                />
              ))}
            </motion.div>
          )}
        </AnimatePresence>

        <AnimatePresence>
          {isPendingApproval && (
            <HumanApprovalModal
              candidates={candidates}
              onApprove={handleApprove}
            />
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
