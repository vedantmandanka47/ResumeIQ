import { NavLink } from 'react-router-dom'
import './Navbar.css'

export default function Navbar() {
  return (
    <nav className="navbar glass" role="navigation" aria-label="Main navigation">
      <div className="container navbar__inner">
        {/* Brand */}
        <NavLink to="/" className="navbar__brand" aria-label="ResumeIQ home">
          <span className="navbar__logo" aria-hidden="true">✦</span>
          <span className="navbar__name">ResumeIQ</span>
        </NavLink>

        {/* Links */}
        <ul className="navbar__links" role="list">
          <li>
            <NavLink
              to="/status"
              id="nav-status"
              className={({ isActive }) =>
                `navbar__link ${isActive ? 'navbar__link--active' : ''}`
              }
            >
              System Status
            </NavLink>
          </li>
          {/* Future nav items added per phase */}
          <li>
            <NavLink
              to="/upload"
              id="nav-upload"
              className={({ isActive }) =>
                `navbar__link ${isActive ? 'navbar__link--active' : ''}`
              }
            >
              Analyse Resume
            </NavLink>
          </li>
        </ul>

        {/* CTA */}
        <NavLink to="/upload" className="btn btn-primary navbar__cta" id="nav-cta">
          Get Started
        </NavLink>
      </div>
    </nav>
  )
}
