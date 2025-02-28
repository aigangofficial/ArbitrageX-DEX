import * as Sentry from '@sentry/node';
import { ProfilingIntegration } from '@sentry/profiling-node';

export function initializeSentry() {
  if (!process.env.SENTRY_DSN) {
    console.warn('SENTRY_DSN not found in environment variables. Error tracking disabled.');
    return;
  }

  Sentry.init({
    dsn: process.env.SENTRY_DSN,
    integrations: [
      new ProfilingIntegration(),
    ],
    tracesSampleRate: 1.0,
    profilesSampleRate: 1.0,
    environment: process.env.NODE_ENV || 'development',
    beforeSend(event) {
      // Remove sensitive data
      if (event.request?.data) {
        delete event.request.data.privateKey;
        delete event.request.data.mnemonic;
      }
      return event;
    },
  });

  // Set up error boundaries
  process.on('unhandledRejection', (error: Error) => {
    Sentry.captureException(error);
  });

  process.on('uncaughtException', (error: Error) => {
    Sentry.captureException(error);
  });
}

export function trackError(error: Error, context?: Record<string, any>) {
  Sentry.withScope((scope) => {
    if (context) {
      scope.setExtras(context);
    }
    Sentry.captureException(error);
  });
}

export function trackMetric(name: string, value: number, tags?: Record<string, string>) {
  Sentry.addBreadcrumb({
    category: 'metrics',
    message: `${name}: ${value}`,
    data: tags,
    level: 'info',
  });
}

export function setUser(userId: string) {
  Sentry.setUser({ id: userId });
}

export function clearUser() {
  Sentry.setUser(null);
}
