"use client";

import styles from "./Avatar.module.css";

export interface AvatarProps {
  src?: string;
  alt?: string;
  name?: string;
  size?: "sm" | "md" | "lg";
  className?: string;
}

function getInitials(name: string): string {
  return name
    .split(" ")
    .map((w) => w[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();
}

function hashColor(name: string): string {
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  const hue = Math.abs(hash % 360);
  return `hsl(${hue}, 55%, 55%)`;
}

export function Avatar({
  src,
  alt,
  name,
  size = "md",
  className = "",
}: AvatarProps) {
  const initials = name ? getInitials(name) : "?";
  const bgColor = name ? hashColor(name) : "var(--color-bg-tertiary)";

  if (src) {
    // eslint-disable-next-line @next/next/no-img-element
    return (
      <img
        src={src}
        alt={alt || name || "Avatar"}
        className={`${styles.avatar} ${styles[size]} ${className}`}
      />
    );
  }

  return (
    <div
      className={`${styles.avatar} ${styles.fallback} ${styles[size]} ${className}`}
      style={{ backgroundColor: bgColor }}
      aria-label={name || "Avatar"}
    >
      <span className={styles.initials}>{initials}</span>
    </div>
  );
}
