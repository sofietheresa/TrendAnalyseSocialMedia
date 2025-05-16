/**
 * Utility functions for consistent date and time formatting
 * using German locale (de-DE)
 */

/**
 * Format a date as a localized string (date and time)
 * @param {string|Date} dateString - ISO date string or Date object
 * @param {Object} options - Additional formatting options
 * @returns {string} Formatted date and time in German format
 */
export const formatDateTime = (dateString, options = {}) => {
  if (!dateString) return 'N/A';
  const date = dateString instanceof Date ? dateString : new Date(dateString);
  
  return date.toLocaleString('de-DE', options);
};

/**
 * Format a date as a localized date only string
 * @param {string|Date} dateString - ISO date string or Date object
 * @param {Object} options - Additional formatting options
 * @returns {string} Formatted date in German format
 */
export const formatDate = (dateString, options = {}) => {
  if (!dateString) return 'N/A';
  const date = dateString instanceof Date ? dateString : new Date(dateString);
  
  return date.toLocaleDateString('de-DE', options);
};

/**
 * Format a date as a short date (day and month only)
 * @param {string|Date} dateString - ISO date string or Date object
 * @returns {string} Short date in German format (e.g., "15. Mai")
 */
export const formatShortDate = (dateString) => {
  if (!dateString) return 'N/A';
  const date = dateString instanceof Date ? dateString : new Date(dateString);
  
  return date.toLocaleDateString('de-DE', { day: 'numeric', month: 'short' });
};

/**
 * Format a date as a weekday
 * @param {string|Date} dateString - ISO date string or Date object
 * @returns {string} Weekday in German format (e.g., "Mo", "Di")
 */
export const formatWeekday = (dateString) => {
  if (!dateString) return 'N/A';
  const date = dateString instanceof Date ? dateString : new Date(dateString);
  
  return date.toLocaleDateString('de-DE', { weekday: 'short' });
};

/**
 * Format a number with German thousands separator
 * @param {number} value - Number to format
 * @returns {string} Formatted number with German thousands separator
 */
export const formatNumber = (value) => {
  if (value === undefined || value === null) return '0';
  return value.toLocaleString('de-DE');
};

export default {
  formatDateTime,
  formatDate,
  formatShortDate,
  formatWeekday,
  formatNumber
}; 