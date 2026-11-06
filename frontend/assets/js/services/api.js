/**
 * The only module that talks to the backend. UI code calls these functions and never uses fetch directly.
 */
import { request } from '../core/http.js';
import { getToken, saveSession } from './auth.js';

const enc = encodeURIComponent;

export const getVehicleTypes = () => request('/vehicle-types');
export const getBrands = (typeId) => request(`/vehicle-types/${enc(typeId)}/brands`);
export const getModels = (brandId) => request(`/brands/${enc(brandId)}/models`);
export const getVariants = (modelId) => request(`/models/${enc(modelId)}/variants`);
export const getSlots = (variantId, date) => request(`/variants/${enc(variantId)}/slots?date=${enc(date)}`);

/** @returns {Promise<{bookingId: string}>} Rejects with ApiError status 409 if the slot was taken. */
export const createBooking = ({ variantId, date, slotStart, email, mobile }) =>
  request('/bookings', { method: 'POST', body: { variantId, date, slotStart, email, mobile } });

export const getDealerInfo = () => request('/dealer-info');

export async function verifyDealerPin(pin) {
  const { token, expiresIn } = await request('/dealer/verify-pin', { method: 'POST', body: { pin } });
  saveSession(token, expiresIn);
}

export const getBookings = () => request('/bookings', { token: getToken() });
export const markCompleted = (bookingId) =>
  request(`/bookings/${enc(bookingId)}/complete`, { method: 'PATCH', token: getToken() });
