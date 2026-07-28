"use client";

import styles from "./Skeleton.module.css";

export interface SkeletonProps {
  /** Shape: text line, circle (avatar), rectangle (card), or inline block */
  variant?: "text" | "circle" | "rect" | "inline";
  width?: string | number;
  height?: string | number;
  className?: string;
}

export function Skeleton({
  variant = "text",
  width,
  height,
  className = "",
}: SkeletonProps) {
  return (
    <div
      className={`skeleton ${styles.skeleton} ${styles[variant]} ${className}`}
      style={{ width, height }}
      aria-hidden="true"
    />
  );
}
