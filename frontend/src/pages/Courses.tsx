import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import client from '../api/client';
import { useAuth } from '../auth/AuthContext';
import { Topbar } from '../components/Topbar';
import { AnimatedProgressBar } from '../components/AnimatedProgressBar';
import { CourseItem } from '../types/courses';
import './Courses.css';

export function Courses() {
  const { user } = useAuth();
  const [courses, setCourses] = useState<CourseItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const loadCourses = useCallback(async () => {
    if (!user) return;
    setLoading(true);
    setLoadError(null);
    try {
      const response = await client.get<{ courses: CourseItem[] }>(`/api/learner/${user.id}/courses`);
      setCourses(response.data.courses);
    } catch (err) {
      console.error('Failed to load courses:', err);
      setLoadError('Could not load courses.');
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    loadCourses();
  }, [loadCourses]);

  if (loading) {
    return (
      <div className="page courses">
        <Topbar title="Courses" />
        <div className="content-loading">
          <p className="status-message">Loading courses&hellip;</p>
        </div>
      </div>
    );
  }

  if (loadError) {
    return (
      <div className="page courses">
        <Topbar title="Courses" />
        <p className="status-message status-message--error">{loadError}</p>
      </div>
    );
  }

  return (
    <div className="page courses">
      <Topbar title="Courses" />

      <div className="course-grid">
        {courses.map((course) => (
          <div key={course.id} className={`course-card${!course.built ? ' course-card--locked' : ''}`}>
            <span className="course-card__category">{course.category}</span>
            <h2 className="course-card__title">{course.title}</h2>
            <p className="course-card__description">{course.description}</p>

            {course.built && course.tracks_progress && course.progress_percent !== null && (
              <div className="course-card__progress">
                <div className="course-card__progress-track">
                  <AnimatedProgressBar
                    percent={course.progress_percent}
                    className="course-card__progress-fill"
                  />
                </div>
                <span className="course-card__progress-label">{course.progress_percent}% complete</span>
              </div>
            )}

            {course.built && !course.tracks_progress && course.item_count !== null && (
              <span className="course-card__meta">{course.item_count} signs</span>
            )}

            {!course.built && course.locked_reason && (
              <span className="course-card__locked-reason">{course.locked_reason}</span>
            )}

            {course.built && course.route ? (
              <Link to={course.route} className="btn course-card__action">
                Open
              </Link>
            ) : (
              <button className="btn btn--ghost course-card__action" disabled>
                Not yet available
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
