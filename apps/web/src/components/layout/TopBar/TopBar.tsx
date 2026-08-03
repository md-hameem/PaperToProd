"use client";

import { useEffect, useState, useRef } from "react";
import { Bell, Search, Sun, Moon, Check } from "lucide-react";
import { useTheme } from "@/providers/theme-provider";
import { Avatar } from "@/components/ui/Avatar";
import { getNotifications, markNotificationRead } from "@/lib/api";
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

  const [notifications, setNotifications] = useState<any[]>([]);
  const [showNotifMenu, setShowNotifMenu] = useState(false);
  const notifMenuRef = useRef<HTMLDivElement>(null);

  const unreadCount = notifications.filter((n) => !n.is_read).length;
  // If the parent provided notificationCount, use it or fallback to the fetched unreadCount
  const displayCount = notificationCount > 0 ? notificationCount : unreadCount;

  useEffect(() => {
    // We only fetch notifications if this is a logged-in view
    if (userName) {
      loadNotifications();
    }
  }, [userName]);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (notifMenuRef.current && !notifMenuRef.current.contains(event.target as Node)) {
        setShowNotifMenu(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const loadNotifications = async () => {
    try {
      const data = await getNotifications();
      setNotifications(data);
    } catch (err) {
      console.error("Failed to load notifications", err);
    }
  };

  const handleMarkRead = async (id: number) => {
    try {
      await markNotificationRead(id);
      loadNotifications();
    } catch (err) {
      console.error("Failed to mark read", err);
    }
  };

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
        <div className={styles.notifContainer} ref={notifMenuRef}>
          <button
            className={styles.iconBtn}
            aria-label="Notifications"
            onClick={() => setShowNotifMenu(!showNotifMenu)}
          >
            <Bell size={18} />
            {displayCount > 0 && (
              <span className={styles.notifBadge}>
                {displayCount > 9 ? "9+" : displayCount}
              </span>
            )}
          </button>

          {showNotifMenu && (
            <div className={styles.notifMenu}>
              <div className={styles.notifHeader}>
                <h3>Notifications</h3>
              </div>
              <div className={styles.notifList}>
                {notifications.length === 0 ? (
                  <div className={styles.notifEmpty}>No notifications</div>
                ) : (
                  notifications.map((notif) => (
                    <div key={notif.id} className={`${styles.notifItem} ${notif.is_read ? styles.notifRead : ''}`}>
                      <div className={styles.notifContent}>
                        <p>{notif.message}</p>
                        <span className={styles.notifTime}>
                          {new Date(notif.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                        </span>
                      </div>
                      {!notif.is_read && (
                        <button
                          className={styles.markReadBtn}
                          onClick={(e) => { e.stopPropagation(); handleMarkRead(notif.id); }}
                          title="Mark as read"
                        >
                          <Check size={16} />
                        </button>
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

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
