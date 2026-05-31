export default function StrengthsList({ strengths }) {
  if (!strengths || strengths.length === 0) return null;

  return (
    <div className="strengths-section">
      <h3 className="label">Strengths</h3>
      <div className="strengths-list">
        {strengths.map((strength, idx) => (
          <div key={idx} className="strength-item">
            {strength}
          </div>
        ))}
      </div>
    </div>
  );
}
