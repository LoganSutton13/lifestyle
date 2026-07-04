# Cursor Build Specification: Mobile-First Health/Fitness Coaching PWA

_Last updated: 2026-07-04_

This document is the implementation contract for building a clean, professional health/fitness coaching app inspired by Trainerize-style mobile UX. The app must be implemented exactly from this specification unless a contradiction is found. Do not invent product features beyond what is described here. When an implementation choice is not explicitly specified, choose the simplest scalable approach that preserves security, mobile usability, and maintainable architecture.

## 1. Executive Decision Summary

### Product
Build a mobile-first health/fitness coaching Progressive Web App (PWA) with three roles:

1. Client
2. Coach
3. Admin

Clients can view assigned meal plans, complete daily checklist activities, record measurements/body-weight data, view graphs, update profile details, choose a food-character avatar, change password, and delete their account.

Coaches can associate existing client accounts to themselves, view client health-related data, assign meal plan items, and assign daily activities.

Admins have their own admin area where they can create coach accounts, elevate existing clients to coach role, delete any account, and change their own password.

### Recommended stack
Use this stack unless the user explicitly changes it later:

- Frontend: React + TypeScript + Vite
- Styling: Tailwind CSS with custom reusable components
- PWA: vite-plugin-pwa, web app manifest, service worker for static assets only
- Icons: lucide-react or another open-source SVG icon package. Do not use emoji anywhere in the UI.
- Charts: Recharts
- Forms: React Hook Form + Zod
- Data fetching: TanStack Query
- Backend: Python + FastAPI
- Database: PostgreSQL hosted on Neon Free for MVP, with easy migration to a paid Postgres provider later
- ORM/migrations: SQLAlchemy 2.x async + Alembic
- Auth: Custom username/password authentication with Argon2 password hashing, JWT access token, and rotating refresh tokens stored server-side
- Frontend hosting: Vercel
- Backend hosting primary: Vercel Python/FastAPI runtime
- Backend hosting fallback: Railway FastAPI service if Vercel limitations become problematic

### Current platform facts checked on 2026-07-04
These facts influence the deployment plan:

- Vercel supports FastAPI/Python through its Python runtime. Vercel looks for a FastAPI instance named `app` at supported entrypoints such as `app/main.py`, and custom entrypoints can be configured with `[tool.vercel] entrypoint` in `pyproject.toml`.
  Source: https://vercel.com/docs/frameworks/backend/fastapi
- Vercel FastAPI apps become a single Vercel Function, and the Python/FastAPI application bundle must fit within Vercel Function limits, including the documented 500 MB Python bundle limit.
  Source: https://vercel.com/docs/frameworks/backend/fastapi and https://vercel.com/docs/functions/runtimes/python
- Vercel supports Vite frontend deployments and auto-detects common build settings, but this spec still gives exact settings.
  Source: https://vercel.com/docs/frameworks/frontend/vite
- Railway supports FastAPI deployment from GitHub/CLI/Dockerfile and provides a public domain from the service networking settings.
  Source: https://docs.railway.com/guides/fastapi
- Railway requires apps to listen on `0.0.0.0:$PORT` for public networking.
  Source: https://docs.railway.com/public-networking
- Neon has a Free plan with PostgreSQL, 0.5 GB storage per project, and serverless-friendly features. This is suitable for MVP/prototype, not a guarantee for long-term production scale.
  Source: https://neon.com/pricing
- Samsung Health/Galaxy Watch data access is not directly available to a browser-only React PWA. Samsung Health Data SDK and Health Connect integrations are Android/native-app oriented and permission-gated. Build the database/API extension points now, but do not implement watch sync in MVP.
  Sources: https://developer.samsung.com/health/data/overview.html and https://developer.android.com/health-and-fitness/health-connect

## 2. Hard Requirements and Non-Negotiables

### General
- Build the app as a mobile-first PWA.
- The app must look clean, sleek, simple, and professional.
- Theme: white background, cyan-blue primary accents, black text.
- Use open-source SVG/icon libraries. Do not use emojis.
- All core client views must be usable on a phone-sized viewport first.
- The frontend must include all PWA assets and configuration needed so users can add it to their homescreen and see the configured app icon.
- All sensitive operations must be protected by authentication and role-based authorization.
- Store timestamps in UTC in the database.
- Render user-provided raw text as escaped text, never as HTML.
- Do not expose password hashes or refresh-token hashes in any API response.

### Backend language decision
The user originally preferred C# but approved Python if it works with Vercel. Therefore, implement the backend in Python/FastAPI as the primary backend. Do not implement a C# backend unless the user later explicitly reverses this decision.

### Health and fitness disclaimer
This application is for fitness/wellness tracking and coaching support. Do not make medical-diagnosis claims. Do not build features that suggest diagnosis, treatment, or emergency medical guidance.

### Samsung/Galaxy Watch integration
Do not block MVP on Samsung watch integration. For the MVP, manual measurement entry is required. Create extensible fields in the database for future data sources, but do not claim that the browser PWA can directly read Samsung Health/Galaxy Watch steps.

## 3. User Roles and Permissions

### Role definitions

| Role | Purpose |
| --- | --- |
| Client | Standard user who tracks meals, tasks, notes, measurements, profile settings. |
| Coach | Coaching user who manages associated clients and assigns meal/task items. |
| Admin | Administrative user with separate admin area for account management. |

### Capability matrix

| Feature | Client | Coach | Admin |
| --- | --- | --- | --- |
| Register from public login/register page | Yes, creates client only | No | No |
| Login from client/coach login page | Yes | Yes | Should redirect to admin area if admin uses it accidentally |
| Login from admin page | No | No | Yes |
| View client bottom nav | Yes | No | No |
| View meal plan assigned to self | Yes | No | No |
| Add own measurements | Yes | No | No |
| View own measurement graphs | Yes | No | No |
| Complete assigned checklist tasks | Yes | No | No |
| Add daily note | Yes | No | No |
| Edit own profile/account info | Yes | Yes | Yes |
| Delete own account with password confirmation | Yes | Yes | Yes |
| Add existing clients to client list | No | Yes | No, except through account management if needed later |
| View associated client health data | No | Yes | Optional through admin user list only; not required for MVP |
| Assign meal plan items to clients | No | Yes | No |
| Assign daily activities to clients | No | Yes | No |
| Create coach account | No | No | Yes |
| Elevate client to coach | No | No | Yes |
| Delete any account | No | No | Yes |
| Change admin password | No | No | Yes |

### Authorization rules
- A client can only access their own data.
- A coach can only access data for clients associated through `coach_clients`.
- A coach can add only existing users whose role is `client` to their client list.
- A coach cannot view or edit a client's password or password hash.
- A coach cannot delete client accounts.
- An admin can create coach accounts, elevate clients to coach, and delete accounts.
- An admin cannot view raw passwords or password hashes.
- Account deletion must cascade/delete associated application data according to the database constraints below.

## 4. UX/UI Design System

### Visual style
Use a white/cyan-blue theme:

```ts
const theme = {
  colors: {
    background: '#FFFFFF',
    surface: '#F8FAFC',
    surfaceElevated: '#FFFFFF',
    primary: '#00B8D9',
    primaryDark: '#0086A8',
    primarySoft: '#E6FAFE',
    text: '#0B0F14',
    textMuted: '#4B5563',
    border: '#E5E7EB',
    danger: '#EF4444',
    success: '#10B981',
    warning: '#F59E0B'
  }
}
```

### Typography
- Use system font stack or Inter if added as an npm/web font dependency.
- Body text: 16px minimum on mobile.
- Titles: 24-30px, semibold/bold.
- Buttons and form labels must be readable on mobile.
- Text color must be black or near-black for primary content.

