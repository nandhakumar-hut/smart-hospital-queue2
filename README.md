# Smart Hospital Queue & Waiting-Time Management System

A full-stack web app that cuts unnecessary hospital waiting: appointment booking, digital tokens, **real-time** queue tracking,
estimated waiting time, QR check-in, multi-stage patient journeys, notifications, analytics and reports.

**Stack:** Python 3.10+ / Flask, SQLite (stdlib), vanilla HTML/CSS/JS, Server-Sent Events for real time, built-in QR encoder (no extra package), `reportlab` (PDF).

## Quick start

```bash
cd smart-hospital-queue
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # optional, then edit SECRET_KEY
python run.py
```
Open <http://127.0.0.1:5000>. On first start the database is created and filled with demo data.
Reset the demo data any time with `python reset_db.py`. Run the tests with `python -m unittest discover -s tests -v`.

## Demo accounts

| Role | Login | Password | Notes |
|---|---|---|---|
| Patient | `patient@hospital.test` | `Patient@123` | Has token **CA-9** in a live Cardiology queue (4 patients ahead) |
| Patient 2 | `patient2@hospital.test` | `Patient@123` | Mid-journey: consultation done, **Blood Test waiting**, X-ray / review / pharmacy pending |
| Doctor | `dr.mehta@hospital.test` | `Doctor@123` | Cardiology queue (more: `dr.desai@...`, `dr.iyer@...`, `dr.nair@...`, `dr.shah@...` ...) |
| Staff (front desk) | `staff@hospital.test` | `Staff@123` | All queues of City General Hospital, QR check-in, priority |
| Lab / Radiology / Pharmacy staff | `lab.staff@hospital.test`, `radiology.staff@hospital.test`, `pharmacy.staff@hospital.test` | `Staff@123` | Their department counter only |
| Admin | `admin@hospital.test` | `Admin@123` | Everything |

40 more demo patients exist (`patient3@hospital.test` ... `patient42@hospital.test`, same password) plus 4 weeks of historical queue data that feeds the analytics.

