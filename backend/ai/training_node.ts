import { Logger } from 'winston';
import { Redis } from 'ioredis';
import { GANTrainer } from './gan_trainer';
import { QuantumValidator } from './quantum_validator';
import { SimulationScenario } from '../api/config';
import { CompetitorPattern } from './competitor_analyzer';
import * as tf from '@tensorflow/tfjs-node';

interface TrainingMetrics {
    loss: number;
    accuracy: number;
    epochsCompleted: number;
    quantumSafetyScore: number;
    gradientNorm: number;
    validationLoss: number;
}

interface ModelCheckpoint {
    version: string;
    timestamp: number;
    weights: tf.Tensor[];
    metrics: TrainingMetrics;
    quantumSignature: string;
}

export class TrainingNode {
    private currentJob: {
        id: string;
        startTime: number;
        metrics: TrainingMetrics;
    } | null = null;

    private modelCheckpoints: ModelCheckpoint[] = [];
    private readonly maxCheckpoints = 5;
    private isTraining = false;

    constructor(
        private readonly nodeId: string,
        private readonly logger: Logger,
        private readonly redis: Redis,
        private readonly ganTrainer: GANTrainer,
        private readonly quantumValidator: QuantumValidator,
        private readonly config: {
            batchSize: number;
            epochs: number;
            learningRate: number;
            checkpointInterval: number;
            quantumSafetyThreshold: number;
            maxGradientNorm: number;
            validationSplit: number;
        }
    ) {}

    async handleTrainingJob(job: {
        id: string;
        scenarios: SimulationScenario[];
        competitor: CompetitorPattern;
    }): Promise<void> {
        if (this.isTraining) {
            throw new Error('Node is already training');
        }

        try {
            this.isTraining = true;
            this.currentJob = {
                id: job.id,
                startTime: Date.now(),
                metrics: this.initializeMetrics()
            };

            await this.updateJobStatus(job.id, 'running');
            await this.trainModel(job.scenarios, job.competitor);
            await this.updateJobStatus(job.id, 'completed');

        } catch (error) {
            this.logger.error(`Training failed for job ${job.id}:`, error);
            await this.updateJobStatus(job.id, 'failed');
            throw error;

        } finally {
            this.isTraining = false;
            this.currentJob = null;
        }
    }

    private async trainModel(
        scenarios: SimulationScenario[],
        competitor: CompetitorPattern
    ): Promise<void> {
        const validationSplit = Math.floor(scenarios.length * this.config.validationSplit);
        const trainingScenarios = scenarios.slice(0, -validationSplit);
        const validationScenarios = scenarios.slice(-validationSplit);

        let epoch = 0;
        while (epoch < this.config.epochs) {
            // Train one epoch
            const metrics = await this.trainEpoch(trainingScenarios, validationScenarios);
            
            // Update metrics
            if (this.currentJob) {
                this.currentJob.metrics = metrics;
                await this.updateJobMetrics(this.currentJob.id, metrics);
            }

            // Validate quantum safety
            const quantumSafe = await this.validateQuantumSafety(metrics);
            if (!quantumSafe) {
                this.logger.warn('Training halted due to quantum safety concerns');
                break;
            }

            // Create checkpoint if needed
            if (epoch % this.config.checkpointInterval === 0) {
                await this.createCheckpoint(metrics);
            }

            epoch++;
        }
    }

    private async trainEpoch(
        trainingScenarios: SimulationScenario[],
        validationScenarios: SimulationScenario[]
    ): Promise<TrainingMetrics> {
        // Train on batches
        const batchMetrics = await this.ganTrainer.trainOnBatch(
            trainingScenarios,
            this.config.batchSize
        );

        // Validate
        const validationMetrics = await this.ganTrainer.validate(validationScenarios);

        // Calculate gradient norm
        const gradientNorm = await this.calculateGradientNorm();

        return {
            loss: batchMetrics.loss,
            accuracy: batchMetrics.accuracy,
            epochsCompleted: (this.currentJob?.metrics.epochsCompleted || 0) + 1,
            quantumSafetyScore: await this.calculateQuantumSafetyScore(batchMetrics),
            gradientNorm,
            validationLoss: validationMetrics.loss
        };
    }

