/**
 * Development logging utilities.
 * Automatically disables debug logging in production builds.
 */

// Development logging is enabled only in dev mode
const DEV_LOGGING = import.meta.env.DEV;

/**
 * Log messages only in development mode.
 * In production builds, this is a no-op.
 */
export const devLog = (...args: unknown[]): void => {
  if (DEV_LOGGING) {
    console.log(...args);
  }
};

/**
 * Log errors in all environments.
 * Errors should always be logged for debugging.
 */
export const devError = (...args: unknown[]): void => {
  console.error(...args);
};
