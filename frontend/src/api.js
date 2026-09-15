// Small fetch-based API client. No axios dependency needed.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

function getToken() {
  return localStorage.getItem("token");
}

async function request(path, { method = "GET", body, auth = true, isForm = false } = {}) {
  const headers = {};
  if (!isForm) headers["Content-Type"] = "application/json";
  if (auth) {
    const token = getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers,
    body: body ? (isForm ? body : JSON.stringify(body)) : undefined,
  });

  let data = null;
  const contentType = res.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    data = await res.json();
  }

  if (!res.ok) {
    const message = (data && (data.detail || data.message)) || `Request failed (${res.status})`;
    throw new Error(typeof message === "string" ? message : JSON.stringify(message));
  }
  return data;
}

async function downloadFile(path, fallbackFilename) {
  const token = getToken();
  const res = await fetch(`${API_BASE_URL}${path}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!res.ok) throw new Error(`Download failed (${res.status})`);
  const blob = await res.blob();
  const disposition = res.headers.get("content-disposition") || "";
  const match = disposition.match(/filename="?([^"]+)"?/);
  const filename = match ? match[1] : fallbackFilename;
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}

export const api = {
  // Auth
  register: (payload) => request("/api/auth/register", { method: "POST", body: payload, auth: false }),
  login: (payload) => request("/api/auth/login", { method: "POST", body: payload, auth: false }),
  me: () => request("/api/auth/me"),

  // Profile
  getProfile: () => request("/api/profile"),
  saveProfile: (payload) => request("/api/profile", { method: "PUT", body: payload }),
  saveProfileIdentity: (payload) => request("/api/profile/identity", { method: "PUT", body: payload }),
  changePassword: (payload) => request("/api/auth/change-password", { method: "POST", body: payload }),

  // Dashboard
  getDashboard: () => request("/api/dashboard"),
  logActivity: () => request("/api/dashboard/log-activity", { method: "POST" }),

  // Datasets
  getRecommendedDatasets: () => request("/api/datasets/recommended"),
  listDatasets: () => request("/api/datasets/list"),
  getDatasetStructure: (name) => request(`/api/datasets/${name}/structure`),
  getDatasetPreview: (name) => request(`/api/datasets/${name}/preview`),
  getFormatReport: (name) => request(`/api/datasets/${name}/format-report`),
  preprocessDataset: (name, width, height) =>
    request(`/api/datasets/${name}/preprocess?width=${width}&height=${height}`, { method: "POST" }),
  getDatasetLog: () => request("/api/datasets/log"),
  datasetImageUrl: (path) => `${API_BASE_URL}${path}`,

  // Admin
  listUsers: () => request("/api/admin/users"),
  updateUserRole: (id, role) => request(`/api/admin/users/${id}/role`, { method: "PUT", body: { role } }),
  updateUserActive: (id, is_active) =>
    request(`/api/admin/users/${id}/active`, { method: "PUT", body: { is_active } }),
  updateUserLevel: (id, level) => request(`/api/admin/users/${id}/level`, { method: "PUT", body: { level } }),

  // Gesture Recognition, Hand Tracking & Accuracy Assessment (Milestone 2)
  getGestureLibrary: () => request("/api/gesture/library", { auth: false }),
  getHandConnections: () => request("/api/gesture/hand-connections", { auth: false }),
  detectGesture: (blob) => {
    const form = new FormData();
    form.append("file", blob, "frame.jpg");
    return request("/api/gesture/detect", { method: "POST", body: form, isForm: true });
  },
  assessGesture: (blob, targetLabel) => {
    const form = new FormData();
    form.append("file", blob, "frame.jpg");
    return request(`/api/gesture/assess?target_label=${encodeURIComponent(targetLabel)}`, {
      method: "POST",
      body: form,
      isForm: true,
    });
  },
  getGestureHistory: (limit = 20) => request(`/api/gesture/history?limit=${limit}`),
  getGestureStats: () => request("/api/gesture/stats"),

  // AI Feedback & Learning Intelligence (Milestone 3)
  getIntelligenceSummary: () => request("/api/intelligence/summary"),
  getAnalytics: () => request("/api/intelligence/analytics"),
  getWeakAreas: () => request("/api/intelligence/weak-areas"),
  getFeedback: () => request("/api/intelligence/feedback"),
  getRecommendations: () => request("/api/intelligence/recommendations"),
  getLearningPlan: () => request("/api/intelligence/learning-plan"),
  getPerformanceTrend: () => request("/api/intelligence/performance-trend"),
  getPerformanceScore: () => request("/api/intelligence/performance-score"),
  getAssessmentReport: () => request("/api/intelligence/report"),
  getReportHistory: () => request("/api/intelligence/report/history"),
  downloadAssessmentReport: () => downloadFile("/api/intelligence/report/download", "assessment-report.txt"),

  // Certification Workflows (Milestone 4)
  getCertEligibility: () => request("/api/certification/eligibility"),
  issueCertificate: (level) => request(`/api/certification/issue/${level}`, { method: "POST" }),
  getMyCertificates: () => request("/api/certification/my"),
  verifyCertificate: (code) => request(`/api/certification/verify/${code}`, { auth: false }),
  getAllCertificates: () => request("/api/certification/all"),
  updateCertificateStatus: (certId, status) =>
    request(`/api/certification/${certId}/status`, { method: "PUT", body: { status } }),
  downloadCertificate: (certId, code) => downloadFile(`/api/certification/${certId}/download`, `${code}.txt`),
  downloadCertificatePdf: (certId, code) =>
    downloadFile(`/api/certification/${certId}/download/pdf`, `${code}.pdf`),

  // Course & Content Service
  getCourseMeta: () => request("/api/courses/meta"),
  listCourses: (params = {}) => {
    const q = new URLSearchParams();
    if (params.category) q.set("category", params.category);
    if (params.level) q.set("level", params.level);
    if (params.search) q.set("search", params.search);
    const qs = q.toString();
    return request(`/api/courses${qs ? `?${qs}` : ""}`);
  },
  getCourse: (courseId) => request(`/api/courses/${courseId}`),
  enrollInCourse: (courseId) => request(`/api/courses/${courseId}/enroll`, { method: "POST" }),
  markLessonWatched: (lessonId) => request(`/api/courses/lessons/${lessonId}/watched`, { method: "POST" }),
  getMyEnrollments: () => request("/api/courses/my-enrollments"),
  createCourse: (payload) => request("/api/courses", { method: "POST", body: payload }),
  addLesson: (courseId, payload) =>
    request(`/api/courses/${courseId}/lessons`, { method: "POST", body: payload }),

  // Reporting Modules (Milestone 4)
  getLearningReport: () => request("/api/reports/learning"),
  downloadLearningPdf: (username) => downloadFile("/api/reports/learning/pdf", `learning-report-${username}.pdf`),
  downloadAccuracyCsv: (username) => downloadFile("/api/reports/accuracy/csv", `accuracy-report-${username}.csv`),
  downloadAccuracyPdf: (username) => downloadFile("/api/reports/accuracy/pdf", `accuracy-report-${username}.pdf`),
  downloadProgressCsv: (username) => downloadFile("/api/reports/progress/csv", `progress-report-${username}.csv`),
  downloadProgressPdf: (username) => downloadFile("/api/reports/progress/pdf", `progress-report-${username}.pdf`),
  downloadCertificationCsv: (username) =>
    downloadFile("/api/reports/certification/csv", `certification-report-${username}.csv`),
  downloadCertificationPdf: (username) =>
    downloadFile("/api/reports/certification/pdf", `certification-report-${username}.pdf`),
  getClassOverview: () => request("/api/reports/class-overview"),
  downloadClassOverviewCsv: () => downloadFile("/api/reports/class-overview/csv", "class-overview-report.csv"),
  downloadClassOverviewPdf: () => downloadFile("/api/reports/class-overview/pdf", "class-overview-report.pdf"),

  // Notification & Reminder System
  getNotifications: () => request("/api/notifications"),
  getUnreadNotificationCount: () => request("/api/notifications/unread-count"),
  markNotificationRead: (id) => request(`/api/notifications/${id}/read`, { method: "POST" }),
  markAllNotificationsRead: () => request("/api/notifications/read-all", { method: "POST" }),
  postAnnouncement: (payload) => request("/api/notifications/announcement", { method: "POST", body: payload }),

  // Quiz / Knowledge-Check module
  getQuizQuestions: (level, count = 5) =>
    request(`/api/quiz/questions?level=${encodeURIComponent(level)}&count=${count}`),
  submitQuiz: (payload) => request("/api/quiz/submit", { method: "POST", body: payload }),
  getMyQuizAttempts: () => request("/api/quiz/my-attempts"),
};

export { API_BASE_URL };