### Layout
- Mobile max content width: full viewport, with 16px horizontal padding.
- Desktop layout can center content at 480px for client mobile views.
- Coach/admin dashboards can expand up to 1200px on desktop but must remain responsive.
- Touch targets must be at least 44px high.
- Primary actions should be obvious cyan-blue buttons.
- Destructive actions must be red/danger styling with confirmation.

### Client bottom navigation
A fixed bottom home bar must be present on client app pages. It contains exactly four options:

Left to right:

1. Meal Plan
   - Icon: food/utensils icon, for example `Utensils` from lucide-react.
   - Route: `/app/meals`
2. Checklist
   - Icon: checkmark/checklist icon, for example `CheckSquare` or `CircleCheck`.
   - Route: `/app/checklist`
3. Data
   - Icon: graph/chart icon, for example `LineChart`.
   - Route: `/app/data`
4. Profile
   - Icon: user/profile icon, for example `UserCircle`.
   - Route: `/app/profile`

The bottom nav must:
- Be fixed to the bottom.
- Have a white background.
- Have a subtle top border/shadow.
- Highlight the active tab in cyan-blue.
- Respect iOS safe-area inset using `padding-bottom: env(safe-area-inset-bottom)`.
- Never use emoji icons.

## 5. Frontend Routes

### Public/client/coach routes

| Route | Component | Access |
| --- | --- | --- |
| `/` | Redirect based on auth state | Public |
| `/login` | Client/coach login page | Public |
| `/register` | Client self-registration page | Public |
| `/app/meals` | Client meal plan page | Client |
| `/app/checklist` | Client checklist page | Client |
| `/app/data` | Client data graphs page | Client |
| `/app/profile` | Client profile page | Client |
| `/coach` | Coach dashboard/client list | Coach |
| `/coach/clients/:clientId` | Coach client detail dashboard | Coach |
| `/coach/profile` | Coach profile/password page | Coach |

### Admin routes

| Route | Component | Access |
| --- | --- | --- |
| `/admin/login` | Admin-only login page | Public, but only accepts admin users |
| `/admin` | Admin dashboard | Admin |
| `/admin/users` | User management | Admin |
| `/admin/settings` | Admin password/settings | Admin |

### Redirect rules
- Unauthenticated users attempting protected pages redirect to `/login`, except admin routes redirect to `/admin/login`.
- Authenticated client going to `/` redirects to `/app/checklist`.
- Authenticated coach going to `/` redirects to `/coach`.
- Authenticated admin going to `/` redirects to `/admin`.
- If an admin logs in from `/login`, redirect them to `/admin`.
- If a non-admin logs in from `/admin/login`, immediately log them out or show “Admin access required.”

## 6. Frontend Implementation Details

### Required frontend package choices
Use these unless there is a compelling compatibility reason not to:

```bash
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install react-router-dom @tanstack/react-query zod react-hook-form @hookform/resolvers lucide-react recharts canvas-confetti date-fns
npm install -D tailwindcss postcss autoprefixer vite-plugin-pwa vitest @testing-library/react @testing-library/jest-dom jsdom eslint prettier
```

Optional but acceptable:
- `clsx`
- `tailwind-merge`
- `framer-motion` for small UI transitions

Do not add a heavy UI kit unless the user explicitly asks. Build simple reusable components locally.

### Frontend folder structure

```txt
frontend/
  public/
    icons/
      icon-192.png
      icon-512.png
      maskable-512.png
      apple-touch-icon.png
      favicon.svg
    avatars/
      avocado.svg
      blueberry.svg
      strawberry.svg
      banana.svg
      broccoli.svg
      carrot.svg
      apple.svg
      orange.svg
      pear.svg
      oatmeal.svg
      yogurt.svg
      sweet-potato.svg
  src/
    app/
      App.tsx
      router.tsx
      providers.tsx
    assets/
    components/
      ui/
        Button.tsx
        Card.tsx
        Input.tsx
        Select.tsx
        Modal.tsx
        EmptyState.tsx
        Spinner.tsx
        Toast.tsx
      layout/
        ClientAppLayout.tsx
        BottomNav.tsx
        CoachLayout.tsx
        AdminLayout.tsx
    features/
      auth/
        api.ts
        hooks.ts
        LoginPage.tsx
        RegisterPage.tsx
        AdminLoginPage.tsx
        AuthGuard.tsx
      meals/
        MealPlanPage.tsx
        MealFilterTabs.tsx
        MealCard.tsx
      checklist/
        ChecklistPage.tsx
        TaskItem.tsx
        DailyNoteBox.tsx
      measurements/
        DataPage.tsx
        MeasurementChart.tsx
        AddMeasurementModal.tsx
        RangeFilter.tsx
        MeasurementTypeTabs.tsx
      profile/
        ProfilePage.tsx
        AvatarPicker.tsx
        ChangePasswordForm.tsx
        DeleteAccountSection.tsx
      coach/
        CoachDashboard.tsx
        ClientSearchAdd.tsx
        CoachClientDetail.tsx
        CoachMealsPanel.tsx
        CoachTasksPanel.tsx
        CoachMeasurementsPanel.tsx
        CoachNotesPanel.tsx
      admin/
        AdminDashboard.tsx
        AdminUsersPage.tsx
        CreateCoachForm.tsx
        ElevateClientForm.tsx
        DeleteAccountPanel.tsx
        AdminSettingsPage.tsx
    lib/
      apiClient.ts
      authStore.ts
      date.ts
      units.ts
      errors.ts
      constants.ts
    styles/
      index.css
    main.tsx
    vite-env.d.ts
  index.html
  package.json
  vite.config.ts
  tailwind.config.ts
  tsconfig.json
```

### Frontend TypeScript rules
- Enable strict TypeScript.
- Avoid `any`. Use typed API response interfaces.
- Keep API functions in feature-level `api.ts` files or `lib/apiClient.ts`.
- Use TanStack Query for all GET/list operations.
- Use mutations for POST/PATCH/DELETE operations and invalidate relevant query keys.
- Keep components small and cohesive.
- Do not put large API logic inside page components.

### API client behavior
Use a central API client that:
- Reads `VITE_API_BASE_URL` from environment.
- Sends `Authorization: Bearer <accessToken>` when an access token exists in memory.
- Sends `credentials: 'include'` so refresh cookies work.
- On 401, attempts `/api/auth/refresh` once, updates access token in memory, and retries the failed request.
- If refresh fails, clears auth state and redirects to `/login` or `/admin/login` depending on the current route.

Do not store access tokens in localStorage. Access token can be kept in memory. Refresh token is stored in an HttpOnly cookie by the backend.

## 7. Client Feature Specifications

### 7.1 Meal Plan Page
Route: `/app/meals`

Purpose: Client views meals assigned by their coach/admin configuration.

UI requirements:
- Title: “Meal Plan”
- Horizontal filter chips/tabs at top:
  - All
  - Breakfast
  - Lunch
  - Dinner
  - Dessert
- Scrollable meal list.
- Each meal card displays:
  - Meal name
  - Category badge
  - Raw description text rendered as escaped text with whitespace preserved
- Default query loads page 1 with first 10 meals associated with that client.
- Provide pagination controls at bottom:
  - Previous, disabled on page 1
  - Next, disabled when `hasNextPage` is false
- When a filter is applied, reset to page 1 and make a new backend query.
- Do not filter meals only on the client. The backend must perform filtering and pagination.

Default API call:

```http
GET /api/me/meals?page=1&pageSize=10
```

