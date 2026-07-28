/**
 * Motion configuration — Spring presets from Doc 05
 *
 * Usage with Framer Motion:
 *   <motion.div transition={springs.snappy} />
 */

export const springs = {
  /** Interactive elements: toggles, checkboxes, button presses */
  snappy: { type: "spring" as const, stiffness: 300, damping: 24 },

  /** Layout shifts, progress bars, settling animations */
  settle: { type: "spring" as const, stiffness: 200, damping: 28 },

  /** Pipeline node state transitions (agent active/complete/failed) */
  pipeline: { type: "spring" as const, stiffness: 180, damping: 20 },

  /** Completion celebration, confetti-adjacent */
  celebration: { type: "spring" as const, stiffness: 260, damping: 18 },
} as const;

export const durations = {
  instant: 0.1,
  fast: 0.15,
  normal: 0.25,
  slow: 0.4,
  pipeline: 0.45,
} as const;

export const easings = {
  out: [0.16, 1, 0.3, 1] as const,
  inOut: [0.45, 0, 0.55, 1] as const,
  spring: [0.34, 1.56, 0.64, 1] as const,
} as const;

/**
 * Stagger children animations by 20ms per item
 * Usage: <motion.div variants={staggerContainer} initial="hidden" animate="visible">
 */
export const staggerContainer = {
  hidden: {},
  visible: {
    transition: {
      staggerChildren: 0.02,
    },
  },
} as const;

export const fadeInUp = {
  hidden: { opacity: 0, y: 8 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: durations.normal, ease: easings.out },
  },
} as const;

export const fadeIn = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { duration: durations.normal },
  },
} as const;

/**
 * Screen-level transition: cross-fade + 8px vertical slide, 300ms (Doc 05 §21)
 */
export const pageTransition = {
  initial: { opacity: 0, y: 8 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -8 },
  transition: { duration: 0.3, ease: easings.inOut },
} as const;
