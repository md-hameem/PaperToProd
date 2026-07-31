'use client';

import { motion } from 'framer-motion';
import { GithubAuthButton, GoogleAuthButton } from '@/components/AuthButtons';
import styles from './login.module.css';

export default function LoginPage() {
  return (
    <div className={styles.container}>
      {/* Background ambient light effects */}
      <div className={styles.ambientLight1} />
      <div className={styles.ambientLight2} />

      <motion.div
        className={styles.cardWrapper}
        initial={{ opacity: 0, y: 20, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
      >
        <div className={`glass ${styles.card}`}>
          <div className={styles.header}>
            <h1 className={styles.title}>PaperToProd</h1>
            <p className={styles.subtitle}>
              Transform academic research into production-ready code.
            </p>
          </div>

          <div className={styles.authContainer}>
            <GithubAuthButton />
            <GoogleAuthButton />
          </div>

          <div className={styles.footer}>
            By continuing, you agree to our Terms of Service and Privacy Policy.
          </div>
        </div>
      </motion.div>
    </div>
  );
}
