"use client";

import { Bell, Search, Sun, Moon } from "lucide-react";
import { useTheme } from "@/providers/theme-provider";
import { Avatar } from "@/components/ui/Avatar";
import styles from "./TopBar.module.css";

export interface TopBarProps {
  title?: string;
  onSearchClick?: () => void;
  notificationCount?: number;
  userName?: string;
  userAvatar?: string;
  className?: string;
}

export function TopBar({
  title,
  onSearchClick,
  notificationCount = 0,
  userName,
  userAvatar,
  className = "",
}: TopBarProps) {
  const { theme, toggleTheme } = useTheme();

  return (
    <header className={`${styles.topbar} ${className}`}>
      <div className={styles.left}>
        {title && <h1 className={styles.title}>{title}</h1>}
      </div>

      <div className={styles.right}>
        {/* Search trigger */}
        {onSearchClick && (
          <button
            className={styles.iconBtn}
            onClick={onSearchClick}
            aria-label="Search (Ctrl+K)"
          >
            <Search size={18} />
            <kbd className={styles.kbd}>⌘K</kbd>
          </button>
        )}

        {/* Theme toggle */}
        <button
          className={styles.iconBtn}
          onClick={toggleTheme}
          aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
        >
          {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
        </button>

        {/* Notifications */}
        <button className={styles.iconBtn} aria-label="Notifications">
          <Bell size={18} />
          {notificationCount > 0 && (
            <span className={styles.notifBadge}>
              {notificationCount > 9 ? "9+" : notificationCount}
            </span>
          )}
        </button>

        {/* User */}
        <button className={styles.userBtn} aria-label="Account menu">
          <Avatar
            src={userAvatar}
            name={userName || "User"}
            size="sm"
          />
        </button>
      </div>
    </header>
  );
}
