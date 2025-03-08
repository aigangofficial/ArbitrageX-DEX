"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const alertService_1 = require("../alertService");
const AlertModel_1 = require("../../models/AlertModel");
const logger_1 = require("../../utils/logger");
const prom_client_1 = require("prom-client");
const supertest_1 = __importDefault(require("supertest"));
const express_1 = __importDefault(require("express"));
// Mock express app
const app = (0, express_1.default)();
jest.mock('../../models/AlertModel');
jest.mock('nodemailer', () => ({
    createTransport: jest.fn().mockReturnValue({
        sendMail: jest.fn().mockResolvedValue(true),
        close: jest.fn().mockResolvedValue(true)
    })
}));
// Mock rate limiters
jest.mock('../../middleware/rateLimit', () => ({
    alertCleanupLimiter: jest.fn((req, res, next) => next()),
    alertMetricsLimiter: jest.fn((req, res, next) => next())
}));
describe('AlertService', () => {
    let alertService;
    beforeEach(() => {
        jest.clearAllMocks();
        prom_client_1.register.clear();
        alertService = new alertService_1.AlertService(logger_1.logger, {
            host: 'smtp.test.com',
            port: 587,
            secure: false,
            auth: {
                user: 'test@test.com',
                pass: 'password'
            }
        });
    });
    describe('Cleanup with Dry Run', () => {
        it('should simulate cleanup in dry run mode', async () => {
            const mockAlerts = [
                { _id: '1', timestamp: Date.now() - 90 * 86400000, resolved: true },
                { _id: '2', timestamp: Date.now() - 91 * 86400000, resolved: true }
            ];
            AlertModel_1.AlertModel.find.mockResolvedValue(mockAlerts);
            AlertModel_1.AlertModel.countDocuments.mockResolvedValue(5);
            alertService.setDryRun(true);
            // Trigger cleanup manually for testing
            await alertService.scheduleCleanup();
            // Verify no actual deletions occurred
            expect(AlertModel_1.AlertModel.deleteMany).not.toHaveBeenCalled();
            // Verify logging
            expect(logger_1.logger.info).toHaveBeenCalledWith('Dry run: Would delete alerts', expect.objectContaining({
                wouldDeleteCount: 2
            }));
            // Verify metrics
            const metrics = await prom_client_1.register.getMetricsAsJSON();
            const deletedMetric = metrics.find(m => m.name === 'alerts_deleted_total');
            expect(deletedMetric?.values[0].value).toBe(2);
            expect(deletedMetric?.values[0].labels.status).toBe('simulated');
        });
        it('should perform actual cleanup when dry run is disabled', async () => {
            const deleteResult = { deletedCount: 3 };
            AlertModel_1.AlertModel.deleteMany.mockResolvedValue(deleteResult);
            AlertModel_1.AlertModel.countDocuments.mockResolvedValue(10);
            alertService.setDryRun(false);
            // Trigger cleanup manually for testing
            await alertService.scheduleCleanup();
            // Verify actual deletion occurred
            expect(AlertModel_1.AlertModel.deleteMany).toHaveBeenCalled();
            // Verify metrics
            const metrics = await prom_client_1.register.getMetricsAsJSON();
            const deletedMetric = metrics.find(m => m.name === 'alerts_deleted_total');
            expect(deletedMetric?.values[0].value).toBe(3);
            expect(deletedMetric?.values[0].labels.status).toBe('actual');
        });
        it('should track cleanup duration', async () => {
            AlertModel_1.AlertModel.deleteMany.mockResolvedValue({ deletedCount: 1 });
            AlertModel_1.AlertModel.countDocuments.mockResolvedValue(5);
            await alertService.scheduleCleanup();
            const metrics = await prom_client_1.register.getMetricsAsJSON();
            const durationMetric = metrics.find(m => m.name === 'alert_cleanup_duration_seconds');
            expect(durationMetric).toBeDefined();
            expect(typeof durationMetric?.values[0].value).toBe('number');
        });
        it('should handle errors and track failed cleanups', async () => {
            const error = new Error('Database error');
            AlertModel_1.AlertModel.find.mockRejectedValue(error);
            await alertService.scheduleCleanup();
            // Verify error logging
            expect(logger_1.logger.error).toHaveBeenCalledWith('Alert cleanup failed:', error);
            // Verify metrics for failed cleanup
            const metrics = await prom_client_1.register.getMetricsAsJSON();
            const deletedMetric = metrics.find(m => m.name === 'alerts_deleted_total');
            expect(deletedMetric?.values[0].value).toBe(0);
            expect(deletedMetric?.values[0].labels.status).toBe('failed');
        });
    });
    describe('Rate Limiting', () => {
        it('should respect rate limits for cleanup endpoint', async () => {
            // Mock rate limiter behavior
            const mockCleanupLimiter = jest.fn().mockImplementation((req, res, next) => {
                if ((mockCleanupLimiter.mock.calls.length) > 5) {
                    return res.status(429).json({ error: 'Too many requests' });
                }
                return next();
            });
            // Apply mock middleware
            app.post('/api/alerts/cleanup', mockCleanupLimiter, (req, res) => {
                res.json({ success: true });
            });
            // Make multiple requests
            const requests = Array(6).fill(0).map(() => (0, supertest_1.default)(app)
                .post('/api/alerts/cleanup')
                .send({ dryRun: true }));
            const responses = await Promise.all(requests);
            // Verify rate limiting
            expect(responses[5].status).toBe(429);
            expect(responses[5].body).toHaveProperty('error', 'Too many requests');
            expect(mockCleanupLimiter).toHaveBeenCalledTimes(6);
        });
        it('should respect rate limits for metrics endpoint', async () => {
            // Mock rate limiter behavior
            const mockMetricsLimiter = jest.fn().mockImplementation((req, res, next) => {
                if ((mockMetricsLimiter.mock.calls.length) > 30) {
                    return res.status(429).json({ error: 'Too many requests' });
                }
                return next();
            });
            // Apply mock middleware
            app.get('/api/alerts/metrics', mockMetricsLimiter, (req, res) => {
                res.json({ success: true });
            });
            // Make multiple requests
            const requests = Array(31).fill(0).map(() => (0, supertest_1.default)(app)
                .get('/api/alerts/metrics'));
            const responses = await Promise.all(requests);
            // Verify rate limiting
            expect(responses[30].status).toBe(429);
            expect(responses[30].body).toHaveProperty('error', 'Too many requests');
            expect(mockMetricsLimiter).toHaveBeenCalledTimes(31);
        });
        it('should allow requests within rate limits', async () => {
            // Mock successful responses
            app.post('/api/alerts/cleanup', (req, res) => {
                res.json({ success: true });
            });
            app.get('/api/alerts/metrics', (req, res) => {
                res.json({ success: true });
            });
            // Make a single request to cleanup endpoint
            const cleanupResponse = await (0, supertest_1.default)(app)
                .post('/api/alerts/cleanup')
                .send({ dryRun: true });
            expect(cleanupResponse.status).toBe(200);
            expect(cleanupResponse.body).toHaveProperty('success', true);
            // Make a single request to metrics endpoint
            const metricsResponse = await (0, supertest_1.default)(app)
                .get('/api/alerts/metrics');
            expect(metricsResponse.status).toBe(200);
            expect(metricsResponse.body).toHaveProperty('success', true);
        });
        it('should handle rate limit reset after window', async () => {
            let requestCount = 0;
            let lastRequestTime = Date.now();
            // Mock rate limiter with time window
            const mockTimeWindowLimiter = jest.fn().mockImplementation((req, res, next) => {
                const now = Date.now();
                if (now - lastRequestTime >= 15 * 60 * 1000) {
                    requestCount = 0;
                }
                if (requestCount >= 5) {
                    return res.status(429).json({ error: 'Too many requests' });
                }
                requestCount++;
                lastRequestTime = now;
                return next();
            });
            // Apply mock middleware
            app.post('/api/alerts/cleanup', mockTimeWindowLimiter, (req, res) => {
                res.json({ success: true });
            });
            // Make requests up to limit
            for (let i = 0; i < 5; i++) {
                const response = await (0, supertest_1.default)(app)
                    .post('/api/alerts/cleanup')
                    .send({ dryRun: true });
                expect(response.status).toBe(200);
            }
            // Next request should be rate limited
            const limitedResponse = await (0, supertest_1.default)(app)
                .post('/api/alerts/cleanup')
                .send({ dryRun: true });
            expect(limitedResponse.status).toBe(429);
            // Advance time by 15 minutes
            jest.spyOn(Date, 'now').mockImplementation(() => Date.now() + 15 * 60 * 1000);
            // Request should now be allowed
            const resetResponse = await (0, supertest_1.default)(app)
                .post('/api/alerts/cleanup')
                .send({ dryRun: true });
            expect(resetResponse.status).toBe(200);
        });
        it('should skip rate limit for whitelisted IPs', async () => {
            const mockCleanupLimiter = jest.fn().mockImplementation((req, res, next) => {
                // Simulate whitelisted IP
                req.ip = '127.0.0.1';
                return next();
            });
            app.post('/api/alerts/cleanup', mockCleanupLimiter, (req, res) => {
                res.json({ success: true });
            });
            // Make more requests than the limit
            const requests = Array(10).fill(0).map(() => (0, supertest_1.default)(app)
                .post('/api/alerts/cleanup')
                .send({ dryRun: true }));
            const responses = await Promise.all(requests);
            // All requests should succeed for whitelisted IP
            responses.forEach(response => {
                expect(response.status).toBe(200);
                expect(response.body).toHaveProperty('success', true);
            });
        });
        it('should track rate limit metrics', async () => {
            const mockCleanupLimiter = jest.fn().mockImplementation((req, res, next) => {
                req.ip = '192.168.1.1';
                if ((mockCleanupLimiter.mock.calls.length) > 5) {
                    return res.status(429).json({
                        error: 'Too many requests',
                        details: {
                            retryAfter: 900,
                            resetTime: new Date(Date.now() + 900000).toISOString(),
                            limit: 5,
                            windowMs: 900000,
                            endpoint: '/api/alerts/cleanup'
                        }
                    });
                }
                return next();
            });
            app.post('/api/alerts/cleanup', mockCleanupLimiter, (req, res) => {
                res.json({ success: true });
            });
            // Make requests until rate limited
            const requests = Array(6).fill(0).map(() => (0, supertest_1.default)(app)
                .post('/api/alerts/cleanup')
                .send({ dryRun: true }));
            const responses = await Promise.all(requests);
            // Verify rate limit response format
            const limitedResponse = responses[5];
            expect(limitedResponse.status).toBe(429);
            expect(limitedResponse.body).toMatchObject({
                error: 'Too many requests',
                details: expect.objectContaining({
                    retryAfter: expect.any(Number),
                    resetTime: expect.any(String),
                    limit: expect.any(Number),
                    windowMs: expect.any(Number),
                    endpoint: '/api/alerts/cleanup'
                })
            });
            // Verify metrics were tracked
            const metrics = await prom_client_1.register.getMetricsAsJSON();
            const rateLimitMetric = metrics.find(m => m.name === 'rate_limit_hits_total');
            expect(rateLimitMetric).toBeDefined();
            expect(rateLimitMetric?.values[0].value).toBe(1);
            expect(rateLimitMetric?.values[0].labels).toEqual({
                endpoint: '/api/alerts/cleanup',
                ip: '192.168.1.1'
            });
        });
        it('should use Redis store when available', async () => {
            const mockRedis = {
                incr: jest.fn().mockResolvedValue(1),
                decr: jest.fn().mockResolvedValue(0),
                del: jest.fn().mockResolvedValue(1)
            };
            const mockCleanupLimiter = jest.fn().mockImplementation((req, res, next) => {
                mockRedis.incr(`rl:${req.ip}:cleanup`);
                if (mockRedis.incr.mock.calls.length > 5) {
                    return res.status(429).json({
                        error: 'Too many requests',
                        details: {
                            retryAfter: 900,
                            resetTime: new Date(Date.now() + 900000).toISOString()
                        }
                    });
                }
                return next();
            });
            app.post('/api/alerts/cleanup', mockCleanupLimiter, (req, res) => {
                res.json({ success: true });
            });
            // Make multiple requests
            const requests = Array(6).fill(0).map(() => (0, supertest_1.default)(app)
                .post('/api/alerts/cleanup')
                .send({ dryRun: true }));
            const responses = await Promise.all(requests);
            expect(mockRedis.incr).toHaveBeenCalledTimes(6);
            expect(responses[5].status).toBe(429);
        });
        it('should handle burst requests with token bucket', async () => {
            const mockBucket = {
                tryConsume: jest.fn(),
                getTokenCount: jest.fn().mockReturnValue(0),
                getTimeUntilNextToken: jest.fn().mockReturnValue(1000)
            };
            mockBucket.tryConsume
                .mockReturnValueOnce(true) // First request succeeds
                .mockReturnValueOnce(true) // Second request succeeds
                .mockReturnValue(false); // Subsequent requests fail
            const mockCleanupLimiter = jest.fn().mockImplementation((req, res, next) => {
                if (!mockBucket.tryConsume()) {
                    return res.status(429).json({
                        error: 'Too many requests',
                        message: 'Burst limit exceeded',
                        details: {
                            tokensRemaining: mockBucket.getTokenCount(),
                            nextTokenIn: mockBucket.getTimeUntilNextToken()
                        }
                    });
                }
                return next();
            });
            app.post('/api/alerts/cleanup', mockCleanupLimiter, (req, res) => {
                res.json({ success: true });
            });
            // Make burst requests
            const responses = await Promise.all([
                (0, supertest_1.default)(app).post('/api/alerts/cleanup').send({ dryRun: true }),
                (0, supertest_1.default)(app).post('/api/alerts/cleanup').send({ dryRun: true }),
                (0, supertest_1.default)(app).post('/api/alerts/cleanup').send({ dryRun: true })
            ]);
            expect(responses[0].status).toBe(200);
            expect(responses[1].status).toBe(200);
            expect(responses[2].status).toBe(429);
            expect(responses[2].body).toMatchObject({
                error: 'Too many requests',
                message: 'Burst limit exceeded',
                details: {
                    tokensRemaining: 0,
                    nextTokenIn: 1000
                }
            });
        });
        it('should expose rate limit metrics', async () => {
            const response = await (0, supertest_1.default)(app).get('/api/alerts/metrics');
            expect(response.status).toBe(200);
            expect(response.body).toHaveProperty('metrics');
            expect(response.body.metrics).toEqual(expect.arrayContaining([
                expect.objectContaining({
                    name: 'rate_limit_hits_total',
                    help: 'Number of rate limit hits'
                }),
                expect.objectContaining({
                    name: 'rate_limit_tokens_remaining',
                    help: 'Number of tokens remaining in bucket'
                })
            ]));
        });
    });
});
//# sourceMappingURL=alertService.test.js.map