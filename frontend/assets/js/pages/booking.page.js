import * as api from '../services/api.js';
import { isAuthenticated } from '../services/auth.js';
import { $, escapeHtml } from '../core/dom.js';
import { addDays, formatDisplayDate } from '../core/date.js';
import { icons } from '../core/icons.js';
import { initTheme } from '../ui/theme.js';
import { closeModal, initModals, openModal } from '../ui/modal.js';
import { showToast } from '../ui/toast.js';

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const MOBILE_PATTERN = /^[6-9]\d{9}$/;
const SLOT_TAKEN_STATUS = 409;

const el = {
  form: $('#booking-form'),
  typeSelect: $('#type-select'),
  brandSelect: $('#brand-select'),
  modelSelect: $('#model-select'),
  variantSelect: $('#variant-select'),
  variantStatus: $('#variant-status'),
  dateStep: $('#date-step'),
  dateInput: $('#date-input'),
  slotStep: $('#slot-step'),
  slotButton: $('#slot-button'),
  slotSummary: $('#slot-summary'),
  previewStep: $('#preview-step'),
  preview: $('#preview'),
  contactStep: $('#contact-step'),
  emailInput: $('#email-input'),
  emailError: $('#email-error'),
  mobileInput: $('#mobile-input'),
  mobileError: $('#mobile-error'),
  formError: $('#form-error'),
  resetButton: $('#reset-button'),
  submitButton: $('#submit-button'),
  slotModal: $('#slot-modal'),
  slotGrid: $('#slot-grid'),
  slotDateLabel: $('#slot-date-label'),
  reachModal: $('#reach-modal'),
  pinModal: $('#pin-modal'),
  pinForm: $('#pin-form'),
  pinInput: $('#pin-input'),
  pinError: $('#pin-error'),
  pinSubmit: $('#pin-submit'),
  successModal: $('#success-modal'),
};

const emptyState = () => ({ type: null, brand: null, model: null, variant: null, date: '', slot: null });
const state = emptyState();

// Each level loads its options from the selection one level above it.
const cascade = [
  { key: 'type', select: el.typeSelect, placeholder: 'Select type', load: () => api.getVehicleTypes() },
  { key: 'brand', select: el.brandSelect, placeholder: 'Select brand', load: () => api.getBrands(state.type.id) },
  { key: 'model', select: el.modelSelect, placeholder: 'Select model', load: () => api.getModels(state.brand.id) },
  { key: 'variant', select: el.variantSelect, placeholder: 'Select variant', load: () => api.getVariants(state.model.id) },
];

/* ---------- Cascading dropdowns ---------- */

function resetLevel(level, label = level.placeholder) {
  level.items = [];
  level.select.replaceChildren(new Option(label, ''));
  level.select.disabled = true;
}

function variantLabel(variant) {
  return `${variant.name} — ${variant.available ? 'Currently Available' : 'Currently Unavailable'}`;
}

async function loadLevel(index) {
  const level = cascade[index];
  const parent = cascade[index - 1];
  const parentId = parent ? state[parent.key]?.id : null;
  resetLevel(level, 'Loading...');

  try {
    const items = await level.load();
    if (parent && state[parent.key]?.id !== parentId) return; // a newer selection superseded this request
    resetLevel(level);
    level.items = items;
    items.forEach((item) => {
      const isVariant = level.key === 'variant';
      const option = new Option(isVariant ? variantLabel(item) : item.name, String(item.id));
      option.disabled = isVariant && !item.available;
      level.select.add(option);
    });
    level.select.disabled = items.length === 0;
  } catch (error) {
    resetLevel(level);
    showToast(error.message, 'error');
  }
}

function handleLevelChange(index) {
  const level = cascade[index];
  state[level.key] = level.items.find((item) => String(item.id) === level.select.value) ?? null;

  cascade.slice(index + 1).forEach((child) => {
    state[child.key] = null;
    resetLevel(child);
  });
  state.date = '';
  state.slot = null;
  el.dateInput.value = '';

  if (state[level.key] && index < cascade.length - 1) loadLevel(index + 1);
  refresh();
}

/* ---------- Date & slots ---------- */

function handleDateChange() {
  const { value, min, max } = el.dateInput;
  state.slot = null;
  if (value && (value < min || value > max)) {
    state.date = '';
    el.dateInput.value = '';
    showToast('Please choose a date between today and the next 7 days.', 'error');
  } else {
    state.date = value;
  }
  refresh();
  if (state.date) openSlotPicker();
}

