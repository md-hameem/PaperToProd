"use client";

import { forwardRef } from "react";
import { motion } from "framer-motion";
import { Loader2 } from "lucide-react";
import styles from "./Button.module.css";

export interface ButtonProps {
  variant?: "primary" | "secondary" | "ghost" | "destructive";
  size?: "sm" | "md" | "lg";
  loading?: boolean;
  icon?: React.ReactNode;
  iconPosition?: "left" | "right";
  disabled?: boolean;
  children?: React.ReactNode;
  className?: string;
  type?: "button" | "submit" | "reset";
  onClick?: React.MouseEventHandler<HTMLButtonElement>;
  "aria-label"?: string;
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = "primary",
      size = "md",
      loading = false,
      icon,
      iconPosition = "left",
      disabled,
      children,
      className = "",
      type = "button",
      onClick,
      ...props
    },
    ref
  ) => {
    const isDisabled = disabled || loading;

    return (
      <motion.button
        ref={ref}
        type={type}
        className={`${styles.button} ${styles[variant]} ${styles[size]} ${className}`}
        disabled={isDisabled}
        whileHover={isDisabled ? undefined : { scale: 1.02 }}
        whileTap={isDisabled ? undefined : { scale: 0.98 }}
        transition={{ type: "spring", stiffness: 300, damping: 24 }}
        onClick={onClick}
        aria-label={props["aria-label"]}
      >
        {loading && (
          <Loader2 className={styles.spinner} size={size === "sm" ? 14 : 16} />
        )}
        {!loading && icon && iconPosition === "left" && (
          <span className={styles.icon}>{icon}</span>
        )}
        {children && <span className={styles.label}>{children}</span>}
        {!loading && icon && iconPosition === "right" && (
          <span className={styles.icon}>{icon}</span>
        )}
      </motion.button>
    );
  }
);

Button.displayName = "Button";

export { Button };
