export default function BenchmarkChart({ benchmark, userDimensions }) {
  if (!benchmark || !userDimensions) return null;

  return (
    <div className="benchmark-chart">
      <div className="benchmark-chart__header">
        <h3 className="label">Benchmark vs. {benchmark.total_resumes_analyzed} Resumes</h3>
        <div className="benchmark-chart__legend">
          <div className="legend-item">
            <span className="legend-box legend-box--user" />
            <span className="text-sm">You</span>
          </div>
          <div className="legend-item">
            <span className="legend-box legend-box--average" />
            <span className="text-sm">Average across {benchmark.total_resumes_analyzed} resumes</span>
          </div>
        </div>
      </div>

      <div className="benchmark-chart__rows">
        {userDimensions.map((dim, idx) => {
          const avgDim = benchmark.dimension_averages.find(d => d.name === dim.name);
          const avgScore = avgDim ? avgDim.average_score : 50; // Fallback
          
          const getUserColor = (s) => {
            if (s >= 70) return 'var(--score-high)';
            if (s >= 40) return 'var(--score-mid)';
            return 'var(--score-low)';
          };

          return (
            <div key={idx} className="benchmark-row">
              <span className="benchmark-row__label label">{dim.name}</span>
              <div className="benchmark-row__bars">
                {/* Average Bar */}
                <div 
                  className="benchmark-bar benchmark-bar--average"
                  style={{ width: `${avgScore}%` }}
                />
                {/* User Bar */}
                <div 
                  className="benchmark-bar benchmark-bar--user"
                  style={{ 
                    width: `${dim.score}%`,
                    backgroundColor: getUserColor(dim.score)
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
