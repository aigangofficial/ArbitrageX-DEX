import { Logger } from 'winston';
import { Redis } from 'ioredis';
import { GANTrainer } from './gan_trainer';
import { SimulationScenario } from '../api/config';
import { CompetitorPattern } from './competitor_analyzer';

interface TrainingNode {
    id: string;
    endpoint: string;
    status: 'active' | 'training' | 'syncing' | 'offline';
    lastHeartbeat: number;
    capacity: {
        maxBatchSize: number;
        gpuMemory: number;
        currentLoad: number;
    };
}

interface TrainingJob {
    id: string;
    scenarios: SimulationScenario[];
    modelVersion: string;
    status: 'pending' | 'running' | 'completed' | 'failed';
    assignedNode?: string;
    startTime?: number;
    completionTime?: number;
    metrics?: {
        loss: number;
        accuracy: number;
        epochsCompleted: number;
    };
}

interface ModelMetadata {
    version: string;
    timestamp: number;
    metrics: {
        accuracy: number;
        loss: number;
        quantumSafetyScore: number;
    };
    compatibleNodes: string[];
}

export class DistributedOrchestrator {
    private nodes: Map<string, TrainingNode> = new Map();
    private jobs: Map<string, TrainingJob> = new Map();
    private models: Map<string, ModelMetadata> = new Map();
    private primaryNode: string | null = null;
    private readonly healthCheckInterval = 30000; // 30 seconds
    private readonly syncInterval = 300000; // 5 minutes

    constructor(
        private readonly logger: Logger,
        private readonly redis: Redis,
        private readonly ganTrainer: GANTrainer,
        private readonly config: {
            minNodes: number;
            syncThreshold: number;
            maxJobRetries: number;
            modelCheckpointInterval: number;
            regions: Array<{
                id: string;
                endpoint: string;
                priority: number;
            }>;
        }
    ) {}

    async start(): Promise<void> {
        try {
            await this.initializeNodes();
            await this.electPrimaryNode();
            this.startHealthChecks();
            this.startModelSync();
            this.logger.info('Distributed orchestrator started successfully');
        } catch (error) {
            this.logger.error('Failed to start distributed orchestrator:', error);
            throw error;
        }
    }

    async submitTrainingJob(
        scenarios: SimulationScenario[],
        competitor: CompetitorPattern
    ): Promise<string> {
        const jobId = `job_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        
        const job: TrainingJob = {
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

    private async assignJobToNode(job: TrainingJob): Promise<void> {
        const availableNodes = Array.from(this.nodes.values())
            .filter(node => node.status === 'active' && node.capacity.currentLoad < 0.8);

        if (availableNodes.length === 0) {
            this.logger.warn('No available nodes for training job:', job.id);
            return;
        }

        // Select node with lowest load
        const selectedNode = availableNodes.reduce((a, b) => 
            a.capacity.currentLoad < b.capacity.currentLoad ? a : b
        );

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

    private async notifyNode(nodeId: string, job: TrainingJob): Promise<void> {
        const node = this.nodes.get(nodeId);
        if (!node) return;

        try {
            const response = await fetch(`${node.endpoint}/train`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(job)
            });

            if (!response.ok) {
                throw new Error(`Node ${nodeId} rejected training job: ${response.statusText}`);
            }
        } catch (error) {
            this.logger.error(`Failed to notify node ${nodeId}:`, error);
            await this.handleNodeFailure(nodeId, job);
        }
    }

    private async handleNodeFailure(nodeId: string, job: TrainingJob): Promise<void> {
        const node = this.nodes.get(nodeId);
        if (!node) return;

        node.status = 'offline';
        await this.redis.hset(`nodes:${nodeId}`, 'status', 'offline');

        // Reassign job if possible
        job.status = 'pending';
        job.assignedNode = undefined;
        await this.assignJobToNode(job);

        // Trigger primary node re-election if needed
        if (this.primaryNode === nodeId) {
            await this.electPrimaryNode();
        }
    }

    private async electPrimaryNode(): Promise<void> {
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

    private startHealthChecks(): void {
        setInterval(async () => {
            for (const [nodeId, node] of this.nodes.entries()) {
                try {
                    const response = await fetch(`${node.endpoint}/health`);
                    if (!response.ok) {
                        throw new Error(`Health check failed: ${response.statusText}`);
                    }

                    const health = await response.json();
                    await this.updateNodeStatus(nodeId, health);
                } catch (error) {
                    this.logger.error(`Health check failed for node ${nodeId}:`, error);
                    await this.handleNodeFailure(nodeId, 
                        Array.from(this.jobs.values())
                            .find(job => job.assignedNode === nodeId)!
                    );
                }
            }
        }, this.healthCheckInterval);
    }

    private async updateNodeStatus(
        nodeId: string,
        health: unknown
    ): Promise<void> {
        const node = this.nodes.get(nodeId);
        if (!node) return;

        // Type guard for health response
        if (!health || typeof health !== 'object' || !('load' in health) || !('memory' in health)) {
            throw new Error('Invalid health response format');
        }

        const typedHealth = health as { load: number; memory: number };

        node.lastHeartbeat = Date.now();
        node.capacity.currentLoad = typedHealth.load;
        node.status = 'active';

        await this.redis.hset(`nodes:${nodeId}`, {
            lastHeartbeat: node.lastHeartbeat,
            status: node.status,
            currentLoad: node.capacity.currentLoad
        });
    }

    private startModelSync(): void {
        setInterval(async () => {
            if (this.primaryNode !== null && this.isPrimary()) {
                await this.synchronizeModels();
            }
        }, this.syncInterval);
    }

    private async synchronizeModels(): Promise<void> {
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
            } catch (error) {
                this.logger.error(`Model sync failed for node ${node.id}:`, error);
            }
        }
    }

    private async getCurrentModelVersion(): Promise<string> {
        const version = await this.redis.get('current_model_version');
        return version ?? '0.0.1';
    }

    private isPrimary(): boolean {
        return this.primaryNode === Array.from(this.nodes.values())[0]?.id;
    }

    private async initializeNodes(): Promise<void> {
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