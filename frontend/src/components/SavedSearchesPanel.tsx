import React, { useEffect, useState } from 'react';
import { useSavedSearches } from '../hooks/useSavedSearches';
import { SavedSearchCreate } from '../api/saved-searches';

export const SavedSearchesPanel: React.FC = () => {
  const {
    searches,
    selectedSearch,
    loading,
    error,
    fetchSearches,
    createSearch,
    deleteSearch,
    toggleNotifications,
    selectSearch,
  } = useSavedSearches();

  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState<SavedSearchCreate>({
    name: '',
    query: '',
    filters: {},
    notify: true,
    notify_frequency: 'daily',
  });

  useEffect(() => {
    fetchSearches();
  }, [fetchSearches]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createSearch(formData);
      setFormData({
        name: '',
        query: '',
        filters: {},
        notify: true,
        notify_frequency: 'daily',
      });
      setShowForm(false);
    } catch (err) {
      console.error('[v0] Error creating search:', err);
    }
  };

  const handleDelete = async (id: string) => {
    if (confirm('Are you sure you want to delete this saved search?')) {
      try {
        await deleteSearch(id);
      } catch (err) {
        console.error('[v0] Error deleting search:', err);
      }
    }
  };

  return (
    <div className="saved-searches-panel">
      <div className="panel-header">
        <h2>Saved Searches</h2>
        <button
          onClick={() => setShowForm(!showForm)}
          className="btn btn-primary"
        >
          {showForm ? 'Cancel' : '+ New Search'}
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}

      {showForm && (
        <form onSubmit={handleCreate} className="search-form">
          <input
            type="text"
            placeholder="Search name"
            value={formData.name}
            onChange={(e) =>
              setFormData({ ...formData, name: e.target.value })
            }
            required
          />
          <input
            type="text"
            placeholder="Query"
            value={formData.query}
            onChange={(e) =>
              setFormData({ ...formData, query: e.target.value })
            }
            required
          />
          <label>
            <input
              type="checkbox"
              checked={formData.notify}
              onChange={(e) =>
                setFormData({ ...formData, notify: e.target.checked })
              }
            />
            Enable notifications
          </label>
          {formData.notify && (
            <select
              value={formData.notify_frequency}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  notify_frequency: e.target.value as any,
                })
              }
            >
              <option value="immediate">Immediate</option>
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
            </select>
          )}
          <button type="submit" disabled={loading}>
            {loading ? 'Creating...' : 'Create Search'}
          </button>
        </form>
      )}

      {loading && searches.length === 0 ? (
        <div className="loading">Loading...</div>
      ) : searches.length === 0 ? (
        <div className="empty-state">
          <p>No saved searches yet</p>
          <p>Create one to get alerts when new institutions match your criteria</p>
        </div>
      ) : (
        <div className="searches-list">
          {searches.map((search) => (
            <div
              key={search.id}
              className={`search-item ${
                selectedSearch?.id === search.id ? 'active' : ''
              }`}
              onClick={() => selectSearch(search)}
            >
              <div className="search-info">
                <h3>{search.name}</h3>
                <p className="query">{search.query}</p>
                {search.match_count !== undefined && (
                  <p className="match-count">
                    {search.match_count} matches
                  </p>
                )}
              </div>
              <div className="search-actions">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    toggleNotifications(search.id, !search.notify);
                  }}
                  className={`btn-icon ${search.notify ? 'active' : ''}`}
                  title={search.notify ? 'Disable notifications' : 'Enable notifications'}
                >
                  🔔
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDelete(search.id);
                  }}
                  className="btn-icon delete"
                  title="Delete search"
                >
                  ✕
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      <style jsx>{`
        .saved-searches-panel {
          border: 1px solid #e5e7eb;
          border-radius: 8px;
          padding: 16px;
          background: #f9fafb;
        }

        .panel-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
        }

        .panel-header h2 {
          margin: 0;
          font-size: 18px;
          font-weight: 600;
        }

        .search-form {
          display: flex;
          flex-direction: column;
          gap: 12px;
          padding: 12px;
          background: white;
          border-radius: 6px;
          margin-bottom: 16px;
        }

        .search-form input,
        .search-form select {
          padding: 8px 12px;
          border: 1px solid #d1d5db;
          border-radius: 4px;
          font-size: 14px;
        }

        .search-form label {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 14px;
        }

        .search-form button {
          padding: 10px 16px;
          background: #2563eb;
          color: white;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          font-weight: 500;
        }

        .search-form button:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .searches-list {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .search-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 12px;
          background: white;
          border: 1px solid #e5e7eb;
          border-radius: 4px;
          cursor: pointer;
          transition: all 0.2s;
        }

        .search-item:hover {
          border-color: #2563eb;
          background: #f0f9ff;
        }

        .search-item.active {
          border-color: #2563eb;
          background: #eff6ff;
        }

        .search-info h3 {
          margin: 0;
          font-size: 14px;
          font-weight: 600;
        }

        .search-info .query {
          margin: 4px 0 0 0;
          font-size: 12px;
          color: #6b7280;
        }

        .search-info .match-count {
          margin: 4px 0 0 0;
          font-size: 12px;
          color: #059669;
          font-weight: 500;
        }

        .search-actions {
          display: flex;
          gap: 8px;
        }

        .btn-icon {
          width: 32px;
          height: 32px;
          padding: 0;
          border: 1px solid #d1d5db;
          background: white;
          border-radius: 4px;
          cursor: pointer;
          font-size: 16px;
          transition: all 0.2s;
        }

        .btn-icon:hover {
          background: #f3f4f6;
        }

        .btn-icon.active {
          background: #fef3c7;
          border-color: #f59e0b;
        }

        .btn-icon.delete:hover {
          background: #fee2e2;
          border-color: #dc2626;
        }

        .error-message {
          padding: 12px;
          background: #fee2e2;
          color: #dc2626;
          border-radius: 4px;
          margin-bottom: 12px;
          font-size: 14px;
        }

        .loading,
        .empty-state {
          padding: 24px;
          text-align: center;
          color: #6b7280;
          font-size: 14px;
        }

        .empty-state p:first-child {
          font-weight: 500;
          margin: 0 0 8px 0;
        }

        .empty-state p:last-child {
          margin: 0;
          font-size: 12px;
        }
      `}</style>
    </div>
  );
};