Filtered call:

```http
GET /api/me/meals?category=breakfast&page=1&pageSize=10
```

Expected response:

```json
{
  "items": [
    {
      "id": "uuid",
      "name": "Greek Yogurt Bowl",
      "category": "breakfast",
      "categoryLabel": "Breakfast",
      "description": "Plain Greek yogurt, blueberries, chia seeds, and honey.",
      "assignedAt": "2026-07-04T18:30:00Z"
    }
  ],
  "page": 1,
  "pageSize": 10,
  "total": 27,
  "hasNextPage": true
}
```

Acceptance criteria:
- The first page shows at most 10 assigned meals.
- Next page triggers a new backend request.
- Category filter triggers a new backend request.
- Empty state appears if no meals exist.
- Loading and error states are visible and mobile-friendly.

### 7.2 Data Points / Habit Tracker Page
Route: `/app/data`

Purpose: Client records and visualizes measurements such as body weight, waist, hips, and thigh.

UI requirements:
- Title: “Data”
- Top right plus icon button for adding a record. Use a plus icon from lucide-react.
- Top horizontal measurement type tabs. These must be loaded from the backend, not hardcoded in the component:
  - Body Weight
  - Waist
  - Hips
  - Thigh
- Time range filters:
  - 1M (default)
  - 3M
  - 6M
  - 1Y
  - 3Y
  - Optional custom date range, but max range must be 3 years.
- Default graph range: previous month through today.
- Graph must scale based on returned values and selected range.
- Use Recharts `ResponsiveContainer` so the chart fits mobile screens.
- Add-record modal fields:
  - Numeric value
  - Data type (body weight, waist, hips, thigh, etc.)
  - Unit system/unit. Default must be lbs for body weight. Measurements default to inches.
  - Optional recorded datetime, default now.
  - Save button.
- On save:
  - Store numeric value, unit, type, and datetime in database.
  - Update/invalidate the corresponding graph query.
  - Close modal and show success toast.

API calls:

```http
GET /api/me/measurement-types
GET /api/me/measurements?typeKey=body_weight&startDate=2026-06-04&endDate=2026-07-04&unitKey=lb
POST /api/me/measurements
```

POST body:

```json
{
  "typeKey": "body_weight",
  "value": 183.2,
  "unitKey": "lb",
  "recordedAt": "2026-07-04T15:45:00-07:00"
}
```

Graph response:

```json
{
  "type": {
    "key": "body_weight",
    "displayName": "Body Weight"
  },
  "unit": {
    "key": "lb",
    "symbol": "lbs"
  },
  "startDate": "2026-06-04",
  "endDate": "2026-07-04",
  "points": [
    {
      "id": "uuid",
      "recordedAt": "2026-06-10T13:00:00Z",
      "value": 184.5
    }
  ]
}
```

Backend validation:
- Value must be numeric and greater than 0.
- Range cannot exceed 3 years, defined as 1095 days.
- If no range is provided, use previous month through current date.
- If `unitKey` is omitted, return in the measurement type default unit.
- Store original value/unit and normalized base value for future conversions.

Samsung/Galaxy Watch steps:
- Do not implement direct Samsung watch syncing in MVP.
- Add extension-ready fields such as `source` on measurement records.
- Future implementation can add a native Android companion app that reads Samsung Health/Health Connect with user consent and syncs daily steps to this API.
- The PWA should not show a broken “Connect Samsung Watch” button in MVP. If included, it must be hidden behind a disabled feature flag with explanatory copy.

Acceptance criteria:
- Plus icon opens modal.
- Body weight defaults to lbs.
- Saved measurement appears in graph without full page refresh.
- Time range changes query the backend.
- The 3-year max is enforced in frontend and backend.
- Measurement type tabs are data-driven from backend.

### 7.3 Checklist Page
Route: `/app/checklist`

Purpose: Client checks off coach-assigned daily activities and saves notes for that day.

UI requirements:
- Title: “Checklist” or “Today’s Checklist”
- Date selector optional. Default date is today in the user’s profile/browser timezone.
- Scrollable list of tasks active for the selected date.
- Each task row/card displays:
  - Activity title
  - Optional description
  - Checkbox on the right side
- When the client checks off all activities for the selected day:
  - Play a small confetti animation.
  - Use `canvas-confetti` or a small open-source animation library.
  - Confetti should trigger only when transitioning from not-all-complete to all-complete.
  - Do not trigger confetti on initial page load.
- Bottom of page has a daily notes area:
  - Multiline textarea
  - Save button
  - Saved status/updated message
- Notes must be visible to the coach.

API calls:

```http
GET /api/me/checklist?date=2026-07-04
PATCH /api/me/checklist/{taskId}/completion
PUT /api/me/daily-note
```

Completion request:

```json
{
  "date": "2026-07-04",
  "completed": true
}
```

Daily note request:

```json
{
  "date": "2026-07-04",
  "body": "Felt great today. Walked after lunch."
}
```

Checklist response:

```json
{
  "date": "2026-07-04",
  "tasks": [
    {
      "id": "uuid",
      "title": "Drink 1 gallon of water",
      "description": "Spread intake throughout the day.",
      "completed": false
    }
  ],
  "note": {
    "body": "",
    "updatedAt": null
  }
}
```

Acceptance criteria:
- Tasks are loaded from backend.
- Checking/unchecking persists to database.
- Daily notes persist and reload correctly.
- Coach can view completion history and notes.
- Confetti is small, tasteful, and not disruptive.

### 7.4 Profile Page
Route: `/app/profile`

Purpose: Client manages profile/account settings.

UI sections:
1. Profile summary
   - Avatar
   - Username
   - First name
   - Last name
2. Avatar picker
   - 12 healthy food “character” avatars.
   - No emojis.
   - Use local SVG assets in `public/avatars`.
   - Suggested avatar keys:
     - avocado
     - blueberry
     - strawberry
     - banana
     - broccoli
     - carrot
     - apple
     - orange
     - pear
     - oatmeal
     - yogurt
     - sweet-potato
3. Account information form
   - Username
   - First name
   - Last name
   - Timezone optional, default browser timezone when account is created
4. Change password form
   - Current password
   - New password
   - Confirm new password
5. Delete account section
   - Clear warning that this will delete the account and associated application data.
   - Requires current password input.
   - Requires final confirm button.
   - On success, log user out and redirect to `/login`.

Profile update request:

```http
PUT /api/me
```

```json
{
  "username": "samfit",
  "firstName": "Sam",
  "lastName": "Rivera",
  "timezone": "America/Los_Angeles",
  "avatarKey": "avocado"
}
```

Delete request:

```http
DELETE /api/me
```

```json
{
  "password": "user-current-password"
}
```

Acceptance criteria:
- Avatar selection persists.
- Password change requires current password.
- Delete account requires password and cannot be accidental.
- UI uses food-character SVGs, not emoji.

## 8. Coach Feature Specifications

### 8.1 Coach Dashboard
Route: `/coach`

Purpose: Coach sees associated clients and can add existing client accounts.

UI requirements:
- Title: “Clients”
- Search field for existing client accounts by username/name.
- Existing associated client list.
- Client cards show:
  - Avatar
  - First name + last name
  - Username
  - Quick summary: latest body weight if available, today checklist completion count if available
- Button: “Add Client” or plus icon.

API calls:

```http
GET /api/coach/clients?search=sam&page=1&pageSize=20
GET /api/coach/client-search?query=sam
POST /api/coach/clients
DELETE /api/coach/clients/{clientId}
```

Add client request:

```json
{
  "clientId": "uuid"
}
```

