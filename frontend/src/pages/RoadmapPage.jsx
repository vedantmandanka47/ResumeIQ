import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { useAnalysis } from '../hooks/useAnalysis';

import RoadmapTimeline from '../components/roadmap/RoadmapTimeline';
import Button from '../components/common/Button';
import Spinner from '../components/common/Spinner';
import ErrorBlock from '../components/common/ErrorBlock';

import './RoadmapPage.css';

export default function RoadmapPage() {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const { roadmapResult, setRoadmapResult } = useAnalysis();

  const [isLoading, setIsLoading] = useState(!roadmapResult);
  const [error, setError] = useState(null);

  const fetchRoadmap = useCallback(async () => {
    if (roadmapResult) return;
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.resume.roadmap(sessionId);
      setRoadmapResult(data);
    } catch (err) {
      setError(err);
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, roadmapResult, setRoadmapResult]);

  useEffect(() => {
    fetchRoadmap();
  }, [fetchRoadmap]);

  if (isLoading) {
    return (
      <div className="page roadmap-page loading-state">
        <Spinner size={32} />
        <p className="text-secondary mt-4">Mapping out your 6-month skill progression...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page roadmap-page container">
        <ErrorBlock
          message={typeof error === 'string' ? error : error.message}
          retryAfter={error?.retryAfter}
          onRetry={fetchRoadmap}
        />
      </div>
    );
  }

  if (!roadmapResult) return null;

  return (
    <div className="page roadmap-page">
      <div className="container">
        
        <div className="roadmap-header">
          <h1 className="text-3xl">6-Month Roadmap</h1>
          <p className="text-secondary text-base">
            Strategic steps to elevate your profile from {roadmapResult.current_level} to {roadmapResult.target_level}.
          </p>
        </div>

        <div className="roadmap-content">
          <RoadmapTimeline tasks={roadmapResult.roadmap} />
        </div>

        <div className="action-row mt-12 pt-8 border-t">
          <Button onClick={() => navigate(`/analysis/${sessionId}`)}>
            &larr; Back to Analysis
          </Button>
        </div>

      </div>
    </div>
  );
}
