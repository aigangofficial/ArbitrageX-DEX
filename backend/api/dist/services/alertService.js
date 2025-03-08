"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.AlertService = void 0;
const AlertModel_1 = require("../models/AlertModel");
const nodemailer = __importStar(require("nodemailer"));
const events_1 = require("events");
const alertConfig_1 = require("../config/alertConfig");
const prom_client_1 = require("prom-client");
// Prometheus metrics
const alertCleanupGauge = new prom_client_1.Gauge({
    name: 'alert_cleanup_duration_seconds',
    help: 'Duration of alert cleanup operation in seconds'
});
const alertsDeletedCounter = new prom_client_1.Counter({
    name: 'alerts_deleted_total',
    help: 'Total number of alerts deleted by cleanup',
    labelNames: ['status']
});
const alertsRetainedGauge = new prom_client_1.Gauge({
    name: 'alerts_retained_total',
    help: 'Total number of alerts retained in the system'
});
class AlertService extends events_1.EventEmitter {
    constructor(logger, emailConfig) {
        super();
        this.logger = logger;
        this.emailConfig = emailConfig;
        this.cleanupInterval = setTimeout(() => { }, 0);
        this.isDryRun = false;
        this.emailTransporter = nodemailer.createTransport(emailConfig);
        clearTimeout(this.cleanupInterval);
        this.initializeCleanupSchedule();
    }
    setDryRun(enabled) {
        this.isDryRun = enabled;
        this.logger.info(`Dry run mode ${enabled ? 'enabled' : 'disabled'}`);
    }
    initializeCleanupSchedule() {
        this.cleanupInterval = setInterval(() => {
            this.scheduleCleanup();
        }, alertConfig_1.alertConfig.persistence.cleanupInterval);
    }
    async scheduleCleanup(options) {
        const startTime = Date.now();
        try {
            const retentionPeriod = options?.retentionDays || alertConfig_1.alertConfig.persistence.retentionDays;
            const cutoffDate = Date.now() - (retentionPeriod * 86400000); // Convert days to milliseconds
            // Build query for alerts to delete
            const query = {
                resolved: true,
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
            const alertsToDelete = await AlertModel_1.AlertModel.find(query);
            // Track metrics before deletion
            const totalAlerts = await AlertModel_1.AlertModel.countDocuments();
            alertsRetainedGauge.set(totalAlerts);
            if (this.isDryRun) {
                this.logger.info('Dry run: Would delete alerts', {
                    wouldDeleteCount: alertsToDelete.length,
                    retentionDays: retentionPeriod,
                    cutoffDate: new Date(cutoffDate).toISOString(),
                    query
                });
                alertsDeletedCounter.inc({ status: 'simulated' }, alertsToDelete.length);
            }
            else {
                const result = await AlertModel_1.AlertModel.deleteMany(query);
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
        }
        catch (error) {
            this.logger.error('Alert cleanup failed:', error);
            this.emit('cleanupError', error);
            alertsDeletedCounter.inc({ status: 'failed' }, 0);
        }
    }
    async getCleanupMetrics() {
        const metrics = await prom_client_1.register.getMetricsAsJSON();
        const cleanupDuration = metrics.find(m => m.name === 'alert_cleanup_duration_seconds')?.values[0]?.value || 0;
        const alertsRetained = metrics.find(m => m.name === 'alerts_retained_total')?.values[0]?.value || 0;
        const deletedMetrics = metrics.find(m => m.name === 'alerts_deleted_total')?.values || [];
        const totalAlertsDeleted = {
            actual: deletedMetrics.find(m => m.labels?.status === 'actual')?.value || 0,
            simulated: deletedMetrics.find(m => m.labels?.status === 'simulated')?.value || 0,
            failed: deletedMetrics.find(m => m.labels?.status === 'failed')?.value || 0
        };
        return {
            totalAlertsRetained: alertsRetained,
            lastCleanupDuration: cleanupDuration,
            totalAlertsDeleted,
            lastCleanupTimestamp: Date.now()
        };
    }
    async persistAlert(alert) {
        try {
            const newAlert = await AlertModel_1.AlertModel.create({
                ...alert,
                timestamp: Date.now(),
                resolved: false,
                remediationApplied: false
            });
            this.emit('newAlert', newAlert);
            // Send notifications for HIGH severity alerts
            if (alert.severity === 'HIGH') {
                await this.sendNotifications(newAlert);
            }
            this.logger.info('Alert persisted successfully:', {
                alertId: newAlert._id,
                metric: alert.metric,
                severity: alert.severity
            });
        }
        catch (error) {
            this.logger.error('Failed to persist alert:', error);
            throw error;
        }
    }
    async markAlertResolved(alertId) {
        try {
            const alert = await AlertModel_1.AlertModel.findByIdAndUpdate(alertId, {
                resolved: true,
                resolvedAt: Date.now()
            }, { new: true });
            if (alert) {
                this.emit('alertResolved', alert);
                this.logger.info('Alert marked as resolved:', { alertId });
            }
        }
        catch (error) {
            this.logger.error('Failed to mark alert as resolved:', error);
            throw error;
        }
    }
    async markRemediationApplied(alertId) {
        try {
            const alert = await AlertModel_1.AlertModel.findByIdAndUpdate(alertId, {
                remediationApplied: true,
                remediationTimestamp: Date.now()
            }, { new: true });
            if (alert) {
                this.emit('remediationApplied', alert);
                this.logger.info('Alert remediation marked as applied:', { alertId });
            }
        }
        catch (error) {
            this.logger.error('Failed to mark remediation as applied:', error);
            throw error;
        }
    }
    async getActiveAlerts() {
        return AlertModel_1.AlertModel.find({ resolved: false })
            .sort({ timestamp: -1 })
            .lean();
    }
    async getAlertHistory(options = {}) {
        const query = {};
        if (options.startTime || options.endTime) {
            query.timestamp = {};
            if (options.startTime)
                query.timestamp.$gte = options.startTime;
            if (options.endTime)
                query.timestamp.$lte = options.endTime;
        }
        if (options.severity)
            query.severity = options.severity;
        if (options.metric)
            query.metric = options.metric;
        return AlertModel_1.AlertModel.find(query)
            .sort({ timestamp: -1 })
            .limit(options.limit || 100)
            .lean();
    }
    async sendNotifications(alert) {
        try {
            // Send email notification
            await this.emailTransporter.sendMail({
                from: this.emailConfig.auth.user,
                to: alertConfig_1.alertConfig.notifications.recipients,
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
        }
        catch (error) {
            this.logger.error('Failed to send alert notifications:', error);
            throw error;
        }
    }
    async shutdown() {
        clearInterval(this.cleanupInterval);
        await this.emailTransporter.close();
        this.logger.info('Alert service shutdown completed');
    }
}
exports.AlertService = AlertService;
//# sourceMappingURL=alertService.js.map