Rules:
- Coach can add only users with `role = client`.
- If already associated, return 409 with clear error.
- Removing a client association does not delete the client account or health data.

### 8.2 Coach Client Detail
Route: `/coach/clients/:clientId`

Purpose: Coach manages one associated client.

Tabs/sections:
1. Overview
2. Meals
3. Daily Activities
4. Measurements
5. Checklist History / Notes

#### Meals panel
Coach can add meals and assign them to the selected client.

Form fields:
- Meal name
- Category: breakfast, lunch, dinner, dessert
- Description raw text

API:

```http
GET /api/coach/clients/{clientId}/meals?page=1&pageSize=20&category=breakfast
POST /api/coach/clients/{clientId}/meals
PATCH /api/coach/clients/{clientId}/meals/{mealId}
DELETE /api/coach/clients/{clientId}/meals/{mealId}
```

Create request:

```json
{
  "name": "Greek Yogurt Bowl",
  "category": "breakfast",
  "description": "Plain Greek yogurt, blueberries, chia seeds, and honey."
}
```

Rules:
- Meal must belong to the coach who created it.
- Meal must be assigned to the client in the same transaction.
- Description is raw text and must be escaped when rendered.

#### Daily activities panel
Coach can assign daily activities to the selected client.

Form fields:
- Title, e.g. “10k steps”
- Optional description
- Active from date, default today
- Optional active until date
- Repeats daily, default true

API:

```http
GET /api/coach/clients/{clientId}/tasks?active=true
POST /api/coach/clients/{clientId}/tasks
PATCH /api/coach/clients/{clientId}/tasks/{taskId}
DELETE /api/coach/clients/{clientId}/tasks/{taskId}
```

Create request:

```json
{
  "title": "10k steps",
  "description": "Aim for 10,000 total steps today.",
  "activeFrom": "2026-07-04",
  "activeUntil": null,
  "repeatsDaily": true
}
```

#### Measurements panel
Coach can view all health-related data for this associated client.

API:

```http
GET /api/coach/clients/{clientId}/measurement-types
GET /api/coach/clients/{clientId}/measurements?typeKey=body_weight&startDate=2026-06-04&endDate=2026-07-04&unitKey=lb
```

Coach cannot edit client measurements in MVP unless explicitly requested later.

#### Checklist history and notes panel
Coach can view daily completion records and notes.

API:

```http
GET /api/coach/clients/{clientId}/checklist-history?startDate=2026-06-04&endDate=2026-07-04
GET /api/coach/clients/{clientId}/daily-notes?startDate=2026-06-04&endDate=2026-07-04
```

Acceptance criteria:
- Coach cannot access unassociated clients by URL guessing.
- All client detail endpoints enforce coach-client association.
- Coach sees measurements, task completion history, and notes.
- Coach can create meal and task assignments.

## 9. Admin Feature Specifications

### 9.1 Admin Login
Route: `/admin/login`

- Separate visual page from normal `/login`.
- Uses same auth backend endpoint, but frontend must reject non-admin role after login.
- If login succeeds as admin, redirect to `/admin`.
- If user is client/coach, show “Admin access required” and clear auth state.

### 9.2 Admin Dashboard
Route: `/admin`

Cards:
- Total clients
- Total coaches
- Total admins
- Recent users
- Quick links to create coach, elevate user, delete account

### 9.3 Create Coach Account
Route: `/admin/users` or form on `/admin`

Required fields:
- Username
- First name
- Last name
- Password
- Confirm password

API:

```http
POST /api/admin/coaches
```

Request:

```json
{
  "username": "coachanna",
  "firstName": "Anna",
  "lastName": "Coach",
  "password": "secure-password",
  "passwordConfirm": "secure-password"
}
```

Rules:
- Only admins can call this.
- Username must be unique case-insensitively.
- Created role is `coach`.

### 9.4 Elevate Existing Client to Coach
API:

```http
PATCH /api/admin/users/{userId}/role
```

Request:

```json
{
  "role": "coach"
}
```

Rules:
- Allow only `client -> coach` elevation in MVP.
- Do not allow admin to accidentally demote admin through this endpoint.
- Preserve user account details.
- Historical client data can remain in the database, but the user will now see coach UI after login.

### 9.5 Delete Any Account
API:

```http
DELETE /api/admin/users/{userId}
```

Request:

```json
{
  "adminPassword": "admin-current-password",
  "confirmUsername": "targetusername"
}
```

Rules:
- Requires admin’s current password.
- Requires typing the target username exactly.
- Deleting a user cascades associated app data.
- Admin cannot delete their own account through this endpoint. They can delete self through `/api/me` if desired, but protect against deleting the only admin in the system.
- Do not allow deletion of the last admin account.

### 9.6 Admin Change Password
Use shared `/api/me/change-password` endpoint. Admin settings route should expose this.

## 10. Backend Architecture

### Backend folder structure

```txt
backend/
  app/
    __init__.py
    main.py
    api/
      __init__.py
      deps.py
      error_handlers.py
      routers/
        auth.py
        me.py
        meals.py
        measurements.py
        checklist.py
        coach.py
        admin.py
    core/
      config.py
      security.py
      tokens.py
      cors.py
    db/
      base.py
      session.py
      models.py
      migrations/
        env.py
        versions/
    schemas/
      auth.py
      users.py
      meals.py
      measurements.py
      checklist.py
      coach.py
      admin.py
      common.py
    services/
      auth_service.py
      user_service.py
      meal_service.py
      measurement_service.py
      checklist_service.py
      coach_service.py
      admin_service.py
      unit_conversion.py
    repositories/
      users.py
      meals.py
      measurements.py
      checklist.py
      coach_clients.py
      audit_logs.py
    scripts/
      create_initial_admin.py
      seed_reference_data.py
  tests/
    test_auth.py
    test_permissions.py
    test_meals.py
    test_measurements.py
    test_checklist.py
    test_coach.py
    test_admin.py
  alembic.ini
  pyproject.toml
  requirements.txt
  vercel.json
```

### Backend dependencies
Use Python 3.12+.

Recommended `requirements.txt`:

```txt
fastapi>=0.117.1
uvicorn[standard]>=0.30.0
pydantic>=2.8.0
pydantic-settings>=2.4.0
SQLAlchemy[asyncio]>=2.0.0
asyncpg>=0.29.0
alembic>=1.13.0
PyJWT[crypto]>=2.8.0
pwdlib[argon2]>=0.2.0
python-multipart>=0.0.9
orjson>=3.10.0
```

Recommended dev dependencies in `pyproject.toml`:

```toml
[project.optional-dependencies]
dev = [
  "pytest>=8.0.0",
  "pytest-asyncio>=0.23.0",
  "httpx>=0.27.0",
  "ruff>=0.5.0",
  "mypy>=1.10.0"
]
```

### FastAPI app entrypoint
`backend/app/main.py` must export a top-level `app` variable:

```py
from fastapi import FastAPI
from app.api.routers import auth, me, meals, measurements, checklist, coach, admin
from app.core.cors import configure_cors
from app.api.error_handlers import register_error_handlers

app = FastAPI(title="Fitness Coaching API", version="1.0.0")

configure_cors(app)
register_error_handlers(app)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(me.router, prefix="/api/me", tags=["me"])
app.include_router(meals.router, prefix="/api/me/meals", tags=["client meals"])
app.include_router(measurements.router, prefix="/api/me", tags=["client measurements"])
app.include_router(checklist.router, prefix="/api/me", tags=["client checklist"])
app.include_router(coach.router, prefix="/api/coach", tags=["coach"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}
```

### Vercel backend entrypoint configuration
Because the Vercel project root will be `backend/`, add this to `backend/pyproject.toml`:

