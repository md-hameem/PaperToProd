"use client";

import React, { useState } from "react";
import { ChevronDown, Check, Building } from "lucide-react";
import { useWorkspace } from "@/contexts/WorkspaceContext";
import styles from "./WorkspaceSelector.module.css";
import { motion, AnimatePresence } from "framer-motion";

export function WorkspaceSelector() {
  const { workspaces, activeWorkspace, setActiveWorkspace, isLoading } = useWorkspace();
  const [isOpen, setIsOpen] = useState(false);

  if (isLoading) {
    return <div className={styles.loadingPlaceholder}>Loading...</div>;
  }

  if (!activeWorkspace) {
    return null;
  }

  return (
    <div className={styles.container}>
      <button
        className={styles.selectorBtn}
        onClick={() => setIsOpen(!isOpen)}
        aria-expanded={isOpen}
      >
        <div className={styles.iconWrapper}>
          <Building size={16} />
        </div>
        <span className={styles.workspaceName}>{activeWorkspace.name}</span>
        <ChevronDown size={14} className={`${styles.chevron} ${isOpen ? styles.open : ""}`} />
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            className={styles.dropdown}
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.15 }}
          >
            <div className={styles.dropdownHeader}>Switch Workspace</div>
            <ul className={styles.workspaceList}>
              {workspaces.map(workspace => (
                <li key={workspace.id}>
                  <button
                    className={styles.workspaceItem}
                    onClick={() => {
                      setActiveWorkspace(workspace);
                      setIsOpen(false);
                    }}
                  >
                    <span className={styles.itemName}>{workspace.name}</span>
                    {workspace.id === activeWorkspace.id && (
                      <Check size={14} className={styles.checkIcon} />
                    )}
                  </button>
                </li>
              ))}
            </ul>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