## Try the complete flow (about 3 minutes)
1. **Register** a new patient at `/register` -> **sign in**.
2. *Book appointment* -> search hospital / department / doctor / date / availability -> pick a slot -> **token + QR code** are issued and a notification arrives.
   (Slots on today's date that already passed are hidden; the demo has a "today" queue seeded for Dr. Arjun Mehta, so book him for a later day, or use the demo patient.)
3. Open a second browser window as **staff** (`staff@hospital.test`): *QR check-in* -> paste the code shown under the patient's QR (or scan it with a camera in Chrome) -> status becomes **Checked in -> Waiting**.
4. As **doctor** (`dr.mehta@hospital.test`) use the *Queue console*: **Call Next Patient -> Start Consultation -> Complete** (tick Blood test / Pharmacy etc. to continue the journey).
5. The **patient's Live queue** page updates instantly (no refresh): token, now serving, patients ahead, estimated wait, journey stages. Notifications fire at 5 ahead, 3 ahead, next, called, etc.
6. Open *My appointments -> History* and *Consultations* to see the completed visit.
7. As **admin**: Dashboard, Busy-period analytics, Reports (CSV/PDF), and CRUD for hospitals, departments, doctors, staff, working hours, holidays.

## Features
- **Patient:** registration/login, hospital + department + doctor search with live availability, slot booking, digital token, QR, live queue (patients ahead, estimate, progress bar), cancel, history, completed consultations, in-app notifications (+ browser notifications while the page is open).
- **Doctor / staff:** per-queue console (call next, start, complete, skip, recall, absent), today's appointments, QR check-in (typed or camera via `BarcodeDetector`), emergency / high priority with mandatory reason and audit log, doctor "mark me unavailable" (cancels + notifies).
- **Admin:** statistics, current queues, department / doctor charts, busy-period heat-map, reports (7 types, CSV + PDF), full management screens, broadcast notifications, audit log.
- **Departments:** 12 per main hospital (General Medicine ... Pharmacy), each with its own queue; clinical departments queue per doctor.
- **Patient journey:** Registration -> Consultation -> Blood test -> X-ray / scan -> Doctor review -> Pharmacy; completing a stage automatically issues the next token and notifies the patient.
- **Waiting-time estimate** from the live queue + historical service times, always labelled an estimate.
- **Analytics** are descriptive statistics for staffing and capacity planning only. Nothing here diagnoses or decides medical priority; priority is set by authorised staff only.

## Security
Password hashing (salted PBKDF2-SHA256, 600k iterations), HttpOnly + SameSite session cookies (set `COOKIE_SECURE=1` behind HTTPS), CSRF token on every state-changing call, role-based access control on every endpoint,
queue-level authorisation for doctors/staff, patients scoped to their own records, input validation, login throttling, session reset on login, CSV formula-injection protection,
security headers + strict CSP (no inline scripts), parameterised SQL, and an audit log (logins, bookings, queue actions, priority changes, admin changes, exports).

## Configuration (`.env`)
| Variable | Default | Meaning |
|---|---|---|
| `SECRET_KEY` | dev value | **Set a long random value** (signs sessions) |
| `DATABASE_PATH` | `instance/hospital.db` | SQLite file |
| `TIMEZONE` | `Asia/Kolkata` | Hospital's local time zone (slots, "today", queue ordering). Change to yours |
| `SESSION_HOURS` | `8` | Session lifetime |
| `COOKIE_SECURE` | `0` | `1` when served over HTTPS |
| `AUTO_SEED` | `1` | Seed demo data when the DB is empty (use `0` in production) |
| `HOST`, `PORT`, `DEBUG` | `127.0.0.1`, `5000`, `0` | Server settings |

## Project structure
```
smart-hospital-queue/
├── run.py                    start the server          reset_db.py   recreate demo DB
├── requirements.txt  .env.example  README.md
├── app/
│   ├── __init__.py           app factory, CSRF, headers, error handlers
│   ├── config.py  core.py    config, DB helpers, validation, audit, notifications
│   ├── schema.sql            relational schema         seed.py       demo data
│   ├── auth.py               sessions, role decorators, queue access rules
│   ├── scheduling.py         working hours / breaks / holidays -> slots, safe booking
│   ├── queueing.py           queue engine: tokens, transitions, estimates, journeys, notifications
│   ├── analytics.py          statistics, busy periods, reports
│   ├── events.py             real-time broker (SSE)
│   ├── routes/               auth_routes, patient_routes, staff_routes, admin_routes
│   ├── templates/            login, register, patient, staff, admin (+ layout)
│   └── static/               css/style.css, js/{common,shell,auth,patient,staff,admin}.js
├── docs/                     API.md, DATABASE.md
└── tests/test_flow.py        end-to-end tests (journey, isolation, priority, admin, reports, security)
```

## Documentation
- [`docs/API.md`](docs/API.md) - all endpoints
- [`docs/DATABASE.md`](docs/DATABASE.md) - schema, relationships, estimate formula

## Production notes & known limits
- **Real-time** uses Server-Sent Events with an in-process broker: run a single process (threaded server or e.g. `waitress-serve --threads=64 run:app`). For multiple processes replace `app/events.py` with Redis pub/sub.
- **Push notifications:** in-app notifications always work; browser notifications appear while a dashboard tab is open and permission is granted. True background Web Push (service worker + VAPID keys) is not included.
- **SMS / email** delivery is not wired up; `notify()` in `app/core.py` is the single place to add it.
- QR codes are generated by a small built-in encoder (`app/qr.py`, verified against an independent decoder). Scanning with the camera needs a browser with `BarcodeDetector` (Chrome / Edge / Android); otherwise type the code.
- "Call Next" prefers checked-in patients; if nobody has checked in it falls back to the next booked patient so the demo works without extra steps. Tighten this in `queueing.call_next` if you want check-in to be mandatory.
- SQLite is perfect for demos and small clinics; switch to PostgreSQL for large multi-site deployments (SQL is standard apart from `julianday`, `BEGIN IMMEDIATE`, and the partial index syntax).
- Demo data and credentials are for testing only: run with `AUTO_SEED=0`, create your own admin and change every password before real use.