```toml
[project]
name = "fitness-coaching-api"
version = "1.0.0"
requires-python = ">=3.12"

[tool.vercel]
entrypoint = "app.main:app"
```

Use `backend/vercel.json`:

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "functions": {
    "app/main.py": {
      "maxDuration": 60,
      "excludeFiles": "{tests/**,__tests__/**,**/*.test.py,**/test_*.py,fixtures/**,__fixtures__/**,testdata/**,sample-data/**,static/**,assets/**}"
    }
  }
}
```

If Vercel cannot resolve `app/main.py` with the custom entrypoint, simplify by removing the custom entrypoint and ensuring `app/main.py` directly exports `app` as shown above. Do not create multiple serverless functions for each route. Keep one FastAPI app/function.

### Configuration
Use `pydantic-settings`.

Required backend environment variables:

```txt
ENVIRONMENT=development|preview|production
DATABASE_URL=postgresql+asyncpg://...
DB_POOL_MODE=serverless|persistent
JWT_SECRET=generate-a-long-random-secret-at-least-32-bytes
ACCESS_TOKEN_MINUTES=15
REFRESH_TOKEN_DAYS=30
CORS_ORIGINS=http://localhost:5173,https://your-frontend.vercel.app
COOKIE_DOMAIN=
COOKIE_SECURE=false for local, true for production
INITIAL_ADMIN_USERNAME=admin
INITIAL_ADMIN_FIRST_NAME=Admin
INITIAL_ADMIN_LAST_NAME=User
INITIAL_ADMIN_PASSWORD=change-this-before-production
```

Rules:
- In production, `COOKIE_SECURE=true`.
- In production, `CORS_ORIGINS` must not be `*` when credentials are enabled.
- If backend and frontend are on different domains, refresh cookie must use `SameSite=None; Secure`.
- For local dev, use `SameSite=Lax; Secure=false`.

### Database session
Use async SQLAlchemy.

For Vercel/serverless deployment, prefer Neon’s pooled connection string and set SQLAlchemy `poolclass=NullPool` so the external pooler handles pooling. For Railway/persistent deployment, use normal pooling.

Pseudo-code:

```py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

engine_kwargs = {"pool_pre_ping": True}
if settings.DB_POOL_MODE == "serverless":
    engine_kwargs["poolclass"] = NullPool

engine = create_async_engine(settings.DATABASE_URL, **engine_kwargs)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
```

### Dependency injection
Use FastAPI dependencies:

```py
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

async def get_current_user(...):
    ...

def require_roles(*roles: str):
    async def dependency(current_user = Depends(get_current_user)):
        if current_user.role not in roles:
            raise ForbiddenError("Insufficient permissions")
        return current_user
    return dependency
```

Helper:

```py
async def assert_coach_has_client(db: AsyncSession, coach_id: UUID, client_id: UUID) -> None:
    # Query coach_clients and raise 403 if missing.
```

### Error format
Implement consistent errors:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Value must be greater than zero.",
    "details": {}
  }
}
```

Map common cases:
- 400: invalid request/business rule violation
- 401: unauthenticated/token invalid
- 403: authenticated but not allowed
- 404: resource not found or not visible to this user
- 409: conflict, e.g. duplicate username or existing coach-client relation
- 422: validation error

Do not leak internal errors. Log them server-side without sensitive values.

## 11. Authentication and Security

### Password rules
Registration and account creation must require:
- Username
- First name
- Last name
- Password
- Password confirmation

Password validation:
- Minimum length: 10 characters
- Must match confirmation
- Do not log passwords
- Hash using Argon2id through `pwdlib[argon2]` or equivalent Argon2 library

Username validation:
- Case-insensitive unique username
- 3-30 characters
- Allowed characters: letters, numbers, underscore, hyphen, period
- Store using Postgres `CITEXT` or lower-case uniqueness index

### Token strategy
- Login validates username/password.
- Backend returns short-lived access token in JSON.
- Backend sets refresh token as HttpOnly cookie.
- Store refresh token hash in `refresh_tokens` table.
- Refresh endpoint rotates refresh token: revoke old, create new, set new cookie.
- Logout revokes refresh token and clears cookie.
- Frontend stores access token only in memory.

### Account deletion
- User self-delete requires current password.
- Admin deletion requires admin password and typed target username.
- Delete refresh tokens with cascade.
- Delete associated records with cascade.
- Do not retain personal data unless explicitly required later.

### Security headers/frontend
Frontend should include reasonable meta tags and avoid exposing secrets.
Do not put secret values in `VITE_*` env variables. Only public frontend values may use `VITE_`.

### Service worker security
The PWA service worker must not cache authenticated API responses. Cache static assets only. Use network-only or no caching for `/api/*`.

## 12. Database Schema

Use PostgreSQL. Use Alembic migrations, not manual schema changes after the initial migration.

### Initial SQL model reference
This SQL is the target schema. Implement it through Alembic/SQLAlchemy models.

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS citext;

CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  username CITEXT NOT NULL UNIQUE,
  first_name TEXT NOT NULL CHECK (char_length(first_name) BETWEEN 1 AND 80),
  last_name TEXT NOT NULL CHECK (char_length(last_name) BETWEEN 1 AND 80),
  password_hash TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('client', 'coach', 'admin')),
  avatar_key TEXT NOT NULL DEFAULT 'avocado',
  timezone TEXT NOT NULL DEFAULT 'America/Los_Angeles',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_created_at ON users(created_at DESC);

CREATE TABLE refresh_tokens (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  token_hash TEXT NOT NULL UNIQUE,
  expires_at TIMESTAMPTZ NOT NULL,
  revoked_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_used_at TIMESTAMPTZ,
  user_agent TEXT,
  ip_hash TEXT
);

CREATE INDEX idx_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_expires_at ON refresh_tokens(expires_at);

CREATE TABLE coach_clients (
  coach_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  client_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  assigned_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (coach_id, client_id),
  CHECK (coach_id <> client_id)
);

CREATE INDEX idx_coach_clients_client_id ON coach_clients(client_id);

CREATE TABLE meal_categories (
  key TEXT PRIMARY KEY,
  display_name TEXT NOT NULL,
  sort_order INTEGER NOT NULL DEFAULT 0,
  active BOOLEAN NOT NULL DEFAULT true
);

INSERT INTO meal_categories (key, display_name, sort_order) VALUES
  ('breakfast', 'Breakfast', 10),
  ('lunch', 'Lunch', 20),
  ('dinner', 'Dinner', 30),
  ('dessert', 'Dessert', 40);

CREATE TABLE meals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  coach_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name TEXT NOT NULL CHECK (char_length(name) BETWEEN 1 AND 160),
  category_key TEXT NOT NULL REFERENCES meal_categories(key),
  description TEXT NOT NULL DEFAULT '',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_meals_coach_id ON meals(coach_id);
CREATE INDEX idx_meals_category_key ON meals(category_key);
CREATE INDEX idx_meals_created_at ON meals(created_at DESC);

CREATE TABLE meal_assignments (
  meal_id UUID NOT NULL REFERENCES meals(id) ON DELETE CASCADE,
  client_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  assigned_by_coach_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  assigned_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (meal_id, client_id)
);

CREATE INDEX idx_meal_assignments_client_assigned_at ON meal_assignments(client_id, assigned_at DESC);