async function openSlotPicker() {
  el.slotDateLabel.textContent = formatDisplayDate(state.date);
  el.slotGrid.innerHTML = '<div class="loading-state"><span class="spinner" aria-hidden="true"></span> Loading slots...</div>';
  openModal(el.slotModal);

  try {
    const slots = await api.getSlots(state.variant.id, state.date);
    el.slotGrid.replaceChildren(...slots.map(createSlotButton));
    el.slotGrid.querySelector('.slot-button:not(:disabled)')?.focus();
  } catch (error) {
    el.slotGrid.innerHTML = `<p class="form-alert">${escapeHtml(error.message)}</p>`;
  }
}

function createSlotButton(slot) {
  const button = document.createElement('button');
  const status = slot.available ? 'Available' : slot.reason || 'Unavailable';
  button.type = 'button';
  button.className = `slot-button${slot.available ? '' : ' unavailable'}`;
  button.disabled = !slot.available;
  button.setAttribute('aria-label', `${slot.start} to ${slot.end}, ${status}`);
  button.innerHTML = `
    <span class="slot-status">${slot.available ? icons.check(14) : icons.cross(14)} ${escapeHtml(status)}</span>
    <span class="slot-time">${slot.start} - ${slot.end}</span>`;
  if (slot.available) {
    button.addEventListener('click', () => {
      state.slot = slot;
      closeModal(el.slotModal, { restoreFocus: false });
      refresh();
      el.emailInput.focus();
    });
  }
  return button;
}

/* ---------- Rendering ---------- */

function setLocked(step, locked) {
  step.classList.toggle('is-locked', locked);
}

function renderPreview() {
  const rows = [
    ['Type', state.type?.name],
    ['Brand', state.brand?.name],
    ['Model', state.model?.name],
    ['Variant', state.variant?.name],
    ['Date', state.date && formatDisplayDate(state.date)],
    ['Time slot', state.slot && `${state.slot.start} - ${state.slot.end}`],
  ];
  el.preview.innerHTML = rows
    .map(([label, value]) => `<div><dt>${label}</dt><dd>${escapeHtml(value || '—')}</dd></div>`)
    .join('');
}

function renderVariantStatus() {
  el.variantStatus.hidden = !state.variant;
  if (state.variant) {
    el.variantStatus.className = 'status-badge available';
    el.variantStatus.innerHTML = `${icons.check(12)} Currently Available`;
  }
}

function validateContact({ showErrors = false } = {}) {
  const email = el.emailInput.value.trim();
  const mobile = el.mobileInput.value.trim();
  const emailValid = EMAIL_PATTERN.test(email);
  const mobileValid = MOBILE_PATTERN.test(mobile);

  const showEmail = !emailValid && (email || showErrors);
  const showMobile = !mobileValid && (mobile || showErrors);
  el.emailError.textContent = showEmail ? 'Enter a valid email address.' : '';
  el.mobileError.textContent = showMobile ? 'Enter a 10-digit mobile number starting with 6-9.' : '';
  el.emailInput.setAttribute('aria-invalid', String(Boolean(showEmail)));
  el.mobileInput.setAttribute('aria-invalid', String(Boolean(showMobile)));
  return emailValid && mobileValid;
}

/** Derives every step's enabled/locked state from `state`. */
function refresh() {
  const hasVariant = Boolean(state.variant);
  const hasSlot = Boolean(state.slot);

  el.dateInput.disabled = !hasVariant;
  el.slotButton.disabled = !(hasVariant && state.date);
  el.emailInput.disabled = !hasSlot;
  el.mobileInput.disabled = !hasSlot;

  setLocked(el.dateStep, !hasVariant);
  setLocked(el.slotStep, !state.date);
  setLocked(el.previewStep, !hasSlot);
  setLocked(el.contactStep, !hasSlot);

  el.slotSummary.textContent = hasSlot ? `Selected: ${state.slot.start} - ${state.slot.end}` : 'No time selected';
  el.slotSummary.classList.toggle('is-selected', hasSlot);
  el.formError.hidden = true;

  renderVariantStatus();
  renderPreview();
  el.submitButton.disabled = !(hasSlot && validateContact());
}

/* ---------- Reset & submit ---------- */

function hasInput() {
  return Boolean(state.type || el.emailInput.value || el.mobileInput.value);
}

function resetForm() {
  Object.assign(state, emptyState());
  el.typeSelect.value = '';
  cascade.slice(1).forEach((level) => resetLevel(level));
  el.dateInput.value = '';
  el.emailInput.value = '';
  el.mobileInput.value = '';
  el.emailError.textContent = '';
  el.mobileError.textContent = '';
  refresh();
}

