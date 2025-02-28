import * as tf from '@tensorflow/tfjs-node';
import { LayersModel } from '@tensorflow/tfjs-node';
import { SimulationScenario } from '../api/config';
import { Logger } from 'winston';

interface AdversarialImpactInput {
    success: boolean;
    profit?: bigint;
    gasUsed?: bigint;
    route?: string[];
}

export interface TrainingResult {
    loss: number;
    accuracy: number;
}

export class GANTrainer {
    private generator: tf.LayersModel;
    private discriminator: tf.LayersModel;
    private combined: tf.LayersModel;
    
    constructor(
        private readonly logger: Logger,
        private readonly config: {
            hiddenUnits: number[];
            learningRate: number;
        },
        private readonly inputDim: number = 4
    ) {
        this.generator = this.buildGenerator();
        this.discriminator = this.buildDiscriminator();
        this.combined = this.buildCombined();
    }

    private buildGenerator(): tf.LayersModel {
        const model = tf.sequential();
        
        // Input layer
        model.add(tf.layers.dense({
            units: this.config.hiddenUnits[0],
            inputShape: [this.inputDim],
            activation: 'relu'
        }));

        // Hidden layers
        model.add(tf.layers.dense({
            units: this.config.hiddenUnits[1],
            activation: 'relu'
        }));

        // Output layer - generates market scenarios
        model.add(tf.layers.dense({
            units: 4, // matches SimulationScenario shape
            activation: 'sigmoid'
        }));

        model.compile({
            optimizer: tf.train.adam(this.config.learningRate),
            loss: 'binaryCrossentropy'
        });

        return model;
    }

    private buildDiscriminator(): tf.LayersModel {
        const model = tf.sequential();
        
        // Input layer
        model.add(tf.layers.dense({
            units: this.config.hiddenUnits[1],
            inputShape: [4], // matches SimulationScenario shape
            activation: 'relu'
        }));

        // Hidden layer
        model.add(tf.layers.dense({
            units: this.config.hiddenUnits[2],
            activation: 'relu'
        }));

        // Output layer - real/fake classification
        model.add(tf.layers.dense({
            units: 1,
            activation: 'sigmoid'
        }));

        model.compile({
            optimizer: tf.train.adam(this.config.learningRate),
            loss: 'binaryCrossentropy',
            metrics: ['accuracy']
        });

        return model;
    }

    private buildCombined(): tf.LayersModel {
        // Create symbolic input
        const input = tf.input({shape: [this.inputDim]});
        
        // Build generator path using functional API
        let currentLayer = input;
        for (const layer of this.generator.layers) {
            currentLayer = layer.apply(currentLayer) as typeof input;
        }
        
        // Freeze discriminator weights
        this.discriminator.trainable = false;
        
        // Build discriminator path
        for (const layer of this.discriminator.layers) {
            currentLayer = layer.apply(currentLayer) as typeof input;
        }

        // Create combined model
        const model = tf.model({
            inputs: input,
            outputs: currentLayer
        });

        model.compile({
            optimizer: tf.train.adam(this.config.learningRate),
            loss: 'binaryCrossentropy'
        });

        return model;
    }

    async trainGAN(
        realData: SimulationScenario[], 
        epochs: number,
        batchSize: number
    ): Promise<void> {
        if (realData.length === 0) {
            throw new Error('No training data provided');
        }

        for (let epoch = 0; epoch < epochs; epoch++) {
            // Generate random noise for fake scenarios
            const noise = tf.randomNormal([batchSize, this.inputDim]);
            
            // Generate fake scenarios
            const genScenarios = this.generator.predict(noise) as tf.Tensor;
            
            // Train discriminator
            const realLabels = tf.ones([batchSize, 1]);
            const fakeLabels = tf.zeros([batchSize, 1]);
            
            const realTensor = this.preprocessData(realData.slice(0, batchSize));
            
            const dRealLoss = await this.discriminator.trainOnBatch(realTensor, realLabels);
            const dFakeLoss = await this.discriminator.trainOnBatch(genScenarios, fakeLabels);
            
            // Train generator through combined model
            const combinedLoss = await this.combined.trainOnBatch(noise, realLabels);
            
            // Log progress
            this.logTrainingProgress(epoch, {
                discRealLoss: dRealLoss[0],
                discRealAcc: dRealLoss[1],
                discFakeLoss: dFakeLoss[0],
                discFakeAcc: dFakeLoss[1],
                ganLoss: combinedLoss[0]
            });

            // Clean up tensors
            noise.dispose();
            genScenarios.dispose();
            realLabels.dispose();
            fakeLabels.dispose();
            realTensor.dispose();
        }
    }