    private async validateQuantumSafety(metrics: TrainingMetrics): Promise<boolean> {
        // Check quantum safety score
        if (metrics.quantumSafetyScore < this.config.quantumSafetyThreshold) {
            return false;
        }

        // Check gradient norm for potential attacks
        if (metrics.gradientNorm > this.config.maxGradientNorm) {
            return false;
        }

        // Validate model state
        const modelState = await this.ganTrainer.getModelState();
        const validationResult = await this.quantumValidator.validateModelState(modelState);

        return validationResult.isValid;
    }

    private async calculateQuantumSafetyScore(metrics: {
        loss: number;
        accuracy: number;
    }): Promise<number> {
        const modelState = await this.ganTrainer.getModelState();
        const { quantumSafetyScore } = await this.quantumValidator.validateModelState(modelState);
        
        // Combine with training metrics
        return (quantumSafetyScore * 0.7) + 
               (metrics.accuracy * 0.15) + 
               ((1 - metrics.loss) * 0.15);
    }

    private async calculateGradientNorm(): Promise<number> {
        const gradients = await this.ganTrainer.getGradients();
        return tf.tidy(() => {
            const flattenedGradients = gradients.map(g => g.reshape([-1]));
            const concatenated = tf.concat(flattenedGradients);
            return tf.norm(concatenated).dataSync()[0];
        });
    }

    private async createCheckpoint(metrics: TrainingMetrics): Promise<void> {
        const weights = await this.ganTrainer.getWeights();
        const checkpoint: ModelCheckpoint = {
            version: `${this.nodeId}_${Date.now()}`,
            timestamp: Date.now(),
            weights,
            metrics,
            quantumSignature: await this.generateQuantumSignature(weights)
        };

        this.modelCheckpoints.push(checkpoint);
        if (this.modelCheckpoints.length > this.maxCheckpoints) {
            this.modelCheckpoints.shift();
        }

        await this.saveCheckpoint(checkpoint);
    }

    private async generateQuantumSignature(weights: tf.Tensor[]): Promise<string> {
        const modelState = weights.map(w => Array.from(w.dataSync()));
        return this.quantumValidator.signModelState(modelState);
    }

    private async saveCheckpoint(checkpoint: ModelCheckpoint): Promise<void> {
        await this.redis.hset(
            `model_checkpoints:${checkpoint.version}`,
            {
                ...checkpoint,
                weights: JSON.stringify(checkpoint.weights.map(w => Array.from(w.dataSync())))
            }
        );
    }

    private async updateJobStatus(
        jobId: string,
        status: 'running' | 'completed' | 'failed'
    ): Promise<void> {
        await this.redis.hset(`training_jobs:${jobId}`, 'status', status);
    }

    private async updateJobMetrics(jobId: string, metrics: TrainingMetrics): Promise<void> {
        await this.redis.hset(`training_jobs:${jobId}`, {
            metrics: JSON.stringify(metrics),
            lastUpdate: Date.now()
        });
    }

    private initializeMetrics(): TrainingMetrics {
        return {
            loss: 0,
            accuracy: 0,
            epochsCompleted: 0,
            quantumSafetyScore: 1,
            gradientNorm: 0,
            validationLoss: 0
        };
    }

    getStatus(): {
        isTraining: boolean;
        currentJob: {
            id: string;
            startTime: number;
            metrics: TrainingMetrics;
        } | null;
        metrics: TrainingMetrics | null;
    } {
        return {
            isTraining: this.isTraining,
            currentJob: this.currentJob,
            metrics: this.currentJob?.metrics || null
        };
    }
} 