CREATE TABLE measurement_units (
  key TEXT PRIMARY KEY,
  dimension TEXT NOT NULL CHECK (dimension IN ('weight', 'length', 'count')),
  display_name TEXT NOT NULL,
  symbol TEXT NOT NULL,
  system TEXT NOT NULL CHECK (system IN ('imperial', 'metric', 'none')),
  to_base_multiplier NUMERIC(18,10) NOT NULL DEFAULT 1,
  to_base_offset NUMERIC(18,10) NOT NULL DEFAULT 0
);

INSERT INTO measurement_units (key, dimension, display_name, symbol, system, to_base_multiplier) VALUES
  ('kg', 'weight', 'Kilograms', 'kg', 'metric', 1),
  ('lb', 'weight', 'Pounds', 'lbs', 'imperial', 0.45359237),
  ('cm', 'length', 'Centimeters', 'cm', 'metric', 1),
  ('in', 'length', 'Inches', 'in', 'imperial', 2.54),
  ('count', 'count', 'Count', '', 'none', 1);

CREATE TABLE measurement_types (
  key TEXT PRIMARY KEY,
  display_name TEXT NOT NULL,
  dimension TEXT NOT NULL CHECK (dimension IN ('weight', 'length', 'count')),
  default_unit_key TEXT NOT NULL REFERENCES measurement_units(key),
  sort_order INTEGER NOT NULL DEFAULT 0,
  active BOOLEAN NOT NULL DEFAULT true
);

INSERT INTO measurement_types (key, display_name, dimension, default_unit_key, sort_order) VALUES
  ('body_weight', 'Body Weight', 'weight', 'lb', 10),
  ('waist', 'Waist', 'length', 'in', 20),
  ('hips', 'Hips', 'length', 'in', 30),
  ('thigh', 'Thigh', 'length', 'in', 40);

CREATE TABLE measurement_records (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  measurement_type_key TEXT NOT NULL REFERENCES measurement_types(key),
  value_input NUMERIC(12,4) NOT NULL CHECK (value_input > 0),
  unit_key TEXT NOT NULL REFERENCES measurement_units(key),
  value_base NUMERIC(12,4) NOT NULL CHECK (value_base > 0),
  source TEXT NOT NULL DEFAULT 'manual' CHECK (source IN ('manual', 'coach_entered', 'health_connect', 'samsung_health')),
  recorded_at TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_measurement_records_client_type_recorded ON measurement_records(client_id, measurement_type_key, recorded_at ASC);
CREATE INDEX idx_measurement_records_client_recorded ON measurement_records(client_id, recorded_at DESC);

CREATE TABLE assigned_tasks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  coach_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  client_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title TEXT NOT NULL CHECK (char_length(title) BETWEEN 1 AND 160),
  description TEXT NOT NULL DEFAULT '',
  active_from DATE NOT NULL DEFAULT CURRENT_DATE,
  active_until DATE,
  repeats_daily BOOLEAN NOT NULL DEFAULT true,
  archived_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (active_until IS NULL OR active_until >= active_from)
);

CREATE INDEX idx_assigned_tasks_client_active ON assigned_tasks(client_id, active_from, active_until, archived_at);
CREATE INDEX idx_assigned_tasks_coach ON assigned_tasks(coach_id);

CREATE TABLE task_completions (
  task_id UUID NOT NULL REFERENCES assigned_tasks(id) ON DELETE CASCADE,
  client_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  completion_date DATE NOT NULL,
  completed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (task_id, completion_date)
);

CREATE INDEX idx_task_completions_client_date ON task_completions(client_id, completion_date DESC);

CREATE TABLE daily_notes (
  client_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  note_date DATE NOT NULL,
  body TEXT NOT NULL DEFAULT '',
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (client_id, note_date)
);

CREATE INDEX idx_daily_notes_client_date ON daily_notes(client_id, note_date DESC);

