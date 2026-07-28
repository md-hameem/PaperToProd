"use client";

import { motion } from "framer-motion";
import styles from "./Toggle.module.css";

export interface ToggleProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label?: string;
  disabled?: boolean;
  id?: string;
  className?: string;
}

export function Toggle({
  checked,
  onChange,
  label,
  disabled = false,
  id,
  className = "",
}: ToggleProps) {
  const toggleId = id || label?.toLowerCase().replace(/\s+/g, "-");

  return (
    <label
      htmlFor={toggleId}
      className={`${styles.wrapper} ${disabled ? styles.disabled : ""} ${className}`}
    >
      <button
        id={toggleId}
        role="switch"
        type="button"
        aria-checked={checked}
        aria-label={label}
        disabled={disabled}
        className={`${styles.track} ${checked ? styles.checked : ""}`}
        onClick={() => onChange(!checked)}
      >
        <motion.span
          className={styles.thumb}
          layout
          transition={{ type: "spring", stiffness: 300, damping: 24 }}
        />
      </button>
      {label && <span className={styles.label}>{label}</span>}
    </label>
  );
}
