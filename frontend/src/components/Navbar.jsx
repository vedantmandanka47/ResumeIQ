import { NavLink } from 'react-router-dom';
import './Navbar.css';

export default function Navbar() {
  return (
    <nav className="navbar" role="navigation" aria-label="Main navigation">
      <div className="container container--wide navbar__inner">
        {/* Brand */}
        <NavLink to="/" className="navbar__brand" aria-label="ResumeIQ home">
          {/* We'll use a text-based logo since Logo.svg is a complex file */}
          <span className="navbar__logo">ResumeIQ</span>
        </NavLink>

        {/* Links */}
        <ul className="navbar__links" role="list">
          <li>
            <NavLink
              to="/status"
              className={({ isActive }) => `navbar__link ${isActive ? 'navbar__link--active' : ''}`}
            >
              System Status
            </NavLink>
          </li>
          <li>
            <NavLink
              to="/"
              className={({ isActive }) => `navbar__link ${isActive ? 'navbar__link--active' : ''}`}
            >
              Analyze Resume
            </NavLink>
          </li>
        </ul>
      </div>
    </nav>
  );
}
