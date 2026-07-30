"use client";

import { motion } from "framer-motion";
import { Check } from "lucide-react";
import styles from "./Checkbox.module.css";

export interface CheckboxProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label?: string;
  disabled?: boolean;
  indeterminate?: boolean;
  id?: string;
  className?: string;
}

export function Checkbox({
  checked,
  onChange,
  label,
  disabled = false,
  indeterminate = false,
  id,
  className = "",
}: CheckboxProps) {
  const checkboxId = id || label?.toLowerCase().replace(/\s+/g, "-");

  return (
    <label
      htmlFor={checkboxId}
      className={`${styles.wrapper} ${disabled ? styles.disabled : ""} ${className}`}
    >
      <button
        id={checkboxId}
        type="button"
        role="checkbox"
        aria-checked={indeterminate ? "mixed" : checked}
        aria-label={label}
        disabled={disabled}
        className={`${styles.box} ${checked || indeterminate ? styles.checked : ""}`}
        onClick={() => onChange(!checked)}
      >
        <motion.span
          className={styles.indicator}
          initial={false}
          animate={{ scale: checked || indeterminate ? 1 : 0, opacity: checked || indeterminate ? 1 : 0 }}
          transition={{ type: "spring", stiffness: 300, damping: 24 }}
        >
          {indeterminate ? (
            <span className={styles.dash} />
          ) : (
            <Check size={12} strokeWidth={3} />
          )}
        </motion.span>
      </button>
      {label && <span className={styles.label}>{label}</span>}
    </label>
  );
}
