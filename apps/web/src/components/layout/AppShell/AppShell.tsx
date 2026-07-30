"use client";

import { useState } from "react";
import { Sidebar, type NavItem } from "../Sidebar";
import { TopBar } from "../TopBar";
import styles from "./AppShell.module.css";

export interface AppShellProps {
  children: React.ReactNode;
  navItems?: NavItem[];
  activeNav?: string;
  onNavigate?: (id: string) => void;
  pageTitle?: string;
  onSearchClick?: () => void;
  userName?: string;
  userAvatar?: string;
  notificationCount?: number;
}

export function AppShell({
  children,
  navItems,
  activeNav,
  onNavigate,
  pageTitle,
  onSearchClick,
  userName,
  userAvatar,
  notificationCount,
}: AppShellProps) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className={styles.shell}>
      <Sidebar
        items={navItems}
        activeItem={activeNav}
        onNavigate={onNavigate}
        collapsed={collapsed}
        onToggleCollapse={() => setCollapsed(!collapsed)}
      />
      <div className={styles.main}>
        <TopBar
          title={pageTitle}
          onSearchClick={onSearchClick}
          notificationCount={notificationCount}
          userName={userName}
          userAvatar={userAvatar}
        />
        <main className={styles.content}>
          {children}
        </main>
      </div>
    </div>
  );
}
