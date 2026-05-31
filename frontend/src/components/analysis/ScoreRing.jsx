import Badge from '../common/Badge';

export default function ScoreRing({ score, mode }) {
  const getScoreColor = (s) => {
    if (s >= 70) return 'var(--score-high)';
    if (s >= 40) return 'var(--score-mid)';
    return 'var(--score-low)';
  };

  const radius = 56;
  const stroke = 8;
  const normalizedRadius = radius - stroke * 2;
  const circumference = normalizedRadius * 2 * Math.PI;
  const strokeDashoffset = circumference - (score / 100) * circumference;
  
  const color = getScoreColor(score);

  return (
    <div className="score-ring-container">
      <div className="score-ring">
        <svg height={radius * 2} width={radius * 2}>
          {/* Background Ring */}
          <circle
            stroke="var(--border-subtle)"
            fill="transparent"
            strokeWidth={stroke}
            r={normalizedRadius}
            cx={radius}
            cy={radius}
          />
          {/* Fill Ring */}
          <circle
            stroke={color}
            fill="transparent"
            strokeWidth={stroke}
            strokeDasharray={circumference + ' ' + circumference}
            style={{ strokeDashoffset }}
            strokeLinecap="round"
            r={normalizedRadius}
            cx={radius}
            cy={radius}
            transform={`rotate(-90 ${radius} ${radius})`}
          />
        </svg>
        <div className="score-ring__content">
          <span className="score-ring__value">{score}</span>
        </div>
      </div>
      {mode && (
        <Badge variant="idle" className="score-ring__mode">
          {mode.toUpperCase()}
        </Badge>
      )}
    </div>
  );
}
