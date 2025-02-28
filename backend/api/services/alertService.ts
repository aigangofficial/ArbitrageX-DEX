import { Logger } from 'winston';
import { AlertModel, AlertData, IAlert, AlertLeanDoc } from '../models/alert';
import * as nodemailer from 'nodemailer';
import { config } from '../config';
import { EventEmitter } from 'events';
import { alertConfig } from '../config/alertConfig';
import { Gauge, Counter, register } from 'prom-client';

interface EmailConfig {
    host: string;
    port: number;
    secure: boolean;
    auth: {
        user: string;
        pass: string;
    };
}

interface CleanupOptions {
  retentionDays?: number;
  severity?: 'LOW' | 'MEDIUM' | 'HIGH';
  metric?: string;
  startTime?: number;
  endTime?: number;
}

interface CleanupMetrics {
  totalAlertsRetained: number;
  lastCleanupDuration: number;
  totalAlertsDeleted: {
    actual: number;
    simulated: number;
    failed: number;
  };
  lastCleanupTimestamp?: number;
}

interface MetricValue {
  value: number;
  labels: {
    status: string;
  };
}

interface PrometheusMetric {
  name: string;
  values: MetricValue[];
}

// Prometheus metrics
const alertCleanupGauge = new Gauge({
  name: 'alert_cleanup_duration_seconds',
  help: 'Duration of alert cleanup operation in seconds'
});

const alertsDeletedCounter = new Counter({
  name: 'alerts_deleted_total',
  help: 'Total number of alerts deleted by cleanup',
  labelNames: ['status'] as const
});

const alertsRetainedGauge = new Gauge({
  name: 'alerts_retained_total',
  help: 'Total number of alerts retained in the system'
});

export class AlertService extends EventEmitter {
    private emailTransporter: nodemailer.Transporter;
    private cleanupInterval: NodeJS.Timeout = setTimeout(() => {}, 0);
    private isDryRun: boolean = false;

    constructor(
        private readonly logger: Logger,
        private readonly emailConfig: EmailConfig
    ) {
        super();
        this.emailTransporter = nodemailer.createTransport(emailConfig);
        this.initializeCleanupSchedule();
    }

    setDryRun(enabled: boolean): void {
        this.isDryRun = enabled;
        this.logger.info(`Dry run mode ${enabled ? 'enabled' : 'disabled'}`);
    }

    private initializeCleanupSchedule(): void {
        this.cleanupInterval = setInterval(() => {
            this.scheduleCleanup();
        }, alertConfig.persistence.cleanupInterval);
    }

    async scheduleCleanup(options?: CleanupOptions): Promise<void> {
        const startTime = Date.now();
        try {
            const retentionPeriod = options?.retentionDays || alertConfig.persistence.retentionDays;
            const cutoffDate = Date.now() - (retentionPeriod * 86400000); // Convert days to milliseconds
            
            // Build query for alerts to delete
            const query: any = {
                status: 'resolved',
                timestamp: { $lt: cutoffDate }
            };

            if (options?.severity) {
                query.severity = options.severity;
            }

            if (options?.metric) {
                query.metric = options.metric;
            }

            if (options?.startTime) {
                query.timestamp = { ...query.timestamp, $gte: options.startTime };
            }

            if (options?.endTime) {
                query.timestamp = { ...query.timestamp, $lte: options.endTime };
            }

            // Get count of alerts that would be deleted
            const alertsToDelete = await AlertModel.find(query);

            // Track metrics before deletion
            const totalAlerts = await AlertModel.countDocuments();
            alertsRetainedGauge.set(totalAlerts);

            if (this.isDryRun) {
                this.logger.info('Dry run: Would delete alerts', {
                    wouldDeleteCount: alertsToDelete.length,
                    retentionDays: retentionPeriod,
                    cutoffDate: new Date(cutoffDate).toISOString(),
                    query
                });
                alertsDeletedCounter.inc({ status: 'simulated' }, alertsToDelete.length);
            } else {
                const result = await AlertModel.deleteMany(query);

                alertsDeletedCounter.inc({ status: 'actual' }, result.deletedCount);
                
                this.logger.info('Alert cleanup completed', {
                    deletedCount: result.deletedCount,
                    retentionDays: retentionPeriod,
                    cutoffDate: new Date(cutoffDate).toISOString(),
                    query
                });

                this.emit('cleanup', {
                    deletedCount: result.deletedCount,
                    retentionDays: retentionPeriod,
                    timestamp: Date.now(),
                    query
                });
            }

            // Track cleanup duration
            const duration = (Date.now() - startTime) / 1000;
            alertCleanupGauge.set(duration);

        } catch (error) {
            this.logger.error('Alert cleanup failed:', error);
            this.emit('cleanupError', error);
            alertsDeletedCounter.inc({ status: 'failed' }, 0);
        }
    }

