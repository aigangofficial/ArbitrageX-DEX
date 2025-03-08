"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const gan_trainer_1 = require("../gan_trainer");
describe('GANTrainer', () => {
    let trainer;
    let mockLogger;
    const mockConfig = {
        hiddenUnits: [16, 8, 4],
        learningRate: 0.0002
    };
    const mockScenarios = [
        {
            liquidityShock: 0.3,
            gasPriceSpike: 0.5,
            competitorActivity: 0.8,
            marketVolatility: 0.4
        },
        {
            liquidityShock: 0.5,
            gasPriceSpike: 0.7,
            competitorActivity: 0.9,
            marketVolatility: 0.6
        }
    ];
    beforeEach(() => {
        mockLogger = {
            info: jest.fn(),
            error: jest.fn(),
            warn: jest.fn()
        };
        trainer = new gan_trainer_1.GANTrainer(mockLogger, mockConfig);
    });
    describe('trainGAN', () => {
        it('should train on provided scenarios without errors', async () => {
            await expect(trainer.trainGAN(mockScenarios, 2, 1))
                .resolves.not.toThrow();
            expect(mockLogger.info).toHaveBeenCalled();
            expect(mockLogger.error).not.toHaveBeenCalled();
        });
        it('should handle empty scenario list', async () => {
            await expect(trainer.trainGAN([], 1, 1))
                .rejects.toThrow();
            expect(mockLogger.error).toHaveBeenCalled();
        });
    });
    describe('generateScenarios', () => {
        it('should generate requested number of scenarios', () => {
            const count = 3;
            const scenarios = trainer.generateScenarios(count);
            expect(scenarios).toHaveLength(count);
            scenarios.forEach(scenario => {
                expect(scenario).toHaveProperty('liquidityShock');
                expect(scenario).toHaveProperty('gasPriceSpike');
                expect(scenario).toHaveProperty('competitorActivity');
                expect(scenario).toHaveProperty('marketVolatility');
                expect(scenario.liquidityShock).toBeGreaterThanOrEqual(0);
                expect(scenario.liquidityShock).toBeLessThanOrEqual(1);
                expect(scenario.gasPriceSpike).toBeGreaterThanOrEqual(0);
                expect(scenario.gasPriceSpike).toBeLessThanOrEqual(1);
                expect(scenario.competitorActivity).toBeGreaterThanOrEqual(0);
                expect(scenario.competitorActivity).toBeLessThanOrEqual(1);
                expect(scenario.marketVolatility).toBeGreaterThanOrEqual(0);
                expect(scenario.marketVolatility).toBeLessThanOrEqual(1);
            });
        });
    });
    describe('model persistence', () => {
        const testPath = './test-models';
        it('should save and load models', async () => {
            await trainer.saveModel(testPath);
            await expect(trainer.loadModel(testPath))
                .resolves.not.toThrow();
        });
    });
});
//# sourceMappingURL=gan_trainer.test.js.map