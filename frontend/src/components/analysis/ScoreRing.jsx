import { useEffect, useState } from 'react';
import Badge from '../common/Badge';

export default function ScoreRing({ score, mode, delta = null }) {
  const [displayScore, setDisplayScore] = useState(0);

  const radius = 56;
  const stroke = 8;
  const normalizedRadius = radius - stroke * 2;
  const circumference = normalizedRadius * 2 * Math.PI;

  const getScoreColor = (s) => {
    if (s >= 70) return 'var(--score-high)';
    if (s >= 40) return 'var(--score-mid)';
    return 'var(--score-low)';
  };

  // Count-up animation
  useEffect(() => {
    if (score == null) return;
    let start = null;
    const duration = 900;

    const step = (timestamp) => {
      if (!start) start = timestamp;
      const progress = Math.min((timestamp - start) / duration, 1);
      // Ease out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplayScore(Math.round(eased * score));
      if (progress < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }, [score]);

  const targetOffset = circumference - (score / 100) * circumference;
  const color = getScoreColor(score);

  return (
    <div className="score-ring-container">
      <div className="score-ring">
        <svg
          height={radius * 2}
          width={radius * 2}
          style={{
            '--ring-circumference': circumference,
            '--ring-target-offset': targetOffset,
          }}
        >
          {/* Background track */}
          <circle
            stroke="var(--border-subtle)"
            fill="transparent"
            strokeWidth={stroke}
            r={normalizedRadius}
            cx={radius}
            cy={radius}
          />
          {/* Animated fill */}
          <circle
            className="score-ring__fill"
            stroke={color}
            fill="transparent"
            strokeWidth={stroke}
            strokeDasharray={`${circumference} ${circumference}`}
            style={{ strokeDashoffset: circumference }}  // starts empty; CSS animates to target
            strokeLinecap="round"
            r={normalizedRadius}
            cx={radius}
            cy={radius}
            transform={`rotate(-90 ${radius} ${radius})`}
          />
        </svg>

        <div className="score-ring__content">
          <span className="score-ring__value" style={{ fontVariantNumeric: 'tabular-nums' }}>
            {displayScore}
          </span>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 8, flexWrap: 'wrap', justifyContent: 'center' }}>
        {mode && (
          <Badge variant="idle" className="score-ring__mode">
            {mode.toUpperCase()}
          </Badge>
        )}
        {delta != null && (
          <span className={`score-delta score-delta--${delta > 0 ? 'positive' : delta < 0 ? 'negative' : 'neutral'}`}>
            {delta > 0 ? `+${delta}` : delta}
          </span>
        )}
      </div>
    </div>
  );
}
