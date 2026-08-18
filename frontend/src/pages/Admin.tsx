import React, { useCallback, useEffect, useState } from 'react';
import client from '../api/client';
import '../components/DataTable.css';
import { StatsRow, StatTile } from '../components/StatsRow';
import { Topbar } from '../components/Topbar';
import { AdminOverviewResponse } from '../types/admin';

function formatDate(isoString: string): string {
  return new Date(isoString).toLocaleDateString();
}

export function Admin() {
  const [overview, setOverview] = useState<AdminOverviewResponse | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  const loadOverview = useCallback(async () => {
    setLoadError(null);
    try {
      const response = await client.get<AdminOverviewResponse>('/api/admin/overview');
      setOverview(response.data);
    } catch (err) {
      console.error('Failed to load admin overview:', err);
      setLoadError('Could not load the platform overview.');
    }
  }, []);

  useEffect(() => {
    loadOverview();
  }, [loadOverview]);

  return (
    <div className="page admin">
      <Topbar title="Admin Overview" />

      {loadError && <p className="status-message status-message--error">{loadError}</p>}

      {!loadError && overview === null && (
        <div className="content-loading">
          <p className="status-message">Loading overview&hellip;</p>
        </div>
      )}

      {!loadError && overview !== null && (
        <>
          <StatsRow>
            <StatTile value={overview.total_users} label="Total users" />
            <StatTile value={overview.role_counts.learner ?? 0} label="Learners" />
            <StatTile value={overview.total_practice_attempts} label="Practice attempts" />
            <StatTile
              variant="accent"
              value={
                <>
                  {overview.overall_accuracy_percent ?? '—'}
                  {overview.overall_accuracy_percent !== null && <span className="stat-tile__unit">%</span>}
                </>
              }
              label="Platform accuracy"
            />
          </StatsRow>

          <section className="admin-users">
            {overview.users.length === 0 ? (
              <p className="status-message">No users yet.</p>
            ) : (
              <div className="data-table-wrap">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Email</th>
                      <th>Role</th>
                      <th>Joined</th>
                      <th>Attempts</th>
                    </tr>
                  </thead>
                  <tbody>
                    {overview.users.map((user) => (
                      <tr key={user.id}>
                        <td>{user.name}</td>
                        <td>{user.email}</td>
                        <td>{user.role}</td>
                        <td className="data-table__numeric">{formatDate(user.created_at)}</td>
                        <td className="data-table__numeric">
                          {user.total_attempts === null ? '—' : user.total_attempts}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </>
      )}
    </div>
  );
}
