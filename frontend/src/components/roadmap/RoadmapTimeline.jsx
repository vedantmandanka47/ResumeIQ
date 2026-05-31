export default function RoadmapTimeline({ tasks }) {
  if (!tasks || tasks.length === 0) return null;

  return (
    <div className="roadmap-timeline">
      {tasks.map((task, idx) => (
        <div key={idx} className="timeline-item">
          <div className="timeline-item__marker">
            <span className="timeline-item__dot" />
            {idx < tasks.length - 1 && <span className="timeline-item__line" />}
          </div>
          <div className="timeline-item__content">
            <div className="timeline-item__header">
              <span className="timeline-item__timeframe label">{task.timeframe}</span>
            </div>
            <h4 className="timeline-item__title">{task.task}</h4>
            <p className="timeline-item__desc">{task.description}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
