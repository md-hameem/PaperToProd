'use client';

import { useEffect, useRef } from 'react';
import Link from 'next/link';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { Hero3D } from '@/components/landing/Hero3D';
import styles from './landing.module.css';

gsap.registerPlugin(ScrollTrigger);

export default function LandingPage() {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      // Animate the steps
      const steps = gsap.utils.toArray('.' + styles.step);
      steps.forEach((step: any, i: number) => {
        gsap.from(step, {
          scrollTrigger: {
            trigger: step,
            start: "top 80%",
            toggleActions: "play none none reverse"
          },
          y: 50,
          opacity: 0,
          duration: 0.8,
          ease: "power3.out"
        });
      });
    }, scrollRef);

    return () => ctx.revert();
  }, []);

  return (
    <div className={styles.container} ref={scrollRef}>
      {/* Hero Section */}
      <section className={styles.heroSection}>
        <Hero3D />
        <div className={styles.heroContent}>
          <h1 className={styles.heroHeadline}>Research Paper → Running Code</h1>
          <p className={styles.heroSubheadline}>
            Stop wrestling with unmaintained research code. PaperToProd uses an autonomous multi-agent pipeline to reproduce any arXiv paper into a clean, verified, production-ready repository.
          </p>
          <Link href="/login" className={styles.heroCTA}>
            Try it free
          </Link>
        </div>
      </section>

      {/* Live Proof Strip */}
      <section className={styles.liveProofStrip}>
        <div className={styles.marquee}>
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className={styles.proofCard}>
              <span>Attention Is All You Need</span>
              <span className={styles.proofScore}>98% Fidelity</span>
            </div>
          ))}
          {/* Duplicate for infinite scroll */}
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={`dup-${i}`} className={styles.proofCard}>
              <span>Attention Is All You Need</span>
              <span className={styles.proofScore}>98% Fidelity</span>
            </div>
          ))}
        </div>
      </section>

      {/* How it Works (GSAP Storytelling) */}
      <section className={styles.howItWorks}>
        <h2 className={styles.sectionTitle}>How it works</h2>
        <div className={styles.stepContainer}>
          <div className={styles.step}>
            <div className={styles.stepText}>
              <h3>1. Understand</h3>
              <p>Our agents deeply analyze the paper's methodology, mathematics, and architecture to extract a deterministic specification.</p>
            </div>
            <div className={styles.stepVisual}>
              <div>📊 Math Parsing & Extraction</div>
            </div>
          </div>

          <div className={styles.step}>
            <div className={styles.stepText}>
              <h3>2. Build</h3>
              <p>A LangGraph-orchestrated scaffold generates modern PyTorch code, implementing the architecture with precision.</p>
            </div>
            <div className={styles.stepVisual}>
              <div>💻 Code Generation</div>
            </div>
          </div>

          <div className={styles.step}>
            <div className={styles.stepText}>
              <h3>3. Verify</h3>
              <p>The code is deployed to isolated GPU instances to run validation loops until fidelity benchmarks are met.</p>
            </div>
            <div className={styles.stepVisual}>
              <div>✅ GPU Validation & Self-Repair</div>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing Summary */}
      <section className={styles.pricing}>
        <h2 className={styles.sectionTitle}>Simple Pricing</h2>
        <div className={styles.pricingCards}>
          <div className={styles.pricingCard}>
            <h3>Starter</h3>
            <div className={styles.price}>$49<span>/mo</span></div>
            <ul className={styles.pricingFeatures}>
              <li>✓ 10 reproductions per month</li>
              <li>✓ Standard GPU validation</li>
              <li>✓ Public repositories</li>
            </ul>
            <Link href="/login" className={styles.heroCTA}>Get Started</Link>
          </div>
          <div className={styles.pricingCard}>
            <h3>Enterprise</h3>
            <div className={styles.price}>Custom</div>
            <ul className={styles.pricingFeatures}>
              <li>✓ Unlimited reproductions</li>
              <li>✓ BYO LLM API Keys</li>
              <li>✓ SOC 2 Compliant</li>
              <li>✓ Private VPC deployments</li>
            </ul>
            <Link href="/login" className={styles.heroCTA}>Contact Sales</Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className={styles.footer}>
        <p>&copy; 2026 PaperToProd. All rights reserved.</p>
      </footer>
    </div>
  );
}
