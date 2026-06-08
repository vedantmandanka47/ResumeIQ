import { useEffect, useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import './Navbar.css';

const WORKFLOW_STEPS = [
  { path: '/',             label: 'Upload'   },
  { path: '/analysis',     label: 'Analyse'  },
  { path: '/rewrite',      label: 'Rewrite'  },
  { path: '/generate',     label: 'Generate' },
];

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const location = useLocation();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const activeStepIdx = WORKFLOW_STEPS.findIndex(
    (s) => s.path !== '/' && location.pathname.startsWith(s.path)
  );
  const showStepper = activeStepIdx >= 0 || location.pathname === '/';

  return (
    <nav className={`navbar${scrolled ? ' navbar--scrolled' : ''}`} role="navigation">
      <div className="container container--wide navbar__inner">
        <NavLink to="/" className="navbar__brand">
          <span className="navbar__logo">ResumeIQ</span>
        </NavLink>

        {showStepper && (
          <div className="navbar__stepper" aria-label="Workflow steps">
            {WORKFLOW_STEPS.map((step, idx) => {
              const currentIdx = location.pathname === '/'
                ? 0
                : activeStepIdx;
              const isActive   = idx === currentIdx;
              const isDone     = idx < currentIdx;
              return (
                <span
                  key={step.path}
                  className={`stepper-dot${isActive ? ' stepper-dot--active' : ''}${isDone ? ' stepper-dot--done' : ''}`}
                  title={step.label}
                  aria-current={isActive ? 'step' : undefined}
                >
                  {isDone ? '✓' : step.label}
                </span>
              );
            })}
          </div>
        )}

        <ul className="navbar__links" role="list">
          <li>
            <NavLink to="/status" className={({ isActive }) => `navbar__link ${isActive ? 'navbar__link--active' : ''}`}>
              Status
            </NavLink>
          </li>
        </ul>
      </div>
    </nav>
  );
}
