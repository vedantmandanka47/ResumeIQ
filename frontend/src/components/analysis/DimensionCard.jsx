import Card from '../common/Card';

export default function DimensionCard({ name, score, verdict, finding }) {
  const getScoreColor = (s) => {
    if (s >= 70) return 'var(--score-high)';
    if (s >= 40) return 'var(--score-mid)';
    return 'var(--score-low)';
  };

  return (
    <Card className="dimension-card">
      <div className="dimension-card__header">
        <span className="label">{name}</span>
        <span className="dimension-card__score">{score}</span>
      </div>
      
      <div className="dimension-card__bar-track">
        <div 
          className="dimension-card__bar-fill" 
          style={{ 
            width: `${score}%`, 
            backgroundColor: getScoreColor(score) 
          }} 
        />
      </div>

      <div className="dimension-card__content">
        <p className="dimension-card__verdict">{verdict}</p>
        <p className="dimension-card__finding">{finding}</p>
      </div>
    </Card>
  );
}
