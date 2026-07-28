"use client";

import { motion } from "framer-motion";
import styles from "./ProgressRing.module.css";

export interface ProgressRingProps {
  value: number; // 0-100
  size?: number;
  strokeWidth?: number;
  label?: string;
  showValue?: boolean;
  className?: string;
}

export function ProgressRing({
  value,
  size = 80,
  strokeWidth = 6,
  label,
  showValue = true,
  className = "",
}: ProgressRingProps) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (value / 100) * circumference;

  // Color based on fidelity score ranges
  const getColor = (val: number) => {
    if (val >= 80) return "var(--color-fidelity-high)";
    if (val >= 50) return "var(--color-fidelity-mid)";
    return "var(--color-fidelity-low)";
  };

  return (
    <div className={`${styles.wrapper} ${className}`} style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        {/* Background track */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="var(--color-bg-tertiary)"
          strokeWidth={strokeWidth}
        />
        {/* Progress arc */}
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={getColor(value)}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
        />
      </svg>
      {showValue && (
        <div className={styles.valueContainer}>
          <motion.span
            className={styles.value}
            style={{ color: getColor(value) }}
          >
            {Math.round(value)}
          </motion.span>
          {label && <span className={styles.label}>{label}</span>}
        </div>
      )}
    </div>
  );
}
