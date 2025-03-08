"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.DistributedOrchestrator = void 0;
class DistributedOrchestrator {
    constructor(logger, redis, ganTrainer, config) {
        this.logger = logger;
        this.redis = redis;
        this.ganTrainer = ganTrainer;
        this.config = config;
        this.nodes = new Map();
        this.jobs = new Map();
        this.models = new Map();
        this.primaryNode = null;
        this.healthCheckInterval = 30000;
        this.syncInterval = 300000;
    }
    async start() {
        try {
            await this.initializeNodes();
            await this.electPrimaryNode();
            this.startHealthChecks();
            this.startModelSync();
            this.logger.info('Distributed orchestrator started successfully');
        }
        catch (error) {
            this.logger.error('Failed to start distributed orchestrator:', error);
            throw error;
        }
    }
    async submitTrainingJob(scenarios, competitor) {
        const jobId = `job_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        const job = {
            id: jobId,
            scenarios,
            modelVersion: await this.getCurrentModelVersion(),
            status: 'pending'
        };
        await this.redis.hset(`training_jobs:${jobId}`, {
            ...job,
            scenarios: JSON.stringify(scenarios),
            competitor: JSON.stringify(competitor)
        });
        await this.assignJobToNode(job);
        return jobId;
    }
    async assignJobToNode(job) {
        const availableNodes = Array.from(this.nodes.values())
            .filter(node => node.status === 'active' && node.capacity.currentLoad < 0.8);
        if (availableNodes.length === 0) {
            this.logger.warn('No available nodes for training job:', job.id);
            return;
        }
        const selectedNode = availableNodes.reduce((a, b) => a.capacity.currentLoad < b.capacity.currentLoad ? a : b);
        job.assignedNode = selectedNode.id;
        job.status = 'running';
        job.startTime = Date.now();
        await this.redis.hset(`training_jobs:${job.id}`, {
            status: job.status,
            assignedNode: job.assignedNode,
            startTime: job.startTime
        });
        this.logger.info(`Assigned job ${job.id} to node ${selectedNode.id}`);
        await this.notifyNode(selectedNode.id, job);
    }
    async notifyNode(nodeId, job) {
        const node = this.nodes.get(nodeId);
        if (!node)
            return;
        try {
            const response = await fetch(`${node.endpoint}/train`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(job)
            });
            if (!response.ok) {
                throw new Error(`Node ${nodeId} rejected training job: ${response.statusText}`);
            }
        }
        catch (error) {
            this.logger.error(`Failed to notify node ${nodeId}:`, error);
            await this.handleNodeFailure(nodeId, job);
        }
    }
    async handleNodeFailure(nodeId, job) {
        const node = this.nodes.get(nodeId);
        if (!node)
            return;
        node.status = 'offline';
        await this.redis.hset(`nodes:${nodeId}`, 'status', 'offline');
        job.status = 'pending';
        job.assignedNode = undefined;
        await this.assignJobToNode(job);
        if (this.primaryNode === nodeId) {
            await this.electPrimaryNode();
        }
    }
    async electPrimaryNode() {
        const activeNodes = Array.from(this.nodes.values())
            .filter(node => node.status === 'active')
            .sort((a, b) => {
            const priorityA = this.config.regions.find(r => r.id === a.id)?.priority || 0;
            const priorityB = this.config.regions.find(r => r.id === b.id)?.priority || 0;
            return priorityA - priorityB;
        });
        if (activeNodes.length === 0) {
            throw new Error('No active nodes available for primary election');
        }
        const newPrimary = activeNodes[0].id;
        await this.redis.set('primary_node', newPrimary);
        this.primaryNode = newPrimary;
        this.logger.info(`Elected new primary node: ${newPrimary}`);
    }
    startHealthChecks() {
        setInterval(async () => {
            for (const [nodeId, node] of this.nodes.entries()) {
                try {
                    const response = await fetch(`${node.endpoint}/health`);
                    if (!response.ok) {
                        throw new Error(`Health check failed: ${response.statusText}`);
                    }
                    const health = await response.json();
                    await this.updateNodeStatus(nodeId, health);
                }
                catch (error) {
                    this.logger.error(`Health check failed for node ${nodeId}:`, error);
                    await this.handleNodeFailure(nodeId, Array.from(this.jobs.values())
                        .find(job => job.assignedNode === nodeId));
                }
            }
        }, this.healthCheckInterval);
    }
    async updateNodeStatus(nodeId, health) {
        const node = this.nodes.get(nodeId);
        if (!node)
            return;
        if (!health || typeof health !== 'object' || !('load' in health) || !('memory' in health)) {
            throw new Error('Invalid health response format');
        }
        const typedHealth = health;
        node.lastHeartbeat = Date.now();
        node.capacity.currentLoad = typedHealth.load;
        node.status = 'active';
        await this.redis.hset(`nodes:${nodeId}`, {
            lastHeartbeat: node.lastHeartbeat,
            status: node.status,
            currentLoad: node.capacity.currentLoad
        });
    }
    startModelSync() {
        setInterval(async () => {
            if (this.primaryNode !== null && this.isPrimary()) {
                await this.synchronizeModels();
            }
        }, this.syncInterval);
    }
    async synchronizeModels() {
        const activeNodes = Array.from(this.nodes.values())
            .filter(node => node.status === 'active');
        for (const node of activeNodes) {
            try {
                const response = await fetch(`${node.endpoint}/model/sync`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        version: await this.getCurrentModelVersion(),
                        timestamp: Date.now()
                    })
                });
                if (!response.ok) {
                    throw new Error(`Model sync failed: ${response.statusText}`);
                }
            }
            catch (error) {
                this.logger.error(`Model sync failed for node ${node.id}:`, error);
            }
        }
    }
    async getCurrentModelVersion() {
        const version = await this.redis.get('current_model_version');
        return version ?? '0.0.1';
    }
    isPrimary() {
        return this.primaryNode === Array.from(this.nodes.values())[0]?.id;
    }
    async initializeNodes() {
        for (const region of this.config.regions) {
            this.nodes.set(region.id, {
                id: region.id,
                endpoint: region.endpoint,
                status: 'offline',
                lastHeartbeat: 0,
                capacity: {
                    maxBatchSize: 32,
                    gpuMemory: 16384,
                    currentLoad: 0
                }
            });
        }
    }
}
exports.DistributedOrchestrator = DistributedOrchestrator;
//# sourceMappingURL=distributed_orchestrator.js.map