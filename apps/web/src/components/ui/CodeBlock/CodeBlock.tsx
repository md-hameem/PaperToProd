"use client";

import { useState } from "react";
import { Check, Copy } from "lucide-react";
import styles from "./CodeBlock.module.css";

export interface CodeBlockProps {
  code: string;
  language?: string;
  filename?: string;
  showLineNumbers?: boolean;
  maxHeight?: string;
  className?: string;
}

export function CodeBlock({
  code,
  language = "text",
  filename,
  showLineNumbers = true,
  maxHeight = "400px",
  className = "",
}: CodeBlockProps) {
  const [copied, setCopied] = useState(false);
  const lines = code.split("\n");

  const handleCopy = async () => {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className={`${styles.wrapper} ${className}`}>
      {(filename || language) && (
        <div className={styles.header}>
          <span className={styles.filename}>
            {filename || language}
          </span>
          <button
            className={styles.copyBtn}
            onClick={handleCopy}
            aria-label={copied ? "Copied" : "Copy code"}
          >
            {copied ? <Check size={14} /> : <Copy size={14} />}
            <span>{copied ? "Copied!" : "Copy"}</span>
          </button>
        </div>
      )}
      <pre className={styles.pre} style={{ maxHeight }}>
        <code className={styles.code}>
          {lines.map((line, i) => (
            <span key={i} className={styles.line}>
              {showLineNumbers && (
                <span className={styles.lineNumber}>{i + 1}</span>
              )}
              <span className={styles.lineContent}>{line || " "}</span>
            </span>
          ))}
        </code>
      </pre>
    </div>
  );
}
