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
exports.GANTrainer = void 0;
const tf = __importStar(require("@tensorflow/tfjs-node"));
class GANTrainer {
    constructor(logger, config, inputDim = 4) {
        this.logger = logger;
        this.config = config;
        this.inputDim = inputDim;
        this.generator = this.buildGenerator();
        this.discriminator = this.buildDiscriminator();
        this.combined = this.buildCombined();
    }
    buildGenerator() {
        const model = tf.sequential();
        model.add(tf.layers.dense({
            units: this.config.hiddenUnits[0],
            inputShape: [this.inputDim],
            activation: 'relu'
        }));
        model.add(tf.layers.dense({
            units: this.config.hiddenUnits[1],
            activation: 'relu'
        }));
        model.add(tf.layers.dense({
            units: 4,
            activation: 'sigmoid'
        }));
        model.compile({
            optimizer: tf.train.adam(this.config.learningRate),
            loss: 'binaryCrossentropy'
        });
        return model;
    }
    buildDiscriminator() {
        const model = tf.sequential();
        model.add(tf.layers.dense({
            units: this.config.hiddenUnits[1],
            inputShape: [4],
            activation: 'relu'
        }));
        model.add(tf.layers.dense({
            units: this.config.hiddenUnits[2],
            activation: 'relu'
        }));
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
    buildCombined() {
        const input = tf.input({ shape: [this.inputDim] });
        let currentLayer = input;
        for (const layer of this.generator.layers) {
            currentLayer = layer.apply(currentLayer);
        }
        this.discriminator.trainable = false;
        for (const layer of this.discriminator.layers) {
            currentLayer = layer.apply(currentLayer);
        }
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
    async trainGAN(realData, epochs, batchSize) {
        if (realData.length === 0) {
            throw new Error('No training data provided');
        }
        for (let epoch = 0; epoch < epochs; epoch++) {
            const noise = tf.randomNormal([batchSize, this.inputDim]);
            const genScenarios = this.generator.predict(noise);
            const realLabels = tf.ones([batchSize, 1]);
            const fakeLabels = tf.zeros([batchSize, 1]);
            const realTensor = this.preprocessData(realData.slice(0, batchSize));
            const dRealLoss = await this.discriminator.trainOnBatch(realTensor, realLabels);
            const dFakeLoss = await this.discriminator.trainOnBatch(genScenarios, fakeLabels);
            const combinedLoss = await this.combined.trainOnBatch(noise, realLabels);
            this.logTrainingProgress(dRealLoss, dFakeLoss, combinedLoss);
            noise.dispose();
            genScenarios.dispose();
            realLabels.dispose();
            fakeLabels.dispose();
            realTensor.dispose();
        }
    }
    predictAdversarialImpact(trade) {
        try {
            const tradeFeatures = tf.tensor2d([[
                    Number(trade.success),
                    trade.profit ? Number(trade.profit) : 0,
                    trade.gasUsed ? Number(trade.gasUsed) : 0,
                    trade.route ? trade.route.length : 0
                ]]);
            const prediction = this.discriminator.predict(tradeFeatures);
            const impact = prediction.dataSync()[0];
            tradeFeatures.dispose();
            prediction.dispose();
            return Math.floor(impact * 100);
        }
        catch (error) {
            this.logger.error('Error predicting adversarial impact:', error);
            return 15;
        }
    }
    preprocessData(data) {
        return tf.tensor2d(data.map(scenario => [
            scenario.liquidityShock,
            scenario.gasPriceSpike,
            scenario.competitorActivity,
            scenario.marketVolatility
        ]));
    }
    logTrainingProgress(dRealLoss, dFakeLoss, combinedLoss) {
        const metrics = {
            discRealLoss: Array.isArray(dRealLoss) ? dRealLoss[0] : dRealLoss,
            discRealAcc: Array.isArray(dRealLoss) ? dRealLoss[1] : 0,
            discFakeLoss: Array.isArray(dFakeLoss) ? dFakeLoss[0] : dFakeLoss,
            discFakeAcc: Array.isArray(dFakeLoss) ? dFakeLoss[1] : 0,
            ganLoss: Array.isArray(combinedLoss) ? combinedLoss[0] : combinedLoss
        };
        this.logger.debug('Training metrics:', metrics);
    }
    generateScenarios(count) {
        const noise = tf.randomNormal([count, this.inputDim]);
        const generated = this.generator.predict(noise);
        const scenariosArray = Array.from(generated.dataSync());
        noise.dispose();
        generated.dispose();
        const scenarios = [];
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
    async saveModel(path) {
        await this.generator.save(`file://${path}/generator`);
        await this.discriminator.save(`file://${path}/discriminator`);
    }
    async loadModel(path) {
        this.generator = await tf.loadLayersModel(`file://${path}/generator/model.json`);
        this.discriminator = await tf.loadLayersModel(`file://${path}/discriminator/model.json`);
        this.combined = this.buildCombined();
    }
    async trainOnBatch(scenarios, batchSize) {
        return {
            loss: 0,
            accuracy: 0
        };
    }
    async validate(scenarios) {
        return {
            loss: 0,
            accuracy: 0
        };
    }
    async getModelState() {
        const weights = await this.getWeights();
        return weights.map(w => Array.from(w.dataSync()));
    }
    async getWeights() {
        return this.generator.layers.map(layer => layer.getWeights()).flat();
    }
    async getGradients() {
        const gradients = await tf.tidy(() => {
            const input = tf.randomNormal([1, this.inputDim]);
            return tf.gradients(() => this.generator.predict(input));
        });
        return gradients;
    }
    calculateGradients(input) {
        return tf.tidy(() => {
            const g = tf.grads((x) => {
                const pred = this.generator.predict(x);
                return pred;
            });
            const grads = g(input);
            return Array.isArray(grads) ? grads : [grads];
        });
    }
}
exports.GANTrainer = GANTrainer;
//# sourceMappingURL=gan_trainer.js.map