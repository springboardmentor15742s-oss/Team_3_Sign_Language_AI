# Security Notes

## Findings

### Self-registration role escalation (fixed 2026-08-18)

**Issue:** `POST /api/auth/register` accepted an arbitrary `role` field with
no server-side validation. The frontend registration form only ever sent
`role: "learner"`, but the restriction existed in the UI alone — anyone
calling the endpoint directly (curl, browser devtools, Postman) could
self-register as `instructor` or `admin` and immediately receive a valid
access token for that role.

Confirmed exploitable:

```
POST /api/auth/register
{"name": "Sneaky Admin", "email": "...", "password": "...", "role": "admin"}
```

returned a valid admin session — full access to `/api/admin/overview` and
every instructor/admin-only route.

**Fix:** `backend/app/routers/auth.py` now rejects any self-registration
request where `role` is not `"learner"`, with `400 Bad Request`. Instructor
and admin accounts are provisioned out of band (direct DB/script access),
not through the public registration endpoint. See `SELF_SERVICE_ROLES` in
that file.

**Lesson:** a role restriction expressed only in frontend UI (a disabled
`<select>`, a hidden option) is not a security boundary — it's a
convenience for honest users. Every role/permission check in this project
is expected to be enforced server-side; this was the one place that
slipped through, caught during manual testing of the registration flow
before it shipped.
