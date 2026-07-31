'use client';

import { useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { saveToken } from '@/lib/api';
import styles from './callback.module.css';

function CallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    // The FastAPI backend redirect will append ?token=... to the URL.
    const token = searchParams.get('token');

    if (token) {
      saveToken(token);
      // For MVP, redirect straight to job submission page (root or dashboard).
      // If we had a dashboard, we'd check if first-time user.
      router.replace('/');
    } else {
      // If no token, redirect back to login
      router.replace('/login');
    }
  }, [searchParams, router]);

  return (
    <div className={styles.container}>
      <div className={styles.spinner}></div>
      <p className={styles.text}>Authenticating...</p>
    </div>
  );
}

export default function AuthCallbackPage() {
  return (
    <Suspense fallback={
      <div className={styles.container}>
        <div className={styles.spinner}></div>
      </div>
    }>
      <CallbackContent />
    </Suspense>
  );
}
