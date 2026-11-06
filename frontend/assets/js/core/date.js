/** Local-time YYYY-MM-DD (toISOString would shift the day in UTC+ zones). */
export function toISODate(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

export function addDays(days, from = new Date()) {
  const date = new Date(from);
  date.setDate(date.getDate() + days);
  return toISODate(date);
}

export function formatDisplayDate(isoDate) {
  return new Intl.DateTimeFormat('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
    .format(new Date(`${isoDate}T00:00:00`));
}

export function formatLongDate(date = new Date()) {
  return new Intl.DateTimeFormat('en-IN', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' }).format(date);
}

export function toDateTime(isoDate, time) {
  return new Date(`${isoDate}T${time}:00`);
}
