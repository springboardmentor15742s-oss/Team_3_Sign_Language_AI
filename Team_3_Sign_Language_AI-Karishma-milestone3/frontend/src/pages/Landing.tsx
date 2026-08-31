import React, { useEffect, useState } from 'react';
import { Link, NavLink } from 'react-router-dom';
import client from '../api/client';
import { useAuth } from '../auth/AuthContext';
import { ADMIN_ROLES, INSTRUCTOR_ROLES } from '../auth/roles';
import { AnimatedNumber } from '../components/AnimatedNumber';
import './Landing.css';

// A-Z — stable by definition, unlike the sign/gesture counts below, which
// are fetched live so this page can never drift out of sync with what the
// backend actually supports (see /api/common-signs/supported,
// /api/motion-signs/supported).
const ALPHABET_LETTER_COUNT = 26;

interface FeatureCard {
  eyebrow: string;
  title: string;
  description: string;
  status: 'built' | 'locked';
  meta: string;
  route: string | null;
}

function homeRouteFor(role: string): string {
  if (ADMIN_ROLES.includes(role)) return '/admin';
  if (INSTRUCTOR_ROLES.includes(role)) return '/instructor';
  return '/dashboard';
}

const GUEST_NAV_LINKS = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/practice', label: 'Practice' },
  { to: '/common-signs', label: 'Common Signs' },
  { to: '/motion-signs', label: 'Everyday Gestures' },
  { to: '/courses', label: 'Courses' },
];

const ROLE_NAV_LINKS: Record<string, { to: string; label: string }[]> = {
  learner: GUEST_NAV_LINKS,
  instructor: [{ to: '/instructor', label: 'Roster' }],
  admin: [{ to: '/admin', label: 'Overview' }],
};

const STEPS = [
  {
    title: 'Your camera, tracked live',
    text: 'MediaPipe finds 21 hand landmarks per frame from your webcam feed — no server-side video storage, just coordinates.',
  },
  {
    title: 'Classified or rule-tested',
    text: 'A trained SVM classifies alphabet handshapes; rule-based geometry checks common signs and gesture trajectories — each honestly labeled as which one it is.',
  },
  {
    title: 'Instant, specific feedback',
    text: 'Pass, fail, or “no hand detected” — never a guess dressed up as a result.',
  },
  {
    title: 'Progress that’s actually yours',
    text: 'Streaks, accuracy trends, and achievements are all computed from your real attempt history — zero attempts shows as zero, not a placeholder.',
  },
];

function LandingNav() {
  const { user, logout } = useAuth();
  const navLinks = user ? ROLE_NAV_LINKS[user.role] ?? GUEST_NAV_LINKS : GUEST_NAV_LINKS;

  return (
    <header className="landing-nav">
      <Link to="/" className="landing-nav__brand">
        <span className="landing-nav__brand-eyebrow">Sign Language Platform</span>
        <span className="landing-nav__brand-name">SignAI</span>
      </Link>

      <nav className="landing-nav__links">
        {navLinks.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            className={({ isActive }) => `landing-nav__link${isActive ? ' landing-nav__link--active' : ''}`}
          >
            {link.label}
          </NavLink>
        ))}
      </nav>

      <div className="landing-nav__actions">
        {user ? (
          <>
            <span className="landing-nav__email">{user.email}</span>
            <Link className="btn btn--ghost" to={homeRouteFor(user.role)}>
              Go to Dashboard
            </Link>
            <button className="btn btn--ghost" onClick={logout}>
              Log out
            </button>
          </>
        ) : (
          <>
            <Link className="btn btn--ghost" to="/login">
              Log in
            </Link>
            <Link className="btn" to="/register">
              Get started
            </Link>
          </>
        )}
      </div>
    </header>
  );
}

