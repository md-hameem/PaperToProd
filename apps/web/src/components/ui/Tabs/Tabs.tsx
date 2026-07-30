"use client";

import { motion } from "framer-motion";
import styles from "./Tabs.module.css";

export interface Tab {
  id: string;
  label: string;
  icon?: React.ReactNode;
  count?: number;
}

export interface TabsProps {
  tabs: Tab[];
  activeTab: string;
  onChange: (tabId: string) => void;
  className?: string;
}

export function Tabs({ tabs, activeTab, onChange, className = "" }: TabsProps) {
  return (
    <div className={`${styles.tabs} ${className}`} role="tablist">
      {tabs.map((tab) => {
        const isActive = tab.id === activeTab;
        return (
          <button
            key={tab.id}
            role="tab"
            aria-selected={isActive}
            className={`${styles.tab} ${isActive ? styles.active : ""}`}
            onClick={() => onChange(tab.id)}
          >
            {tab.icon && <span className={styles.icon}>{tab.icon}</span>}
            <span>{tab.label}</span>
            {tab.count !== undefined && (
              <span className={styles.count}>{tab.count}</span>
            )}
            {isActive && (
              <motion.div
                className={styles.indicator}
                layoutId="tab-indicator"
                transition={{ type: "spring", stiffness: 300, damping: 28 }}
              />
            )}
          </button>
        );
      })}
    </div>
  );
}
