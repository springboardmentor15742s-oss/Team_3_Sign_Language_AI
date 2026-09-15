import { useEffect, useRef, useState } from "react";
import { api } from "../api";

const TYPE_ICON = {
  achievement: "🎓",
  course_completion: "✅",
  practice_reminder: "👋",
  announcement: "📢",
};

function timeAgo(isoString) {
  const then = new Date(isoString.replace(" ", "T") + "Z");
  const diffMs = Date.now() - then.getTime();
  const mins = Math.floor(diffMs / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

export default function NotificationBell() {
  const [open, setOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const wrapRef = useRef(null);

  function refresh() {
    setLoading(true);
    api
      .getNotifications()
      .then((data) => {
        setNotifications(data.notifications);
        setUnreadCount(data.unread_count);
      })
      .finally(() => setLoading(false));
  }

  // Poll unread count quietly every 60s so the badge stays current without
  // the user needing to open the dropdown.
  useEffect(() => {
    api.getUnreadNotificationCount().then((d) => setUnreadCount(d.unread_count)).catch(() => {});
    const interval = setInterval(() => {
      api.getUnreadNotificationCount().then((d) => setUnreadCount(d.unread_count)).catch(() => {});
    }, 60000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    function handleClickOutside(e) {
      if (wrapRef.current && !wrapRef.current.contains(e.target)) setOpen(false);
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  function toggleOpen() {
    const next = !open;
    setOpen(next);
    if (next) refresh();
  }

  async function handleMarkAllRead() {
    await api.markAllNotificationsRead();
    setNotifications((prev) => prev.map((n) => ({ ...n, is_read: 1 })));
    setUnreadCount(0);
  }

  async function handleNotifClick(n) {
    if (!n.is_read) {
      await api.markNotificationRead(n.id);
      setNotifications((prev) => prev.map((x) => (x.id === n.id ? { ...x, is_read: 1 } : x)));
      setUnreadCount((c) => Math.max(0, c - 1));
    }
  }

  return (
    <div className="notif-bell-wrap" ref={wrapRef}>
      <button className="notif-bell-btn" onClick={toggleOpen} title="Notifications">
        🔔
        {unreadCount > 0 && <span className="notif-badge">{unreadCount > 9 ? "9+" : unreadCount}</span>}
      </button>

      {open && (
        <div className="notif-dropdown">
          <div className="notif-dropdown-header">
            <span>Notifications</span>
            {unreadCount > 0 && (
              <button className="notif-mark-all" onClick={handleMarkAllRead}>
                Mark all read
              </button>
            )}
          </div>
          <div className="notif-list">
            {loading && <p className="muted small notif-empty">Loading…</p>}
            {!loading && notifications.length === 0 && (
              <p className="muted small notif-empty">You're all caught up!</p>
            )}
            {!loading &&
              notifications.map((n) => (
                <div
                  key={n.id}
                  className={`notif-item ${n.is_read ? "" : "unread"}`}
                  onClick={() => handleNotifClick(n)}
                >
                  <span className="notif-icon">{TYPE_ICON[n.type] || "🔔"}</span>
                  <div className="notif-body">
                    <div className="notif-title">{n.title}</div>
                    <div className="notif-message muted small">{n.message}</div>
                    <div className="notif-time muted small">{timeAgo(n.created_at)}</div>
                  </div>
                  {!n.is_read && <span className="notif-dot" />}
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  );
}