export function Landing() {
  const { user } = useAuth();
  // null = not fetched yet. Kept separate from "fetched empty" so the
  // hero stat and feature-card meta text can tell "still loading" apart
  // from "genuinely zero" — same null-vs-zero discipline the rest of the
  // app uses for real attempt data, applied here to platform capability
  // data instead.
  const [commonSigns, setCommonSigns] = useState<string[] | null>(null);
  const [motionSigns, setMotionSigns] = useState<string[] | null>(null);

  useEffect(() => {
    client
      .get<{ signs: string[] }>('/api/common-signs/supported')
      .then((res) => setCommonSigns(res.data.signs))
      .catch((err) => {
        console.error('Failed to load supported common signs:', err);
        setCommonSigns([]);
      });
    client
      .get<{ signs: string[] }>('/api/motion-signs/supported')
      .then((res) => setMotionSigns(res.data.signs))
      .catch((err) => {
        console.error('Failed to load supported motion signs:', err);
        setMotionSigns([]);
      });
  }, []);

  const primaryCta = user
    ? { to: homeRouteFor(user.role), label: 'Go to Dashboard' }
    : { to: '/register', label: 'Get started free' };

  const features: FeatureCard[] = [
    {
      eyebrow: 'Beginner · Real, trained model',
      title: 'ASL Alphabet Fundamentals',
      description:
        'Sign a letter at your camera and a MediaPipe hand-landmark pipeline feeds a trained classifier for instant pass/fail feedback, with a recommendation engine that adapts what you practice next.',
      status: 'built',
      meta: `${ALPHABET_LETTER_COUNT} letters, real accuracy tracking`,
      route: '/practice',
    },
    {
      eyebrow: 'Everyday Communication · Rule-based',
      title: 'Common Signs',
      description:
        'A small set of genuine static-handshape signs, recognized with explicit hand-landmark geometry rather than a trained model — a standalone tester, not scored into your stats.',
      status: 'built',
      meta: commonSigns === null ? 'Loading…' : commonSigns.length > 0 ? commonSigns.join(', ') : 'None available',
      route: '/common-signs',
    },
    {
      eyebrow: 'Everyday Communication · Rule-based motion',
      title: 'Everyday Gestures',
      description:
        "This platform's first motion recognizer: gestures are detected from real hand-trajectory geometry across a short video clip, not a single still frame — and it's attempt-tracked, with real progress.",
      status: 'built',
      meta: motionSigns === null ? 'Loading…' : motionSigns.length > 0 ? motionSigns.join(', ') : 'None available',
      route: '/motion-signs',
    },
    {
      eyebrow: 'Intermediate & Professional Sign Language',
      title: 'Conversational Fluency & Workplace Communication',
      description:
        'Full-word and motion-based conversational signing, plus workplace-specific vocabulary. Both need a real downloaded video-sign dataset and a trained temporal model for the full ASL vocabulary — not built yet.',
      status: 'locked',
      meta: 'Not yet available',
      route: null,
    },
  ];

  return (
    <div className="page landing">
      <LandingNav />

      <section className="landing-hero">
        <span className="landing-hero__eyebrow">AI-assisted sign language practice</span>
        <h1 className="landing-hero__heading">Learn sign language with real-time feedback from your camera.</h1>
        <p className="landing-hero__subheading">
          Practice ASL fingerspelling against a trained classifier, try genuine static signs and everyday
          motion gestures with rule-based hand-landmark geometry, and track real progress &mdash; no
          fabricated capabilities, no invented stats.
        </p>
        <div className="landing-hero__actions">
          <Link className="btn landing-hero__cta" to={primaryCta.to}>
            {primaryCta.label}
          </Link>
          {!user && (
            <Link className="btn btn--ghost" to="/login">
              I already have an account
            </Link>
          )}
        </div>

        <div className="landing-hero__stats">
          <div className="landing-stat">
            <span className="landing-stat__value">
              <AnimatedNumber value={ALPHABET_LETTER_COUNT} />
            </span>
            <span className="landing-stat__label">ASL letters trained</span>
          </div>
          <div className="landing-stat">
            <span className="landing-stat__value">
              <AnimatedNumber value={commonSigns?.length ?? 0} />
            </span>
            <span className="landing-stat__label">common signs, rule-based</span>
          </div>
          <div className="landing-stat">
            <span className="landing-stat__value">
              <AnimatedNumber value={motionSigns?.length ?? 0} />
            </span>
            <span className="landing-stat__label">motion gestures, hand-trajectory geometry</span>
          </div>
        </div>
      </section>

      <section className="landing-section">
        <h2 className="landing-section__title">What&rsquo;s actually built</h2>
        <p className="landing-section__lead">
          Every card below is either real and working today, or plainly marked as not built yet &mdash; the
          same honest split you&rsquo;ll see on the Courses page once you&rsquo;re in.
        </p>
        <div className="landing-feature-grid">
          {features.map((feature) => (
            <div
              key={feature.title}
              className={`landing-feature-card${feature.status === 'locked' ? ' landing-feature-card--locked' : ''}`}
            >
              <span className="landing-feature-card__eyebrow">{feature.eyebrow}</span>
              <h3 className="landing-feature-card__title">{feature.title}</h3>
              <p className="landing-feature-card__description">{feature.description}</p>
              <span className="landing-feature-card__meta">{feature.meta}</span>
              {feature.status === 'built' && feature.route ? (
                <Link className="btn btn--ghost landing-feature-card__action" to={feature.route}>
                  Try it
                </Link>
              ) : (
                <span className="landing-feature-card__locked-tag">Not yet available</span>
              )}
            </div>
          ))}
        </div>
      </section>

      <section className="landing-section">
        <h2 className="landing-section__title">How it works</h2>
        <div className="landing-steps">
          {STEPS.map((step, i) => (
            <div key={step.title} className="landing-step">
              <span className="landing-step__index">{String(i + 1).padStart(2, '0')}</span>
              <h3 className="landing-step__title">{step.title}</h3>
              <p className="landing-step__text">{step.text}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="landing-cta">
        <h2 className="landing-cta__heading">
          {user ? 'Pick up where you left off.' : 'Ready to see your hand shape scored honestly?'}
        </h2>
        <Link className="btn landing-cta__action" to={primaryCta.to}>
          {primaryCta.label}
        </Link>
      </section>

      <footer className="landing-footer">
        <span>Sign Language Learning &amp; Assessment Platform</span>
      </footer>
    </div>
  );
}
