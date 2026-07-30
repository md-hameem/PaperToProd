"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Search, ArrowRight } from "lucide-react";
import styles from "./CommandPalette.module.css";

export interface CommandItem {
  id: string;
  label: string;
  icon?: React.ReactNode;
  section?: string;
  shortcut?: string;
  onSelect: () => void;
}

export interface CommandPaletteProps {
  items: CommandItem[];
  open: boolean;
  onClose: () => void;
  placeholder?: string;
}

export function CommandPalette({
  items,
  open,
  onClose,
  placeholder = "Search commands…",
}: CommandPaletteProps) {
  const [query, setQuery] = useState("");
  const [focusedIndex, setFocusedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const filtered = items.filter((item) =>
    item.label.toLowerCase().includes(query.toLowerCase())
  );

  // Group by section
  const sections = new Map<string, CommandItem[]>();
  for (const item of filtered) {
    const key = item.section || "Actions";
    if (!sections.has(key)) sections.set(key, []);
    sections.get(key)!.push(item);
  }

  const flatItems = filtered;

  // Reset on open
  useEffect(() => {
    if (open) {
      setQuery("");
      setFocusedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [open]);

  // Keyboard shortcut to open (Cmd/Ctrl + K)
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        // Toggle is handled by parent — this is just for reference
      }
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, []);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      switch (e.key) {
        case "ArrowDown":
          e.preventDefault();
          setFocusedIndex((i) => Math.min(i + 1, flatItems.length - 1));
          break;
        case "ArrowUp":
          e.preventDefault();
          setFocusedIndex((i) => Math.max(i - 1, 0));
          break;
        case "Enter":
          e.preventDefault();
          if (flatItems[focusedIndex]) {
            flatItems[focusedIndex].onSelect();
            onClose();
          }
          break;
        case "Escape":
          onClose();
          break;
      }
    },
    [flatItems, focusedIndex, onClose]
  );

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className={styles.overlay}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.15 }}
          onClick={onClose}
        >
          <motion.div
            className={styles.panel}
            initial={{ opacity: 0, scale: 0.95, y: -20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -20 }}
            transition={{ type: "spring", stiffness: 400, damping: 30 }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Search input */}
            <div className={styles.inputWrapper}>
              <Search size={18} className={styles.searchIcon} />
              <input
                ref={inputRef}
                type="text"
                className={styles.input}
                placeholder={placeholder}
                value={query}
                onChange={(e) => {
                  setQuery(e.target.value);
                  setFocusedIndex(0);
                }}
                onKeyDown={handleKeyDown}
              />
            </div>

            {/* Results */}
            <div className={styles.results}>
              {flatItems.length === 0 ? (
                <div className={styles.empty}>No results found</div>
              ) : (
                Array.from(sections.entries()).map(([section, sectionItems]) => (
                  <div key={section} className={styles.section}>
                    <div className={styles.sectionTitle}>{section}</div>
                    {sectionItems.map((item) => {
                      const globalIndex = flatItems.indexOf(item);
                      return (
                        <button
                          key={item.id}
                          className={`${styles.item} ${globalIndex === focusedIndex ? styles.focused : ""}`}
                          onMouseEnter={() => setFocusedIndex(globalIndex)}
                          onClick={() => {
                            item.onSelect();
                            onClose();
                          }}
                        >
                          {item.icon && <span className={styles.itemIcon}>{item.icon}</span>}
                          <span className={styles.itemLabel}>{item.label}</span>
                          {item.shortcut && (
                            <kbd className={styles.shortcut}>{item.shortcut}</kbd>
                          )}
                          <ArrowRight size={14} className={styles.arrow} />
                        </button>
                      );
                    })}
                  </div>
                ))
              )}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
