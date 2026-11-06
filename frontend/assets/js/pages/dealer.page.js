import * as api from '../services/api.js';
import { clearSession, isAuthenticated } from '../services/auth.js';
import { $, $$, escapeHtml } from '../core/dom.js';
import { formatDisplayDate, formatLongDate, toDateTime, toISODate } from '../core/date.js';
import { initTheme } from '../ui/theme.js';
import { showToast } from '../ui/toast.js';

const REFRESH_INTERVAL_MS = 60_000;

const el = {
  dashboard: $('#dashboard'),
  tabs: $$('.tab'),
  dateFilter: $('#date-filter'),
  searchFilter: $('#search-filter'),
  loading: $('#loading-state'),
  empty: $('#empty-state'),
  table: $('#bookings-table'),
  body: $('#bookings-body'),
};

let bookings = [];
let activeStatus = 'Booked';

function redirectToLogin() {
  clearSession();
  window.location.replace('./index.html?dealer');
}

function handleError(error) {
  if (error.status === 401) redirectToLogin();
  else showToast(error.message, 'error');
}

async function loadBookings() {
  try {
    bookings = await api.getBookings();
    render();
  } catch (error) {
    handleError(error);
  } finally {
    el.loading.hidden = true;
  }
}

const rideEnd = (booking) => toDateTime(booking.date, booking.slotEnd);
const rideStart = (booking) => toDateTime(booking.date, booking.slotStart);

function renderSummary() {
  const today = toISODate(new Date());
  const now = new Date();
  $('#count-today').textContent = bookings.filter((b) => b.date === today).length;
  $('#count-upcoming').textContent = bookings.filter((b) => b.status === 'Booked' && rideStart(b) > now).length;
  $('#count-completed').textContent = bookings.filter((b) => b.status === 'Completed').length;
  $('#count-total').textContent = bookings.length;
}

function visibleBookings() {
  const date = el.dateFilter.value;
  const query = el.searchFilter.value.trim().toLowerCase();
  const direction = activeStatus === 'Booked' ? 1 : -1;

  return bookings
    .filter((b) => b.status === activeStatus)
    .filter((b) => !date || b.date === date)
    .filter((b) => !query || [b.email, b.mobile, b.bookingId].some((v) => v.toLowerCase().includes(query)))
    .sort((a, b) => direction * `${a.date}T${a.slotStart}`.localeCompare(`${b.date}T${b.slotStart}`));
}

function createRow(booking) {
  const row = document.createElement('tr');
  const isBooked = booking.status === 'Booked';
  const canComplete = isBooked && rideEnd(booking) <= new Date();
  const vehicle = `${booking.type} - ${booking.brand} - ${booking.model} - ${booking.variant}`;

  row.innerHTML = `
    <td data-label="Booking ID"><strong>${escapeHtml(booking.bookingId)}</strong></td>
    <td data-label="Email">${escapeHtml(booking.email)}</td>
    <td data-label="Mobile">${escapeHtml(booking.mobile)}</td>
    <td data-label="Vehicle">${escapeHtml(vehicle)}</td>
    <td data-label="Date">${escapeHtml(formatDisplayDate(booking.date))}</td>
    <td data-label="Time slot">${escapeHtml(`${booking.slotStart} - ${booking.slotEnd}`)}</td>
    <td data-label="Status"><span class="status-pill ${isBooked ? '' : 'completed'}">${escapeHtml(booking.status)}</span></td>
    <td data-label="Action"></td>`;

  const actionCell = row.lastElementChild;
  if (isBooked) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'complete-button';
    button.textContent = 'Completed';
    button.disabled = !canComplete;
    if (!canComplete) button.title = 'Available after ride time';
    button.addEventListener('click', () => completeBooking(booking, button));
    actionCell.append(button);
  } else {
    actionCell.textContent = '—';
  }
  return row;
}

function render() {
  renderSummary();
  const rows = visibleBookings();
  el.body.replaceChildren(...rows.map(createRow));
  el.table.hidden = rows.length === 0;
  el.empty.hidden = rows.length > 0;
  el.empty.textContent = activeStatus === 'Booked' ? 'No current bookings.' : 'No completed rides yet.';
}

async function completeBooking(booking, button) {
  if (!window.confirm(`Mark booking ${booking.bookingId} as completed?`)) return;
  button.disabled = true;
  try {
    const updated = await api.markCompleted(booking.bookingId);
    bookings = bookings.map((b) => (b.bookingId === updated.bookingId ? updated : b));
    render();
    showToast('Booking moved to History.', 'success');
  } catch (error) {
    button.disabled = false;
    handleError(error);
  }
}

function selectTab(tab) {
  activeStatus = tab.dataset.status;
  el.tabs.forEach((t) => t.setAttribute('aria-selected', String(t === tab)));
  $('#bookings-region').setAttribute('aria-labelledby', tab.id);
  render();
}

function init() {
  initTheme();
  if (!isAuthenticated()) {
    redirectToLogin();
    return;
  }

  el.dashboard.hidden = false;
  $('#today-label').textContent = formatLongDate();

  el.tabs.forEach((tab) => tab.addEventListener('click', () => selectTab(tab)));
  el.dateFilter.addEventListener('change', render);
  el.searchFilter.addEventListener('input', render);
  $('#clear-date').addEventListener('click', () => {
    el.dateFilter.value = '';
    render();
  });
  $('#logout-button').addEventListener('click', () => {
    clearSession();
    window.location.href = './index.html';
  });

  loadBookings();
  // Re-render so "Completed" buttons enable once a ride's end time passes.
  setInterval(() => (isAuthenticated() ? render() : redirectToLogin()), REFRESH_INTERVAL_MS);
}

init();