CREATE TABLE audit_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  actor_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  target_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  action TEXT NOT NULL,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at DESC);
CREATE INDEX idx_audit_logs_actor ON audit_logs(actor_user_id);
CREATE INDEX idx_audit_logs_target ON audit_logs(target_user_id);

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated_at BEFORE UPDATE ON users
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_meals_updated_at BEFORE UPDATE ON meals
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_assigned_tasks_updated_at BEFORE UPDATE ON assigned_tasks
FOR EACH ROW EXECUTE FUNCTION set_updated_at();
```

### Database role constraints
The database cannot easily enforce that `coach_clients.coach_id` points to a user with role `coach` and `client_id` points to `client` without triggers. Enforce this in service-layer code and tests.

### Unit conversion rules
- Weight base unit: kg.
- Length base unit: cm.
- Store the user’s raw input in `value_input` and `unit_key`.
- Store normalized value in `value_base`.
- When returning chart data, convert `value_base` back into the requested unit.
- Do not mutate historical records when a user changes display preferences.

## 13. API Specification

All API routes return JSON. All protected routes require `Authorization: Bearer <accessToken>` except refresh/logout can also rely on refresh cookie.

### 13.1 Auth endpoints

#### Register client
```http
POST /api/auth/register
```

Request:
```json
{
  "username": "samfit",
  "firstName": "Sam",
  "lastName": "Rivera",
  "password": "secure-password",
  "passwordConfirm": "secure-password",
  "timezone": "America/Los_Angeles"
}
```

Response `201`:
```json
{
  "user": {
    "id": "uuid",
    "username": "samfit",
    "firstName": "Sam",
    "lastName": "Rivera",
    "role": "client",
    "avatarKey": "avocado",
    "timezone": "America/Los_Angeles"
  },
  "accessToken": "jwt"
}
```

#### Login
```http
POST /api/auth/login
```

Request:
```json
{
  "username": "samfit",
  "password": "secure-password"
}
```

Response `200`:
```json
{
  "user": {
    "id": "uuid",
    "username": "samfit",
    "firstName": "Sam",
    "lastName": "Rivera",
    "role": "client",
    "avatarKey": "avocado",
    "timezone": "America/Los_Angeles"
  },
  "accessToken": "jwt"
}
```

Also sets refresh cookie.

#### Refresh
```http
POST /api/auth/refresh
```

Response:
```json
{
  "accessToken": "new-jwt"
}
```

Rotates refresh token.

#### Logout
```http
POST /api/auth/logout
```

Revokes current refresh token and clears cookie.

#### Current user
```http
GET /api/auth/me
```

Returns current public user profile.

### 13.2 Shared profile endpoints

```http
PUT /api/me
POST /api/me/change-password
DELETE /api/me
```

Change password request:

```json
{
  "currentPassword": "old-password",
  "newPassword": "new-secure-password",
  "newPasswordConfirm": "new-secure-password"
}
```

### 13.3 Client meals

```http
GET /api/me/meals?page=1&pageSize=10&category=breakfast
```

Rules:
- Default page: 1.
- Default page size: 10.
- Max page size: 50.
- Category optional.
- Category must match active `meal_categories.key`.

### 13.4 Client measurements

```http
GET /api/me/measurement-types
POST /api/me/measurements
GET /api/me/measurements?typeKey=body_weight&startDate=2026-06-04&endDate=2026-07-04&unitKey=lb
```

### 13.5 Client checklist and notes

```http
GET /api/me/checklist?date=2026-07-04
PATCH /api/me/checklist/{taskId}/completion
PUT /api/me/daily-note
```

### 13.6 Coach endpoints

```http
GET /api/coach/clients?search=&page=1&pageSize=20
GET /api/coach/client-search?query=sam
POST /api/coach/clients
DELETE /api/coach/clients/{clientId}
GET /api/coach/clients/{clientId}/summary
GET /api/coach/clients/{clientId}/meals?page=1&pageSize=20&category=breakfast
POST /api/coach/clients/{clientId}/meals
PATCH /api/coach/clients/{clientId}/meals/{mealId}
DELETE /api/coach/clients/{clientId}/meals/{mealId}
GET /api/coach/clients/{clientId}/tasks?active=true
POST /api/coach/clients/{clientId}/tasks
PATCH /api/coach/clients/{clientId}/tasks/{taskId}
DELETE /api/coach/clients/{clientId}/tasks/{taskId}
GET /api/coach/clients/{clientId}/measurement-types
GET /api/coach/clients/{clientId}/measurements?typeKey=body_weight&startDate=2026-06-04&endDate=2026-07-04&unitKey=lb
GET /api/coach/clients/{clientId}/checklist-history?startDate=2026-06-04&endDate=2026-07-04
GET /api/coach/clients/{clientId}/daily-notes?startDate=2026-06-04&endDate=2026-07-04
```

Every `/api/coach/clients/{clientId}/...` endpoint must first verify coach-client association.

### 13.7 Admin endpoints

```http
GET /api/admin/users?role=client&search=sam&page=1&pageSize=20
POST /api/admin/coaches
PATCH /api/admin/users/{userId}/role
DELETE /api/admin/users/{userId}
GET /api/admin/stats
```

Admin stats response:

```json
{
  "clients": 120,
  "coaches": 8,
  "admins": 1,
  "recentUsers": [
    {
      "id": "uuid",
      "username": "samfit",
      "firstName": "Sam",
      "lastName": "Rivera",
      "role": "client",
      "createdAt": "2026-07-04T18:30:00Z"
    }
  ]
}
```

## 14. PWA Requirements

### Manifest
Use `vite-plugin-pwa` and include a web manifest.

Manifest values:

```json
{
  "name": "Elevate Fitness",
  "short_name": "Elevate",
  "description": "Fitness coaching, meal plans, habits, and body data tracking.",
  "start_url": "/",
  "scope": "/",
  "display": "standalone",
  "background_color": "#FFFFFF",
  "theme_color": "#00B8D9",
  "icons": [
    {
      "src": "/icons/icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-512.png",
      "sizes": "512x512",
      "type": "image/png"
    },
    {
      "src": "/icons/maskable-512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "maskable"
    }
  ]
}
```

### Required icon assets
Create all these files:

```txt
frontend/public/icons/favicon.svg
frontend/public/icons/icon-192.png
frontend/public/icons/icon-512.png
frontend/public/icons/maskable-512.png
frontend/public/icons/apple-touch-icon.png
```

Also add in `index.html`:

```html
<link rel="manifest" href="/manifest.webmanifest" />
<link rel="apple-touch-icon" href="/icons/apple-touch-icon.png" />
<meta name="theme-color" content="#00B8D9" />
<meta name="mobile-web-app-capable" content="yes" />
<meta name="apple-mobile-web-app-capable" content="yes" />
<meta name="apple-mobile-web-app-status-bar-style" content="default" />
<meta name="apple-mobile-web-app-title" content="Elevate" />
```

### Service worker strategy
- Precache static frontend assets.
- Do not cache `/api/*` responses.
- Show an offline fallback only for static shell if feasible.
- If user is offline and attempts to save data, show a clear network error. Do not silently queue health data in MVP.

## 15. Deployment Instructions

The final README must include these steps exactly, with project-specific names filled in by implementation.

### 15.1 Local development prerequisites
Install:
- Node.js LTS
- npm
- Python 3.12+
- Git
- PostgreSQL locally or Docker
- Vercel CLI
- Optional Railway CLI for fallback deployment

### 15.2 Clone and install

```bash
git clone <repo-url>
cd <repo-name>

cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e ".[dev]"

cd ../frontend
npm install
```

### 15.3 Local database
Option A: local Postgres.

Create database:

```bash
createdb fitness_app_dev
```

Backend `.env`:

```txt
ENVIRONMENT=development
DATABASE_URL=postgresql+asyncpg://localhost:5432/fitness_app_dev
DB_POOL_MODE=persistent
JWT_SECRET=local-dev-secret-change-this
ACCESS_TOKEN_MINUTES=15
REFRESH_TOKEN_DAYS=30
CORS_ORIGINS=http://localhost:5173
COOKIE_SECURE=false
INITIAL_ADMIN_USERNAME=admin
INITIAL_ADMIN_FIRST_NAME=Admin
INITIAL_ADMIN_LAST_NAME=User
INITIAL_ADMIN_PASSWORD=ChangeMe12345
```

Run migrations and seed:

```bash
cd backend
source .venv/bin/activate
alembic upgrade head
python -m app.scripts.seed_reference_data
python -m app.scripts.create_initial_admin
```

Run backend:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend `.env.local`:

```txt
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Run frontend:

```bash
cd frontend
npm run dev
```

### 15.4 Production database on Neon
1. Create a Neon account.
2. Create a new Neon Postgres project.
3. Copy the pooled connection string if available for serverless deployment.
4. Convert the connection string to SQLAlchemy async format:
   - From: `postgresql://user:pass@host/db?sslmode=require`
   - To: `postgresql+asyncpg://user:pass@host/db?ssl=require`
5. Save this as `DATABASE_URL` in backend hosting environment.
6. Use `DB_POOL_MODE=serverless` for Vercel backend.
7. Run migrations against production database:

```bash
cd backend
source .venv/bin/activate
DATABASE_URL="postgresql+asyncpg://..." alembic upgrade head
DATABASE_URL="postgresql+asyncpg://..." python -m app.scripts.seed_reference_data
DATABASE_URL="postgresql+asyncpg://..." python -m app.scripts.create_initial_admin
```

Important:
- The Neon free tier is appropriate for MVP/prototype. Monitor storage and compute usage.
- Do not commit database URLs or secrets.

### 15.5 Deploy backend to Vercel
Use a separate Vercel project for `backend/`.

Steps:
1. Push repository to GitHub.
2. In Vercel, create a new project.
3. Import the GitHub repository.
4. Set Root Directory to `backend`.
5. Framework preset can be left as auto-detected/Other for Python/FastAPI.
6. Ensure `backend/app/main.py` exports `app` and `backend/pyproject.toml` has `[tool.vercel] entrypoint = "app.main:app"`.
7. Add environment variables:

```txt
ENVIRONMENT=production
DATABASE_URL=<Neon async pooled URL>
DB_POOL_MODE=serverless
JWT_SECRET=<long random secret>
ACCESS_TOKEN_MINUTES=15
REFRESH_TOKEN_DAYS=30
CORS_ORIGINS=https://<frontend-project>.vercel.app
COOKIE_SECURE=true
COOKIE_DOMAIN=
INITIAL_ADMIN_USERNAME=<admin username>
INITIAL_ADMIN_FIRST_NAME=<admin first name>
INITIAL_ADMIN_LAST_NAME=<admin last name>
INITIAL_ADMIN_PASSWORD=<temporary strong password>
```

8. Deploy.
9. Visit:

```txt
https://<backend-project>.vercel.app/api/health
```

Expected:

```json
{"status":"ok"}
```

10. After frontend is deployed, update `CORS_ORIGINS` with the final frontend production URL and redeploy backend.

### 15.6 Deploy frontend to Vercel
Use a separate Vercel project for `frontend/`.

Steps:
1. In Vercel, create a new project.
2. Import the same GitHub repository.
3. Set Root Directory to `frontend`.
4. Framework Preset: Vite.
5. Build Command: `npm run build`.
6. Output Directory: `dist`.
7. Install Command: `npm install`.
8. Add environment variable:

```txt
VITE_API_BASE_URL=https://<backend-project>.vercel.app
```

9. Deploy.
10. Visit frontend production URL.
11. Test login, registration, and `/api/health` connectivity.
12. On mobile Chrome/Safari, test add-to-home-screen and verify app icon appears.

### 15.7 Backend fallback: deploy FastAPI to Railway
Use this only if Vercel Python serverless constraints cause issues.

Required backend start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Steps:
1. In Railway, create a new project.
2. Deploy from GitHub repository.
3. Set service root directory to `backend` if using monorepo.
4. Set environment variables same as Vercel, except:

```txt
DB_POOL_MODE=persistent
COOKIE_SECURE=true
CORS_ORIGINS=https://<frontend-project>.vercel.app
```

5. Set start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

6. In Railway service networking settings, generate a public domain.
7. Run migrations. Prefer Railway pre-deploy command if configured:

```bash
alembic upgrade head && python -m app.scripts.seed_reference_data
```

8. Update frontend `VITE_API_BASE_URL` to the Railway backend URL and redeploy frontend.
9. Update backend `CORS_ORIGINS` if needed.

## 16. README Requirements

The generated project must include a `README.md` at repository root with:

1. App summary
2. Tech stack
3. Folder structure
4. Local setup
5. Environment variable list for frontend and backend
6. Database setup and migrations
7. How to create initial admin
8. How to run tests
9. How to deploy frontend on Vercel
10. How to deploy backend on Vercel
11. Railway backend fallback instructions
12. PWA icon requirements
13. Known limitation: Samsung/Galaxy Watch direct PWA integration is not included in MVP
14. Troubleshooting section

## 17. Testing Requirements

### Backend tests
Use pytest and httpx AsyncClient.

Required test cases:
- Register creates client role only.
- Duplicate username fails case-insensitively.
- Login succeeds with correct password.
- Login fails with wrong password.
- Access protected endpoint without token returns 401.
- Client cannot access another client’s data.
- Coach can access associated client data.
- Coach cannot access unassociated client data.
- Admin can create coach.
- Admin can elevate client to coach.
- Admin cannot delete last admin.
- Meal pagination defaults to 10.
- Meal category filter queries correct results.
- Measurement record saves with normalized base value.
- Measurement query rejects ranges longer than 1095 days.
- Checklist completion persists.
- Confetti itself is frontend-only, but backend completion state is tested.
- Daily notes persist and are visible through coach endpoint.
- Delete account removes user data and tokens.

### Frontend tests
Use Vitest + Testing Library for key components:
- Bottom nav renders four correct tabs with SVG icons.
- Meal filters call query with category and reset page.
- Add measurement modal validates numeric value.
- Checklist page triggers completion mutation when checkbox changes.
- Profile delete account form requires password.
- Auth guard redirects unauthenticated users.
- Admin route rejects non-admin user.

### Manual QA checklist
- Mobile viewport 390x844.
- iPhone Safari add-to-home-screen icon.
- Android Chrome PWA install prompt/icon.
- Keyboard does not cover critical form fields.
- Bottom nav remains visible and usable.
- No emoji icons anywhere.
- No horizontal scrolling on client pages.
- Auth tokens are not in localStorage.
- API responses do not include password hashes.
- Meal descriptions render text safely.

## 18. Implementation Order for Cursor

Implement in this order. Do not start with UI polish before data/auth basics exist.

### Phase 1: Project scaffolding
1. Create monorepo structure.
2. Create Vite React TypeScript frontend.
3. Add Tailwind.
4. Add FastAPI backend.
5. Add lint/test tooling.
6. Add README skeleton.

### Phase 2: Database and backend foundations
1. Add SQLAlchemy models.
2. Add Alembic.
3. Create initial migration.
4. Add seed script for categories/units/types.
5. Add initial admin script.
6. Add config, DB session, error handlers.

### Phase 3: Auth and profile
1. Register/login/refresh/logout/me.
2. Role-based dependencies.
3. Profile update.
4. Change password.
5. Delete self.
6. Frontend auth provider and route guards.

### Phase 4: Client app
1. Client layout and bottom nav.
2. Meal plan page.
3. Data page with measurement types, chart, add modal.
4. Checklist page with task completions, notes, confetti.
5. Profile page with avatar picker.
6. PWA manifest/icons/service worker.

### Phase 5: Coach app
1. Coach client list/search/add.
2. Coach client detail page.
3. Meals CRUD/assignment.
4. Tasks CRUD.
5. Measurements/notes/history viewing.

### Phase 6: Admin app
1. Admin login page.
2. Admin stats/dashboard.
3. User list/search.
4. Create coach.
5. Elevate client.
6. Delete account with safety confirmations.
7. Admin settings/password.

### Phase 7: Deployment and QA
1. Confirm local migrations/tests pass.
2. Deploy database.
3. Deploy backend.
4. Deploy frontend.
5. Confirm PWA icons.
6. Update README with actual deployment URLs/placeholders.
7. Run manual QA checklist.

## 19. Code Quality Standards

### Backend
- Use service layer for business logic.
- Use repository layer for complex queries.
- Use Pydantic schemas for input/output validation.
- Use FastAPI dependencies for auth/roles.
- Keep routers thin.
- Use transactions for multi-table changes such as creating meal + assignment.
- Use meaningful error codes.
- Do not catch broad exceptions unless logging and returning safe error.
- Do not commit secrets.
- Use Ruff for formatting/linting.

### Frontend
- Use strict TypeScript.
- Use reusable components.
- Use feature folders.
- Use TanStack Query for server state.
- Use React Hook Form + Zod for forms.
- Avoid prop drilling where auth state can be provided by context.
- Avoid global CSS except Tailwind base/theme and app-level tokens.
- Make all interactive controls keyboard accessible.
- Add aria-labels to icon-only buttons.
- Use SVG icons from approved open-source package or project SVG assets.

## 20. Acceptance Criteria by Product Area

### Auth
- Clients can self-register.
- Coaches and clients log in from same normal login page.
- Admin has separate admin login page.
- Role redirects work.
- Passwords are hashed.
- Refresh token rotation works.

### Meals
- Coach can create meal for associated client.
- Client sees assigned meals.
- Pagination works with 10 default.
- Filters query backend.

### Measurements/data
- Client can add measurement record from plus icon.
- Type/unit/value/datetime saved.
- Graph updates after save.
- Time range filters work.
- Backend enforces 3-year maximum.
- Measurement types are scalable/data-driven.

### Checklist
- Client sees coach-assigned tasks.
- Checkbox on right side.
- Completion stored by date.
- Confetti triggers when all tasks complete.
- Daily notes save and coach can view.

### Profile
- User can choose among 12 healthy food-character avatars.
- User can edit account info.
- User can change password.
- User can delete account with password confirmation.

### Coach
- Coach can add existing clients.
- Coach can click client and manage meals/tasks.
- Coach can view health data, task history, and notes.
- Coach cannot access unassociated clients.

### Admin
- Admin can create coach account.
- Admin can elevate client to coach.
- Admin can delete accounts with safety confirmation.
- Admin can change password.
- Admin page is distinct from normal login/client/coach views.

### PWA/mobile
- PWA has manifest and icons for homescreen installation.
- Bottom nav works on mobile.
- UI is clean, white/cyan-blue, black text.
- No emoji icons.

## 21. Known Non-MVP Items

Do not implement these unless requested later:
- Native Samsung Health/Galaxy Watch syncing.
- Payments/subscriptions.
- In-app chat/messaging.
- Push notifications.
- Email password resets.
- Food macro database or calorie calculations.
- File/image upload for meal photos.
- Multi-tenant organization billing.

The database design should not prevent these from being added later, but the MVP should stay focused.

