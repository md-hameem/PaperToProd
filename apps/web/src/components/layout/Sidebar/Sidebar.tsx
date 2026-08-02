"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
  Home,
  FolderKanban,
  LayoutGrid,
  Settings,
  ChevronLeft,
  ChevronRight,
  User,
} from "lucide-react";
import styles from "./Sidebar.module.css";
import { WorkspaceSelector } from "./WorkspaceSelector";

export interface NavItem {
  id: string;
  label: string;
  icon: React.ReactNode;
  href?: string;
  badge?: number;
}

export interface SidebarProps {
  items?: NavItem[];
  activeItem?: string;
  onNavigate?: (id: string) => void;
  collapsed?: boolean;
  onToggleCollapse?: () => void;
  header?: React.ReactNode;
  footer?: React.ReactNode;
  className?: string;
}

const defaultItems: NavItem[] = [
  { id: "dashboard", label: "Dashboard", icon: <Home size={20} /> },
  { id: "jobs", label: "Jobs", icon: <FolderKanban size={20} /> },
  { id: "gallery", label: "Gallery", icon: <LayoutGrid size={20} /> },
  { id: "settings/workspace", label: "Workspace", icon: <Settings size={20} /> },
  { id: "settings/profile", label: "Profile", icon: <User size={20} /> },
];

export function Sidebar({
  items = defaultItems,
  activeItem = "dashboard",
  onNavigate,
  collapsed = false,
  onToggleCollapse,
  header,
  footer,
  className = "",
}: SidebarProps) {
  const [hovered, setHovered] = useState<string | null>(null);

  return (
    <motion.aside
      className={`${styles.sidebar} ${collapsed ? styles.collapsed : ""} ${className}`}
      animate={{ width: collapsed ? 64 : 240 }}
      transition={{ type: "spring", stiffness: 300, damping: 28 }}
    >
      {/* Header */}
      <div className={styles.header}>
        {header || (
          <div className={styles.brand}>
            <div className={styles.logo}>P</div>
            {!collapsed && (
              <motion.span
                className={styles.brandName}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
              >
                PaperToProd
              </motion.span>
            )}
          </div>
        )}
      </div>

      {!collapsed && <WorkspaceSelector />}


      {/* Nav */}
      <nav className={styles.nav}>
        {items.map((item) => {
          const isActive = item.id === activeItem;
          const isHovered = item.id === hovered;
          return (
            <button
              key={item.id}
              className={`${styles.navItem} ${isActive ? styles.active : ""}`}
              onClick={() => onNavigate?.(item.id)}
              onMouseEnter={() => setHovered(item.id)}
              onMouseLeave={() => setHovered(null)}
              aria-current={isActive ? "page" : undefined}
              title={collapsed ? item.label : undefined}
            >
              <span className={styles.navIcon}>{item.icon}</span>
              {!collapsed && <span className={styles.navLabel}>{item.label}</span>}
              {!collapsed && item.badge !== undefined && item.badge > 0 && (
                <span className={styles.badge}>{item.badge}</span>
              )}
              {isActive && (
                <motion.div
                  className={styles.activeIndicator}
                  layoutId="sidebar-active"
                  transition={{ type: "spring", stiffness: 300, damping: 28 }}
                />
              )}
              {isHovered && !isActive && (
                <motion.div
                  className={styles.hoverBg}
                  layoutId="sidebar-hover"
                  transition={{ type: "spring", stiffness: 300, damping: 28 }}
                />
              )}
            </button>
          );
        })}
      </nav>

      {/* Footer */}
      <div className={styles.footer}>
        {footer}
        {onToggleCollapse && (
          <button
            className={styles.collapseBtn}
            onClick={onToggleCollapse}
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
          </button>
        )}
      </div>
    </motion.aside>
  );
}