    predictAdversarialImpact(trade: AdversarialImpactInput): number {
        try {
            // Convert trade data to tensor format
            const tradeFeatures = tf.tensor2d([[
                Number(trade.success),
                trade.profit ? Number(trade.profit) : 0,
                trade.gasUsed ? Number(trade.gasUsed) : 0,
                trade.route ? trade.route.length : 0
            ]]);

            // Get adversarial prediction from discriminator
            const prediction = this.discriminator.predict(tradeFeatures) as tf.Tensor;
            const impact = prediction.dataSync()[0];

            // Clean up tensors
            tradeFeatures.dispose();
            prediction.dispose();

            // Return impact as percentage (0-100)
            return Math.floor(impact * 100);
        } catch (error) {
            this.logger.error('Error predicting adversarial impact:', error);
            return 15; // Default to 15% impact on error
        }
    }

    private preprocessData(data: SimulationScenario[]): tf.Tensor {
        return tf.tensor2d(data.map(scenario => [
            scenario.liquidityShock,
            scenario.gasPriceSpike,
            scenario.competitorActivity,
            scenario.marketVolatility
        ]));
    }

    private logTrainingProgress(
        epoch: number,
        metrics: {
            discRealLoss: number;
            discRealAcc: number;
            discFakeLoss: number;
            discFakeAcc: number;
            ganLoss: number;
        }
    ): void {
        this.logger.info(`Epoch ${epoch + 1} - D Real Loss: ${metrics.discRealLoss.toFixed(4)}, Acc: ${metrics.discRealAcc.toFixed(4)}`);
        this.logger.info(`Epoch ${epoch + 1} - D Fake Loss: ${metrics.discFakeLoss.toFixed(4)}, Acc: ${metrics.discFakeAcc.toFixed(4)}`);
        this.logger.info(`Epoch ${epoch + 1} - G Loss: ${metrics.ganLoss.toFixed(4)}`);
    }

    generateScenarios(count: number): SimulationScenario[] {
        const noise = tf.randomNormal([count, this.inputDim]);
        const generated = this.generator.predict(noise) as tf.Tensor;
        const scenariosArray = Array.from(generated.dataSync());
        
        noise.dispose();
        generated.dispose();
        
        const scenarios: SimulationScenario[] = [];
        for (let i = 0; i < count; i++) {
            scenarios.push({
                liquidityShock: scenariosArray[i * 4],
                gasPriceSpike: scenariosArray[i * 4 + 1],
                competitorActivity: scenariosArray[i * 4 + 2],
                marketVolatility: scenariosArray[i * 4 + 3]
            });
        }
        
        return scenarios;
    }

    async saveModel(path: string): Promise<void> {
        await this.generator.save(`file://${path}/generator`);
        await this.discriminator.save(`file://${path}/discriminator`);
    }

    async loadModel(path: string): Promise<void> {
        this.generator = await tf.loadLayersModel(`file://${path}/generator/model.json`);
        this.discriminator = await tf.loadLayersModel(`file://${path}/discriminator/model.json`);
        this.combined = this.buildCombined();
    }

    async trainOnBatch(
        scenarios: SimulationScenario[],
        batchSize: number
    ): Promise<TrainingResult> {
        // Implementation details
        return {
            loss: 0,
            accuracy: 0
        };
    }

    async validate(scenarios: SimulationScenario[]): Promise<TrainingResult> {
        // Implementation details
        return {
            loss: 0,
            accuracy: 0
        };
    }

    async getModelState(): Promise<number[][]> {
        const weights = await this.getWeights();
        return weights.map(w => Array.from(w.dataSync()));
    }

    async getWeights(): Promise<tf.Tensor[]> {
        return this.generator.layers.map(layer => layer.getWeights()).flat();
    }

    async getGradients(): Promise<tf.Tensor[]> {
        const gradients = await tf.tidy(() => {
            const input = tf.randomNormal([1, this.inputDim]);
            return tf.gradients(() => this.generator.predict(input) as tf.Tensor);
        });
        return gradients;
    }
} 