    async getCleanupMetrics(): Promise<CleanupMetrics> {
        const metrics = await register.getMetricsAsJSON();
        
        const cleanupDuration = metrics.find(m => m.name === 'alert_cleanup_duration_seconds')?.values[0]?.value || 0;
        const alertsRetained = metrics.find(m => m.name === 'alerts_retained_total')?.values[0]?.value || 0;
        
        const deletedMetrics = metrics.find(m => m.name === 'alerts_deleted_total')?.values || [];
        const totalAlertsDeleted = {
            actual: (deletedMetrics.find(m => m.labels?.status === 'actual')?.value as number) || 0,
            simulated: (deletedMetrics.find(m => m.labels?.status === 'simulated')?.value as number) || 0,
            failed: (deletedMetrics.find(m => m.labels?.status === 'failed')?.value as number) || 0
        };

        return {
            totalAlertsRetained: alertsRetained,
            lastCleanupDuration: cleanupDuration,
            totalAlertsDeleted,
            lastCleanupTimestamp: Date.now()
        };
    }

    async persistAlert(alert: Omit<AlertData, 'status' | 'timestamp'>): Promise<void> {
        try {
            const newAlert = new AlertModel({
                ...alert,
                status: 'pending',
                timestamp: new Date()
            });
            await newAlert.save();
            this.emit('alert:created', newAlert);
            await this.sendNotifications(newAlert);
        } catch (error) {
            this.logger.error('Failed to persist alert:', error);
            throw error;
        }
    }

    async getActiveAlerts(): Promise<AlertLeanDoc[]> {
        const alerts = await AlertModel.find({ status: 'pending' })
            .sort({ timestamp: -1 })
            .lean()
            .exec();
        return alerts as AlertLeanDoc[];
    }

    async markAlertResolved(alertId: string): Promise<void> {
        const alert = await AlertModel.findByIdAndUpdate(
            alertId,
            { status: 'resolved' },
            { new: true }
        );
        if (!alert) {
            throw new Error(`Alert with ID ${alertId} not found`);
        }
        this.emit('alert:resolved', alert);
    }

    async getAlertHistory(
        options: {
            startTime?: number;
            endTime?: number;
            severity?: 'LOW' | 'MEDIUM' | 'HIGH';
            metric?: string;
            limit?: number;
        } = {}
    ): Promise<IAlert[]> {
        const query: any = {};
        
        if (options.startTime || options.endTime) {
            query.timestamp = {};
            if (options.startTime) query.timestamp.$gte = options.startTime;
            if (options.endTime) query.timestamp.$lte = options.endTime;
        }
        
        if (options.severity) query.severity = options.severity;
        if (options.metric) query.metric = options.metric;

        return AlertModel.find(query)
            .sort({ timestamp: -1 })
            .limit(options.limit || 100)
            .lean();
    }

    private async sendNotifications(alert: IAlert): Promise<void> {
        try {
            // Send email notification
            await this.emailTransporter.sendMail({
                from: this.emailConfig.auth.user,
                to: alertConfig.notifications.recipients,
                subject: `[HIGH SEVERITY] ArbitrageX Alert: ${alert.metric}`,
                html: `
                    <h2>High Severity Alert</h2>
                    <p><strong>Metric:</strong> ${alert.metric}</p>
                    <p><strong>Message:</strong> ${alert.message}</p>
                    <p><strong>Value:</strong> ${alert.value}</p>
                    <p><strong>Threshold:</strong> ${alert.threshold}</p>
                    <p><strong>Remediation:</strong> ${alert.remediation}</p>
                    <p><strong>Timestamp:</strong> ${new Date(alert.timestamp).toISOString()}</p>
                `
            });

            // Emit webhook event for external integrations
            this.emit('notification', {
                type: 'HIGH_SEVERITY_ALERT',
                alert
            });

            this.logger.info('Alert notifications sent successfully:', {
                alertId: alert._id,
                metric: alert.metric
            });
        } catch (error) {
            this.logger.error('Failed to send alert notifications:', error);
            throw error;
        }
    }

    async shutdown(): Promise<void> {
        clearInterval(this.cleanupInterval);
        if (this.emailTransporter) {
            this.emailTransporter.close();
        }
        this.logger.info('Alert service shutdown completed');
    }
} 