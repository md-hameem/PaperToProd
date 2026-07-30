"use client";

import { forwardRef, useState, useRef, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, Check } from "lucide-react";
import styles from "./Select.module.css";

export interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

export interface SelectProps {
  options: SelectOption[];
  value?: string;
  onChange?: (value: string) => void;
  label?: string;
  placeholder?: string;
  error?: string;
  disabled?: boolean;
  className?: string;
}

const Select = forwardRef<HTMLDivElement, SelectProps>(
  (
    {
      options,
      value,
      onChange,
      label,
      placeholder = "Select…",
      error,
      disabled = false,
      className = "",
    },
    ref
  ) => {
    const [open, setOpen] = useState(false);
    const [focusedIndex, setFocusedIndex] = useState(-1);
    const containerRef = useRef<HTMLDivElement>(null);
    const selectedOption = options.find((o) => o.value === value);

    const close = useCallback(() => {
      setOpen(false);
      setFocusedIndex(-1);
    }, []);

    // Close on outside click
    useEffect(() => {
      if (!open) return;
      const handler = (e: MouseEvent) => {
        if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
          close();
        }
      };
      document.addEventListener("mousedown", handler);
      return () => document.removeEventListener("mousedown", handler);
    }, [open, close]);

    const handleKeyDown = (e: React.KeyboardEvent) => {
      if (disabled) return;

      switch (e.key) {
        case "Enter":
        case " ":
          e.preventDefault();
          if (open && focusedIndex >= 0) {
            const opt = options[focusedIndex];
            if (!opt.disabled) {
              onChange?.(opt.value);
              close();
            }
          } else {
            setOpen(true);
          }
          break;
        case "ArrowDown":
          e.preventDefault();
          if (!open) {
            setOpen(true);
          } else {
            setFocusedIndex((i) => Math.min(i + 1, options.length - 1));
          }
          break;
        case "ArrowUp":
          e.preventDefault();
          setFocusedIndex((i) => Math.max(i - 1, 0));
          break;
        case "Escape":
          close();
          break;
      }
    };

    return (
      <div className={`${styles.wrapper} ${className}`} ref={ref}>
        {label && <span className={styles.label}>{label}</span>}
        <div ref={containerRef} className={styles.container}>
          <button
            type="button"
            className={`${styles.trigger} ${open ? styles.open : ""} ${error ? styles.error : ""}`}
            onClick={() => !disabled && setOpen(!open)}
            onKeyDown={handleKeyDown}
            disabled={disabled}
            aria-haspopup="listbox"
            aria-expanded={open}
          >
            <span className={selectedOption ? styles.selectedText : styles.placeholder}>
              {selectedOption?.label || placeholder}
            </span>
            <ChevronDown
              size={16}
              className={`${styles.chevron} ${open ? styles.chevronOpen : ""}`}
            />
          </button>

          <AnimatePresence>
            {open && (
              <motion.ul
                className={styles.dropdown}
                role="listbox"
                initial={{ opacity: 0, y: -4, scaleY: 0.95 }}
                animate={{ opacity: 1, y: 0, scaleY: 1 }}
                exit={{ opacity: 0, y: -4, scaleY: 0.95 }}
                transition={{ duration: 0.15, ease: [0.16, 1, 0.3, 1] }}
                style={{ transformOrigin: "top" }}
              >
                {options.map((opt, i) => (
                  <li
                    key={opt.value}
                    role="option"
                    aria-selected={opt.value === value}
                    className={`${styles.option} ${opt.value === value ? styles.optionSelected : ""} ${i === focusedIndex ? styles.optionFocused : ""} ${opt.disabled ? styles.optionDisabled : ""}`}
                    onClick={() => {
                      if (!opt.disabled) {
                        onChange?.(opt.value);
                        close();
                      }
                    }}
                    onMouseEnter={() => setFocusedIndex(i)}
                  >
                    <span>{opt.label}</span>
                    {opt.value === value && <Check size={14} />}
                  </li>
                ))}
              </motion.ul>
            )}
          </AnimatePresence>
        </div>
        {error && <p className={styles.errorText}>{error}</p>}
      </div>
    );
  }
);

Select.displayName = "Select";

export { Select };
