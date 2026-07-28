"use client";

import { motion } from "framer-motion";
import styles from "./Card.module.css";

export interface CardProps {
  variant?: "default" | "elevated" | "outlined";
  hoverable?: boolean;
  padding?: "none" | "sm" | "md" | "lg";
  className?: string;
  children?: React.ReactNode;
  onClick?: () => void;
}

export function Card({
  variant = "default",
  hoverable = false,
  padding = "md",
  className = "",
  children,
  onClick,
}: CardProps) {
  const cls = `${styles.card} ${styles[variant]} ${styles[`pad-${padding}`]} ${className}`;

  if (hoverable) {
    return (
      <motion.div
        className={cls}
        whileHover={{ y: -2, boxShadow: "var(--shadow-lg)" }}
        transition={{ type: "spring" as const, stiffness: 300, damping: 24 }}
        onClick={onClick}
      >
        {children}
      </motion.div>
    );
  }

  return (
    <div className={cls} onClick={onClick}>
      {children}
    </div>
  );
}
