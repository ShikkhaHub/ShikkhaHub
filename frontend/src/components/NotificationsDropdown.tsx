import React, { useState, useRef, useEffect } from 'react';
import { useNotifications } from '../hooks/useNotifications';

export const NotificationsDropdown: React.FC = () => {
  const {
    notifications,
    summary,
    loading,
    markAsRead,
    markAllAsRead,
    deleteNotification,
  } = useNotifications();

  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(e.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const unreadCount = summary?.unread_count || 0;

  const handleNotificationClick = async (notificationId: string) => {
    try {
      await markAsRead(notificationId);
    } catch (err) {
      console.error('[v0] Error marking notification as read:', err);
    }
  };

  const handleDelete = async (e: React.MouseEvent, notificationId: string) => {
    e.stopPropagation();
    try {
      await deleteNotification(notificationId);
    } catch (err) {
      console.error('[v0] Error deleting notification:', err);
    }
  };

  return (
    <div className="notifications-dropdown" ref={dropdownRef}>
      <button
        className="notifications-button"
        onClick={() => setIsOpen(!isOpen)}
      >
        🔔
        {unreadCount > 0 && <span className="badge">{unreadCount}</span>}
      </button>

      {isOpen && (
        <div className="dropdown-menu">
          <div className="dropdown-header">
            <h3>Notifications</h3>
            {unreadCount > 0 && (
              <button
                onClick={markAllAsRead}
                className="btn-link"
              >
                Mark all as read
              </button>
            )}
          </div>

          {loading && notifications.length === 0 ? (
            <div className="dropdown-loading">Loading...</div>
          ) : notifications.length === 0 ? (
            <div className="dropdown-empty">
              <p>No notifications</p>
            </div>
          ) : (
            <div className="notifications-list">
              {notifications.map((notification) => (
                <div
                  key={notification.id}
                  className={`notification-item ${
                    notification.read ? 'read' : 'unread'
                  }`}
                  onClick={() => handleNotificationClick(notification.id)}
                >
                  <div className="notification-content">
                    <h4>{notification.title}</h4>
                    <p>{notification.message}</p>
                    <span className="notification-type">
                      {notification.type}
                    </span>
                  </div>
                  <button
                    className="btn-close"
                    onClick={(e) =>
                      handleDelete(e, notification.id)
                    }
                    title="Delete notification"
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          )}

          <div className="dropdown-footer">
            <a href="/notifications" className="view-all">
              View all notifications →
            </a>
          </div>
        </div>
      )}

      <style>{`
        .notifications-dropdown {
          position: relative;
        }

        .notifications-button {
          position: relative;
          width: 40px;
          height: 40px;
          border: 1px solid #e5e7eb;
          background: white;
          border-radius: 6px;
          cursor: pointer;
          font-size: 20px;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: all 0.2s;
        }

        .notifications-button:hover {
          background: #f9fafb;
          border-color: #d1d5db;
        }

        .badge {
          position: absolute;
          top: -8px;
          right: -8px;
          background: #dc2626;
          color: white;
          width: 20px;
          height: 20px;
          border-radius: 10px;
          font-size: 12px;
          font-weight: bold;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .dropdown-menu {
          position: absolute;
          top: 100%;
          right: 0;
          width: 360px;
          background: white;
          border: 1px solid #e5e7eb;
          border-radius: 8px;
          box-shadow: 0 10px 15px rgba(0, 0, 0, 0.1);
          margin-top: 8px;
          z-index: 1000;
          display: flex;
          flex-direction: column;
          max-height: 500px;
        }

        .dropdown-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 12px 16px;
          border-bottom: 1px solid #e5e7eb;
        }

        .dropdown-header h3 {
          margin: 0;
          font-size: 16px;
          font-weight: 600;
        }

        .btn-link {
          background: none;
          border: none;
          color: #2563eb;
          cursor: pointer;
          font-size: 12px;
          text-decoration: none;
        }

        .btn-link:hover {
          text-decoration: underline;
        }

        .notifications-list {
          flex: 1;
          overflow-y: auto;
          max-height: 350px;
        }

        .notification-item {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          padding: 12px 16px;
          border-bottom: 1px solid #f3f4f6;
          cursor: pointer;
          transition: background 0.2s;
        }

        .notification-item:hover {
          background: #f9fafb;
        }

        .notification-item.unread {
          background: #eff6ff;
        }

        .notification-content {
          flex: 1;
          margin-right: 8px;
        }

        .notification-item h4 {
          margin: 0;
          font-size: 14px;
          font-weight: 600;
          color: #1f2937;
        }

        .notification-item p {
          margin: 4px 0 0 0;
          font-size: 13px;
          color: #6b7280;
        }

        .notification-type {
          display: inline-block;
          margin-top: 4px;
          padding: 2px 8px;
          background: #f3f4f6;
          border-radius: 4px;
          font-size: 11px;
          color: #6b7280;
          font-weight: 500;
        }

        .btn-close {
          background: none;
          border: none;
          color: #9ca3af;
          cursor: pointer;
          font-size: 16px;
          padding: 0;
          width: 20px;
          height: 20px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .btn-close:hover {
          color: #dc2626;
        }

        .dropdown-loading,
        .dropdown-empty {
          padding: 32px 16px;
          text-align: center;
          color: #9ca3af;
          font-size: 14px;
        }

        .dropdown-footer {
          padding: 12px 16px;
          border-top: 1px solid #e5e7eb;
          text-align: center;
        }

        .view-all {
          color: #2563eb;
          text-decoration: none;
          font-size: 13px;
          font-weight: 500;
        }

        .view-all:hover {
          text-decoration: underline;
        }
      `}</style>
    </div>
  );
};
