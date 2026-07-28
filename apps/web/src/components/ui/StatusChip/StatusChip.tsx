"use client";

import styles from "./StatusChip.module.css";

type StatusType =
  | "queued"
  | "running"
  | "complete"
  | "partial"
  | "failed"
  | "cancelled";

type AgentType =
  | "extractor"
  | "finder"
  | "scaffolder"
  | "devops"
  | "reviewer"
  | "docgen";

export interface StatusChipProps {
  status?: StatusType;
  agent?: AgentType;
  label?: string;
  size?: "sm" | "md";
  className?: string;
}

const statusLabels: Record<StatusType, string> = {
  queued: "Queued",
  running: "Running",
  complete: "Complete",
  partial: "Partial",
  failed: "Failed",
  cancelled: "Cancelled",
};

export function StatusChip({
  status,
  agent,
  label,
  size = "md",
  className = "",
}: StatusChipProps) {
  const chipLabel =
    label || (status ? statusLabels[status] : agent || "Unknown");
  const colorClass = status
    ? styles[`status-${status}`]
    : agent
      ? styles[`agent-${agent}`]
      : "";

  return (
    <span
      className={`${styles.chip} ${styles[size]} ${colorClass} ${className}`}
    >
      {(status === "running") && <span className={styles.pulse} />}
      {chipLabel}
    </span>
  );
}
