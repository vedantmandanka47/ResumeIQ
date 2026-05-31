export default function SignalsPanel({ signals }) {
  if (!signals) return null;

  return (
    <div className="signals-panel">
      <div className="signals-row">
        <span className="label">Skills They Hire For</span>
        <div className="signals-chips">
          {signals.key_skills_they_hire_for?.map((skill, idx) => (
            <span key={idx} className="signal-chip">{skill}</span>
          ))}
        </div>
      </div>
      <div className="signals-row">
        <span className="label">Culture</span>
        <div className="signals-chips">
          {signals.culture_keywords?.map((word, idx) => (
            <span key={idx} className="signal-chip">{word}</span>
          ))}
        </div>
      </div>
    </div>
  );
}