async function handleSubmit(event) {
  event.preventDefault();
  if (!state.slot || !validateContact({ showErrors: true })) return;

  const booking = { ...state };
  el.submitButton.disabled = true;
  el.submitButton.innerHTML = '<span class="spinner" aria-hidden="true"></span> Booking...';

  try {
    const { bookingId } = await api.createBooking({
      variantId: booking.variant.id,
      date: booking.date,
      slotStart: booking.slot.start,
      email: el.emailInput.value.trim(),
      mobile: el.mobileInput.value.trim(),
    });
    showSuccess(booking, bookingId);
    resetForm();
  } catch (error) {
    el.formError.textContent = error.message;
    el.formError.hidden = false;
    if (error.status === SLOT_TAKEN_STATUS) {
      state.slot = null;
      refresh();
      el.formError.textContent = error.message;
      el.formError.hidden = false;
      openSlotPicker();
    }
  } finally {
    el.submitButton.textContent = 'Book Test Ride';
    el.submitButton.disabled = !(state.slot && validateContact());
  }
}

function showSuccess(booking, bookingId) {
  $('#success-summary').innerHTML = [
    `${booking.type.name} · ${booking.brand.name} · ${booking.model.name}`,
    booking.variant.name,
    `${formatDisplayDate(booking.date)} · ${booking.slot.start} - ${booking.slot.end}`,
  ].map((line) => `<li>${escapeHtml(line)}</li>`).join('');
  $('#booking-reference').textContent = `Booking ID: ${bookingId}`;
  openModal(el.successModal);
}

/* ---------- Reach us & dealer PIN ---------- */

let dealerInfoLoaded = false;

async function openReachUs() {
  openModal(el.reachModal);
  if (dealerInfoLoaded) return;
  try {
    const { phone, email } = await api.getDealerInfo();
    $('#dealer-phone').innerHTML = `<a href="tel:${escapeHtml(phone.replace(/\s/g, ''))}">${escapeHtml(phone)}</a>`;
    $('#dealer-email').innerHTML = `<a href="mailto:${escapeHtml(email)}">${escapeHtml(email)}</a>`;
    dealerInfoLoaded = true;
  } catch {
    $('#dealer-phone').textContent = 'Unavailable';
    $('#dealer-email').textContent = 'Unavailable';
  }
}

function openPinPrompt() {
  if (isAuthenticated()) {
    window.location.href = './dealer.html';
    return;
  }
  el.pinInput.value = '';
  el.pinError.textContent = '';
  openModal(el.pinModal, el.pinInput);
}

async function handlePinSubmit(event) {
  event.preventDefault();
  const pin = el.pinInput.value.trim();
  if (!/^\d{4,8}$/.test(pin)) {
    el.pinError.textContent = 'PIN must be 4-8 digits.';
    return;
  }

  el.pinSubmit.disabled = true;
  el.pinSubmit.textContent = 'Verifying...';
  try {
    await api.verifyDealerPin(pin);
    window.location.href = './dealer.html';
  } catch (error) {
    el.pinError.textContent = error.message;
    el.pinInput.value = '';
    el.pinInput.focus();
  } finally {
    el.pinSubmit.disabled = false;
    el.pinSubmit.textContent = 'Unlock Dashboard';
  }
}

/* ---------- Init ---------- */

function init() {
  initTheme();
  initModals();

  el.dateInput.min = addDays(0);
  el.dateInput.max = addDays(7);

  cascade.forEach((level, index) => level.select.addEventListener('change', () => handleLevelChange(index)));
  el.dateInput.addEventListener('change', handleDateChange);
  el.slotButton.addEventListener('click', openSlotPicker);
  el.emailInput.addEventListener('input', refresh);
  el.mobileInput.addEventListener('input', () => {
    el.mobileInput.value = el.mobileInput.value.replace(/\D/g, '');
    refresh();
  });
  el.resetButton.addEventListener('click', () => {
    if (!hasInput() || window.confirm('Clear all booking details?')) resetForm();
  });
  el.form.addEventListener('submit', handleSubmit);

  $('#reach-us-button').addEventListener('click', openReachUs);
  $('#reschedule-button').addEventListener('click', () => showToast('Online rescheduling is coming soon.'));
  $('#dealer-button').addEventListener('click', openPinPrompt);
  el.pinForm.addEventListener('submit', handlePinSubmit);

  resetLevel(cascade[0], 'Loading...');
  loadLevel(0);
  refresh();

  // dealer.html redirects here with ?dealer when there is no valid session.
  if (new URLSearchParams(window.location.search).has('dealer')) {
    window.history.replaceState(null, '', window.location.pathname);
    openPinPrompt();
  }
}

init();
