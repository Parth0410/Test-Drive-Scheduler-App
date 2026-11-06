# Frontend - BGSW MOTO-TORQUE Test Ride Booking

Modern, responsive front-end web application built using **vanilla HTML5, CSS3, and ES Modules** (no external frameworks or libraries).

---

## 1. Overview & Features

- **Customer Booking Flow (`index.html`)**:
  - Stepped progressive form unlocking steps 1 through 5.
  - **Dependent Cascading Dropdowns**: Vehicle Type $\rightarrow$ Brand $\rightarrow$ Model $\rightarrow$ Variant.
  - **Availability Badge**: Highlights variants as *Currently Available* or *Currently Unavailable*. Unavailable variants are disabled from selection.
  - **Date Picker**: Constrained to today up to today + 7 days. Same-day bookings are allowed for showroom walk-in tracking.
  - **Time Slot Selector**: Interactive modal showing 14 operating slots (10:00 to 17:00, 30 min each). Real-time booked vs available status with distinct icons and color-blind accessible labels.
  - **Ride Preview Card**: Live-updated summary of all selected parameters.
  - **Contact & Validation**: Real-time validation for email and 10-digit Indian mobile numbers (starting with 6–9).
  - **Double-booking rejection & feedback**: Prevents duplicate slot bookings.
  - **Reach Us**: Modal showing dealer contact details and support information.

- **Dealer Dashboard (`dealer.html`)**:
  - **PIN Security**: Protected access via security PIN verification modal (`2545`).
  - **Summary Metrics**: Today's Rides, Upcoming, Completed, and Total count cards.
  - **Status Tabs**: Separate views for "Current Bookings" (`Booked`) and "History" (`Completed`).
  - **Filters**: Real-time search by customer email, mobile number, or booking reference, plus date filtering.
  - **Ride Completion**: "Completed" action button enabled only after the ride's end time has elapsed.
  - **Responsive Layout**: Data table automatically transforms into stacked cards on mobile screens.

- **Theme Toggle**:
  - Persistent Dark / Light theme switch at top-right corner across all pages.
  - Default theme is dark with automotive racing accents (`#E10600`).
  - Stored in `localStorage`.

---

## 2. File & Directory Structure

```
frontend/
├── index.html                 # Customer booking page
├── dealer.html                # Dealer management dashboard
├── assets/
│   ├── css/
│   │   ├── variables.css      # CSS variables (colors, fonts, dark/light themes)
│   │   ├── base.css           # Typography, resets, base utilities
│   │   ├── layout.css         # Header, brand logo, navigation, page containers
│   │   ├── components.css     # Buttons, inputs, modals, toasts, loaders
│   │   └── pages/
│   │       ├── booking.css    # Booking page specific styles
│   │       └── dealer.css     # Dealer dashboard & data table styles
│   └── js/
│       ├── config.js          # API base URL configuration
│       ├── core/
│       │   ├── http.js        # Generic fetch wrapper with ApiError handling
│       │   ├── dom.js         # DOM query helpers & HTML escaping utilities
│       │   ├── date.js        # Date formatting and ISO string helpers
│       │   └── icons.js       # Inline accessible SVG icons
│       ├── services/
│       │   ├── api.js         # API service layer (the ONLY module talking to backend)
│       │   └── auth.js        # Dealer session token storage & authentication state
│       ├── ui/
│       │   ├── theme.js       # Theme toggle switch controller
│       │   ├── modal.js       # Modal popup controller with keyboard focus trap & ESC handling
│       │   └── toast.js       # Toast notifications controller
│       └── pages/
│           ├── booking.page.js # Controller & state management for index.html
│           └── dealer.page.js  # Controller & data rendering for dealer.html
└── README.md                  # This file
```

---

## 3. How to Run & Test

The frontend is served directly by the backend application at root URL `http://127.0.0.1:8000/`.

1. Start the backend server:
   ```powershell
   cd ../backend
   python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```
2. Open your browser and navigate to:
   - Customer Booking: `http://127.0.0.1:8000/` or `http://127.0.0.1:8000/index.html`
   - Dealer Dashboard: `http://127.0.0.1:8000/dealer.html` (enter PIN **2545** when prompted)

*(Note: If serving the frontend from an independent server such as VS Code Live Server at port 5500, ensure CORS is configured in `backend/.env` under `CORS_ORIGINS`).*
