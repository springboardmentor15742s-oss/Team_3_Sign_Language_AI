# UI Wireframes & Workflow Planning — Milestone 1 (React Frontend)

Text/ASCII wireframes for every screen implemented in this build.
(Implemented literally as React pages under `frontend/src/pages/`.)

---

## 1. Home / Landing (`pages/Home.jsx`)

```
┌───────────────────────────────────────────────────────────┐
│ 🤟 Sign Language Learning & Assessment Platform             │
│ Milestone 1 — Project Initialization...                     │
├───────────────────────────────────────────────────────────┤
│  Getting Started                 │  Datasets                │
│  1. Login / Register             │  4. Dataset Explorer     │
│  2. Learner Profile              │  5. Admin Panel (admin)  │
│  3. Learner Dashboard            │                          │
├───────────────────────────────────────────────────────────┤
│  [ Login status banner ]                                    │
│  [ ▸ About this Milestone (expandable <details>) ]          │
└───────────────────────────────────────────────────────────┘
   Navbar (top): Home | Dashboard | Profile | Dataset Explorer |
                 Admin Panel (if admin) ... [user chip] [Log out]
```

## 2. Login / Register (`pages/Login.jsx`)

```
┌───────────────────────────────────┐
│ 🔐 Login / Register                │
│ ┌───────────┬───────────────────┐ │
│ │  Login    │    Register        │ │  <- tab buttons
│ ├───────────┴───────────────────┤ │
│ │ Username: [___________]        │ │
│ │ Password: [___________]        │ │
│ │        [ Log in ]              │ │
│ └────────────────────────────────┘ │
└───────────────────────────────────┘

Register tab:
  Username | Email | Role (dropdown) | Password | Confirm Password
  [ Register ]
```

## 3. Learner Dashboard (`pages/Dashboard.jsx`)

```
┌───────────────────────────────────────────────────────────┐
│ 📊 Learner Dashboard                                        │
│ [Level] [Language] [Goals set] [Logged activities]  <- KPIs │
├───────────────────────────────────┬─────────────────────────┤
│ 📈 Learning Progress (bar chart)   │ 🎯 Learning Goals        │
│ 🕘 Recent Activity Log (table)     │ 🏆 Recommended Next Steps│
└───────────────────────────────────┴─────────────────────────┘
```

## 4. Learner Profile (`pages/Profile.jsx`)

```
┌───────────────────────────────────────────┐
│ 👤 Learner Profile Management               │
│ Username: (readonly)   Email: (readonly)    │
│ Learning Level:     [Beginner ▾]             │
│ Preferred Language: [ASL ▾]                  │
│ Learning Goals:     [x] Everyday Comm.       │
│                      [ ] Educational Vocab   │
│ About you:          [________________]      │
│               [ 💾 Save Profile ]            │
├───────────────────────────────────────────┤
│ 📋 Current Profile Summary                   │
└───────────────────────────────────────────┘
```

## 5. Dataset Explorer (`pages/DatasetExplorer.jsx`)

```
┌───────────────────────────────────────────────────────────┐
│ 🗂️ Dataset Explorer                                         │
│ 📚 Recommended Datasets table (name / purpose / source)     │
├───────────────────────────────────┬─────────────────────────┤
│ 🔍 Analyze folder structure &      │ 🖼️ Sample images preview │
│    labels  [bar chart + table]     │    (per-class thumbnails)│
├───────────────────────────────────┴─────────────────────────┤
│ 🧾 Image Format Report (dimensions / mode / format)          │
│ ⚙️ Preprocessing: target size sliders + [ 🚀 Run ] button     │
│ 📜 Recent Dataset Actions Log (table)                        │
└───────────────────────────────────────────────────────────┘
```

## 6. Admin Panel (`pages/AdminPanel.jsx`) — Administrator role only

```
┌───────────────────────────────────────────┐
│ 🛠️ Admin Panel                              │
│ 👥 Registered Users (table)                  │
│ ✏️ Manage a User:                            │
│    Select user ▾ | New role ▾ [Update]       │
│    Active [x] [Update]                       │
│ 🗂️ Dataset Integration Log (table)            │
└───────────────────────────────────────────┘
```

---

## Navigation flow (React Router)

```
        ┌──────────┐
        │  Home /  │
        └────┬─────┘
             │ not logged in
             ▼
     ┌───────────────┐
     │ /login        │  (Login/Register tabs)
     └───────┬───────┘
             │ logged in (JWT stored client-side)
   ┌─────────┼─────────────┬───────────────┐
   ▼         ▼              ▼               ▼
/dashboard /profile   /datasets       /admin*
                                        (*ProtectedRoute checks
                                         role === "Administrator")
```

`ProtectedRoute` wraps every authenticated page: it redirects to `/login`
if there's no user, and shows an "Access denied" card if the user's role
isn't in the page's `allowedRoles`.
