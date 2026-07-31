'use client';

import { useEffect, useState } from 'react';
import { motion, useAnimation } from 'framer-motion';
import styles from './FidelityRing.module.css';

interface FidelityRingProps {
  score: number; // 0 to 100
  size?: number;
  strokeWidth?: number;
}

export function FidelityRing({ score, size = 120, strokeWidth = 10 }: FidelityRingProps) {
  const [displayScore, setDisplayScore] = useState(0);
  const controls = useAnimation();
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;

  useEffect(() => {
    // Animate the SVG stroke
    controls.start({
      strokeDashoffset: circumference - (score / 100) * circumference,
      transition: { duration: 1.2, ease: "easeOut" }
    });

    // Count up the number
    let startTimestamp: number | null = null;
    const duration = 1200; // ms

    const step = (timestamp: number) => {
      if (!startTimestamp) startTimestamp = timestamp;
      const progress = Math.min((timestamp - startTimestamp) / duration, 1);

      // ease-out cubic
      const easeOut = 1 - Math.pow(1 - progress, 3);
      setDisplayScore(Math.floor(easeOut * score));

      if (progress < 1) {
        window.requestAnimationFrame(step);
      }
    };

    window.requestAnimationFrame(step);
  }, [score, circumference, controls]);

  // Determine color based on score
  const getColor = () => {
    if (score >= 80) return 'var(--color-status-success)';
    if (score >= 50) return 'var(--color-status-warning)';
    return 'var(--color-status-error)';
  };

  return (
    <div className={styles.container} style={{ width: size, height: size }}>
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        className={styles.svg}
      >
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="var(--color-border-primary)"
          strokeWidth={strokeWidth}
          fill="none"
        />
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={getColor()}
          strokeWidth={strokeWidth}
          fill="none"
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={controls}
          className={styles.progressRing}
        />
      </svg>
      <div className={styles.scoreContainer}>
        <span className={styles.score}>{displayScore}</span>
        <span className={styles.label}>/100</span>
      </div>
    </div>
  );
}
