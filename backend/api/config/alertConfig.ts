export interface AlertConfig {
    email: {
        host: string;
        port: number;
        secure: boolean;
        auth: {
            user: string;
            pass: string;
        };
    };
    notifications: {
        recipients: string[];
        webhookUrls?: string[];
        smsEnabled?: boolean;
        smsConfig?: {
            accountSid: string;
            authToken: string;
            fromNumber: string;
            toNumbers: string[];
        };
    };
    persistence: {
        retentionDays: number;
        cleanupInterval: number;
    };
}

export const alertConfig: AlertConfig = {
    email: {
        host: process.env.SMTP_HOST || 'smtp.gmail.com',
        port: parseInt(process.env.SMTP_PORT || '587', 10),
        secure: process.env.SMTP_SECURE === 'true',
        auth: {
            user: process.env.SMTP_USER || '',
            pass: process.env.SMTP_PASS || ''
        }
    },
    notifications: {
        recipients: (process.env.ALERT_RECIPIENTS || '').split(',').filter(Boolean),
        webhookUrls: (process.env.ALERT_WEBHOOK_URLS || '').split(',').filter(Boolean),
        smsEnabled: process.env.SMS_ENABLED === 'true',
        smsConfig: process.env.SMS_ENABLED === 'true' ? {
            accountSid: process.env.TWILIO_ACCOUNT_SID || '',
            authToken: process.env.TWILIO_AUTH_TOKEN || '',
            fromNumber: process.env.TWILIO_FROM_NUMBER || '',
            toNumbers: (process.env.SMS_RECIPIENTS || '').split(',').filter(Boolean)
        } : undefined
    },
    persistence: {
        retentionDays: parseInt(process.env.ALERT_RETENTION_DAYS || '30', 10),
        cleanupInterval: parseInt(process.env.ALERT_CLEANUP_INTERVAL || '86400000', 10) // 24 hours
    }
}; 