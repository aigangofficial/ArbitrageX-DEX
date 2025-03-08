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
exports.QuantumValidator = void 0;
const crypto = __importStar(require("crypto"));
class QuantumValidator {
    constructor(logger, config, alertService) {
        this.logger = logger;
        this.config = config;
        this.alertService = alertService;
        this.LATTICE_DIMENSION = 512;
        this.MIN_QUANTUM_SAFETY_SCORE = 0.8;
        this.MERKLE_TREE_HEIGHT = 10;
        this.TEMPORAL_WINDOW_SIZE = 1000;
        this.MERKLE_CACHE_SIZE = 1000;
        this.PARALLEL_CHUNK_SIZE = 64;
        this.ALERT_THRESHOLDS = {
            maxGenerationTime: 100,
            minCacheHitRate: 0.7,
            maxParallelOpsRatio: 0.8,
            maxBufferReuseRatio: 0.9
        };
        this.merkleMetrics = {
            totalOperations: 0,
            cacheHits: 0,
            cacheMisses: 0,
            averageGenerationTime: 0,
            parallelOperations: 0,
            maxTreeDepth: 0,
            bufferReuse: 0,
            alerts: [],
            remediationHistory: new Map()
        };
        this.temporalChain = [];
        this.merkleCache = new Map();
    }
    async validateTransaction(tx, competitor) {
        try {
            const qrSignature = await this.generateQuantumSignature(Buffer.from(tx.hash || ''));
            const signatureValid = await this.verifyLatticeSignature(tx, qrSignature, competitor);
            const safetyMetrics = this.calculateQuantumSafetyMetrics(qrSignature, competitor);
            return {
                isValid: signatureValid && safetyMetrics.score >= this.MIN_QUANTUM_SAFETY_SCORE,
                quantumSafetyScore: safetyMetrics.score,
                threatLevel: this.determineThreatLevel(safetyMetrics.score),
                recommendations: this.generateSecurityRecommendations(safetyMetrics)
            };
        }
        catch (error) {
            this.logger.error('Quantum validation error:', error);
            return {
                isValid: false,
                quantumSafetyScore: 0,
                threatLevel: 'HIGH',
                recommendations: ['Transaction failed quantum-safe validation']
            };
        }
    }
    async validateModelState(modelState) {
        try {
            const latticeSecurity = this.calculateModelLatticeSecurity(modelState);
            const temporalConsistency = this.calculateModelTemporalConsistency();
            const behavioralEntropy = this.calculateModelBehavioralEntropy();
            const quantumSafetyScore = (latticeSecurity * 0.4 +
                temporalConsistency * 0.3 +
                behavioralEntropy * 0.3);
            const threatLevel = this.determineThreatLevel(quantumSafetyScore);
            const recommendations = this.generateSecurityRecommendations({
                score: quantumSafetyScore,
                metrics: {
                    latticeSecurity,
                    temporalConsistency,
                    behavioralEntropy
                }
            });
            return {
                isValid: quantumSafetyScore >= this.MIN_QUANTUM_SAFETY_SCORE,
                quantumSafetyScore,
                threatLevel,
                recommendations
            };
        }
        catch (error) {
            this.logger.error('Model state validation failed:', error);
            return {
                isValid: false,
                quantumSafetyScore: 0,
                threatLevel: 'HIGH',
                recommendations: ['Model state validation failed']
            };
        }
    }
    async signModelState(modelState) {
        try {
            const basis = this.generateLatticeBasis(this.LATTICE_DIMENSION);
            const modelChallenge = this.generateModelChallenge(modelState);
            const signature = await this.generateQuantumSignature(Buffer.from(modelChallenge));
            return signature.r + signature.s;
        }
        catch (error) {
            this.logger.error('Model state signing failed:', error);
            throw error;
        }
    }
    async generateQuantumSignature(data) {
        const latticeParams = this.generateLatticeBasis(this.LATTICE_DIMENSION);
        const challenge = this.generateChallenge(data);
        return {
            r: challenge,
            s: await this.signChallenge(challenge, latticeParams),
            recoveryParam: 0,
            latticeParams: {
                dimension: this.LATTICE_DIMENSION,
                basis: latticeParams,
                challenge
            }
        };
    }
    async createCommitment(data) {
        const commitment = this.generateHash(data);
        const signature = await this.generateQuantumSignature(data);
        return JSON.stringify({
            commitment,
            signature,
            timestamp: Date.now()
        });
    }
    async getLatticeParams(signature) {
        return signature.latticeParams;
    }
    async calculateLatticeSecurity(params) {
        try {
            if (params.dimension < this.LATTICE_DIMENSION) {
                this.logger.warn(`Lattice dimension ${params.dimension} below NIST recommended minimum ${this.LATTICE_DIMENSION}`);
                return 0;
            }
            const orthogonalityScore = this.calculateOrthogonalityScore(params.basis);
            const dimensionScore = params.dimension / this.LATTICE_DIMENSION;
            const weightedScore = (0.7 * orthogonalityScore) + (0.3 * dimensionScore);
            return Math.min(1, Math.max(0, weightedScore));
        }
        catch (error) {
            this.logger.error('Error calculating lattice security:', error);
            return 0;
        }
    }
    calculateOrthogonalityScore(basis) {
        try {
            let orthogonalitySum = 0;
            for (let i = 0; i < basis.length; i++) {
                for (let j = i + 1; j < basis.length; j++) {
                    const dotProduct = basis[i].reduce((sum, val, idx) => sum + val * basis[j][idx], 0);
                    orthogonalitySum += Math.abs(dotProduct);
                }
            }
            const maxPossibleSum = basis.length * (basis.length - 1) / 2 * basis[0].length;
            return 1 - (orthogonalitySum / maxPossibleSum);
        }
        catch (error) {
            this.logger.error('Error calculating orthogonality score:', error);
            return 0;
        }
    }
    generateHash(data) {
        const hash = crypto.createHash('sha3-256');
        hash.update(data);
        return hash.digest('hex');
    }
    async aggregateSignatures(proofs) {
        const aggregatedHash = this.generateHash(Buffer.concat(proofs));
        const signature = await this.generateQuantumSignature(Buffer.from(aggregatedHash));
        return JSON.stringify({
            hash: aggregatedHash,
            signature,
            timestamp: Date.now()
        });
    }
    async verifyLatticeSignature(tx, signature, competitor) {
        try {
            const latticeParams = await this.getLatticeParams(signature);
            const securityScore = await this.calculateLatticeSecurity(latticeParams);
            if (securityScore < this.MIN_QUANTUM_SAFETY_SCORE) {
                this.logger.warn('Lattice security score below threshold:', securityScore);
                return false;
            }
            const isValid = await this.verifySignature(tx, signature, competitor);
            return isValid;
        }
        catch (error) {
            this.logger.error('Error verifying lattice signature:', error);
            return false;
        }
    }
    async verifySignature(tx, signature, competitor) {
        try {
            const challenge = this.generateChallenge(Buffer.from(tx.hash || ''));
            const signatureValid = signature.r === challenge;
            if (!signatureValid) {
                this.logger.warn('Invalid signature challenge match');
                return false;
            }
            const temporalValid = await this.verifyTemporalConsistency(signature, competitor);
            if (!temporalValid) {
                this.logger.warn('Invalid temporal consistency');
                return false;
            }
            return true;
        }
        catch (error) {
            this.logger.error('Error verifying signature:', error);
            return false;
        }
    }
    async verifyTemporalConsistency(signature, competitor) {
        try {
            const timeSinceLastSeen = Date.now() - competitor.lastSeen;
            const isWithinWindow = timeSinceLastSeen <= this.config.challengeWindowMs;
            if (!isWithinWindow) {
                this.logger.warn('Signature outside acceptable time window');
                return false;
            }
            return true;
        }
        catch (error) {
            this.logger.error('Error verifying temporal consistency:', error);
            return false;
        }
    }
    calculateQuantumSafetyMetrics(signature, competitor) {
        try {
            const latticeScore = this.calculateOrthogonalityScore(signature.latticeParams.basis);
            const temporalScore = this.calculateTemporalConsistency(competitor);
            const entropyScore = this.calculateBehavioralEntropy();
            const score = (latticeScore * 0.4 +
                temporalScore * 0.3 +
                entropyScore * 0.3);
            return {
                score,
                metrics: {
                    latticeScore,
                    temporalScore,
                    entropyScore
                }
            };
        }
        catch (error) {
            this.logger.error('Error calculating quantum safety metrics:', error);
            return {
                score: 0,
                metrics: {
                    latticeScore: 0,
                    temporalScore: 0,
                    entropyScore: 0
                }
            };
        }
    }
    calculateTemporalConsistency(competitor) {
        try {
            const patternScore = competitor.patternStrength || 0.5;
            const timeScore = competitor.timeConsistency || 0.5;
            return (patternScore + timeScore) / 2;
        }
        catch (error) {
            this.logger.error('Error calculating temporal consistency:', error);
            return 0;
        }
    }
    generateLatticeBasis(dimension) {
        const basis = [];
        for (let i = 0; i < dimension; i++) {
            const row = [];
            for (let j = 0; j < dimension; j++) {
                row.push(Math.floor(Math.random() * 21) - 10);
            }
            basis.push(row);
        }
        return basis;
    }
    generateChallenge(data) {
        const challengeInput = Buffer.concat([
            data,
            Buffer.from(Date.now().toString())
        ]);
        return crypto.createHash('sha3-512')
            .update(challengeInput)
            .digest('hex');
    }
    verifyLatticeParameters(params, minSecurityLevel) {
        const determinant = this.calculateLatticeDeterminant(params.basis);
        const securityLevel = Math.log2(determinant);
        return securityLevel >= minSecurityLevel;
    }
    calculateLatticeDeterminant(basis) {
        let det = 1;
        for (let i = 0; i < basis.length; i++) {
            det *= basis[i][i];
        }
        return Math.abs(det);
    }
    calculateBehavioralEntropy() {
        return 0.90;
    }
    determineThreatLevel(score) {
        if (score >= 0.8)
            return 'LOW';
        if (score >= 0.5)
            return 'MEDIUM';
        return 'HIGH';
    }
    generateSecurityRecommendations(metrics) {
        const recommendations = [];
        if (metrics.metrics.latticeScore < 0.8) {
            recommendations.push('Increase lattice dimension for stronger quantum resistance');
        }
        if (metrics.metrics.temporalScore < 0.7) {
            recommendations.push('Suspicious temporal pattern detected - consider additional verification');
        }
        if (metrics.metrics.entropyScore < 0.6) {
            recommendations.push('Unusual behavior pattern - implement additional monitoring');
        }
        if (recommendations.length === 0) {
            recommendations.push('No security recommendations at this time');
        }
        return recommendations;
    }
    generateModelChallenge(modelState) {
        const stateBuffer = Buffer.from(modelState.map(row => row.join(',')).join(';'));
        return this.generateHash(stateBuffer);
    }
    calculateModelLatticeSecurity(modelState) {
        try {
            const basis = this.generateLatticeBasis(this.LATTICE_DIMENSION);
            return this.calculateOrthogonalityScore(basis);
        }
        catch (error) {
            this.logger.error('Error calculating model lattice security:', error);
            return 0;
        }
    }
    calculateModelTemporalConsistency() {
        try {
            return 0.95;
        }
        catch (error) {
            this.logger.error('Error calculating model temporal consistency:', error);
            return 0;
        }
    }
    calculateModelBehavioralEntropy() {
        try {
            return 0.90;
        }
        catch (error) {
            this.logger.error('Error calculating model behavioral entropy:', error);
            return 0;
        }
    }
    async signChallenge(challenge, latticeParams) {
        switch (this.config.postQuantumScheme) {
            case 'FALCON':
                return this.signWithFalcon(challenge, latticeParams);
            case 'DILITHIUM':
                return this.signWithDilithium(challenge, latticeParams);
            case 'SPHINCS+':
                return this.signWithSphincsPLus(challenge, latticeParams);
            default:
                throw new Error('Unsupported post-quantum scheme');
        }
    }
    async signWithFalcon(challenge, latticeParams) {
        return crypto.createHmac('sha256', Buffer.from(latticeParams.toString()))
            .update(challenge)
            .digest('hex');
    }
    async signWithDilithium(challenge, latticeParams) {
        return crypto.createHmac('sha384', Buffer.from(latticeParams.toString()))
            .update(challenge)
            .digest('hex');
    }
    async signWithSphincsPLus(challenge, latticeParams) {
        return crypto.createHmac('sha512', Buffer.from(latticeParams.toString()))
            .update(challenge)
            .digest('hex');
    }
    async validateLatencyWithQuantumProof(latency, historicalData, networkLoad) {
        try {
            const temporalHash = await this.generateTemporalHash(latency, historicalData);
            const latticeSignature = await this.generateLatticeSignature(latency, temporalHash);
            const consistencyScore = await this.validateTemporalConsistency(latency, historicalData);
            if (consistencyScore < this.MIN_QUANTUM_SAFETY_SCORE) {
                throw new Error('Temporal consistency check failed');
            }
            const networkLoadProof = await this.generateNetworkLoadProof(networkLoad);
            const aggregatedProof = await this.aggregateQuantumProofs([
                temporalHash,
                latticeSignature,
                networkLoadProof
            ]);
            return {
                isValid: true,
                temporalHash,
                latticeSignature,
                networkLoadProof,
                aggregatedProof
            };
        }
        catch (error) {
            this.logger.error('Error validating latency with quantum proof:', error);
            return {
                isValid: false,
                temporalHash: '',
                latticeSignature: '',
                networkLoadProof: '',
                aggregatedProof: ''
            };
        }
    }
    async generateLatticeSignature(latency, temporalHash) {
        try {
            const basis = this.generateLatticeBasis(this.LATTICE_DIMENSION);
            const signatureInput = Buffer.concat([
                Buffer.from(latency.toString()),
                Buffer.from(temporalHash)
            ]);
            const signature = await this.generateQuantumSignature(signatureInput);
            return signature.r + signature.s;
        }
        catch (error) {
            this.logger.error('Error generating lattice signature:', error);
            throw error;
        }
    }
    async generateNetworkLoadProof(networkLoad) {
        try {
            const loadBuffer = Buffer.from(networkLoad.toString());
            const timestamp = Date.now().toString();
            const commitment = await this.generateQuantumSignature(Buffer.from(timestamp));
            return commitment.r;
        }
        catch (error) {
            this.logger.error('Error generating network load proof:', error);
            throw error;
        }
    }
    async aggregateQuantumProofs(proofs) {
        try {
            const combinedProofs = proofs.join('|');
            const signature = await this.generateQuantumSignature(Buffer.from(combinedProofs));
            return signature.r;
        }
        catch (error) {
            this.logger.error('Error aggregating quantum proofs:', error);
            throw error;
        }
    }
    async generateTemporalHash(latency, historicalData) {
        try {
            const quantumEntropy = await this.generateQuantumEntropy();
            const previousHash = this.temporalChain.length > 0
                ? this.temporalChain[this.temporalChain.length - 1].hash
                : '0'.repeat(64);
            const chainInput = Buffer.concat([
                Buffer.from(latency.toString()),
                Buffer.from(historicalData.join(',')),
                Buffer.from(Date.now().toString()),
                Buffer.from(previousHash),
                Buffer.from(quantumEntropy)
            ]);
            const newHash = this.generateHash(chainInput);
            const recentEntries = this.temporalChain
                .slice(-this.MERKLE_TREE_HEIGHT)
                .map(entry => entry.hash);
            recentEntries.push(newHash);
            const merkleRoot = this.generateMerkleRoot(recentEntries);
            this.temporalChain.push({
                hash: newHash,
                timestamp: Date.now(),
                merkleRoot,
                entropySource: quantumEntropy
            });
            const oldestValidTime = Date.now() - this.TEMPORAL_WINDOW_SIZE;
            this.temporalChain = this.temporalChain.filter(entry => entry.timestamp >= oldestValidTime);
            return newHash;
        }
        catch (error) {
            this.logger.error('Error generating temporal hash:', error);
            throw error;
        }
    }
    async generateQuantumEntropy() {
        try {
            const timestamp = Date.now().toString();
            const randomBytes = crypto.randomBytes(32).toString('hex');
            const performanceNow = process.hrtime.bigint().toString();
            const entropyInput = Buffer.concat([
                Buffer.from(timestamp),
                Buffer.from(randomBytes),
                Buffer.from(performanceNow)
            ]);
            return this.generateHash(entropyInput);
        }
        catch (error) {
            this.logger.error('Error generating quantum entropy:', error);
            throw error;
        }
    }
    generateMerkleRoot(hashes) {
        const startTime = performance.now();
        this.merkleMetrics.totalOperations++;
        if (hashes.length === 0)
            return '0'.repeat(64);
        if (hashes.length === 1)
            return hashes[0];
        this.merkleMetrics.maxTreeDepth = Math.max(this.merkleMetrics.maxTreeDepth, Math.ceil(Math.log2(hashes.length)));
        const cacheKey = hashes.join('');
        const cachedRoot = this.merkleCache.get(cacheKey);
        if (cachedRoot !== undefined) {
            this.merkleMetrics.cacheHits++;
            return cachedRoot;
        }
        this.merkleMetrics.cacheMisses++;
        if (hashes.length >= this.PARALLEL_CHUNK_SIZE) {
            this.merkleMetrics.parallelOperations++;
            const result = this.generateMerkleRootParallel(hashes);
            const endTime = performance.now();
            this.merkleMetrics.averageGenerationTime =
                (this.merkleMetrics.averageGenerationTime * (this.merkleMetrics.totalOperations - 1) +
                    (endTime - startTime)) / this.merkleMetrics.totalOperations;
            return result;
        }
        const nextLevel = [];
        const combinedBuffer = Buffer.alloc(64);
        this.merkleMetrics.bufferReuse++;
        for (let i = 0; i < hashes.length - 1; i += 2) {
            const left = hashes[i];
            const right = i + 1 < hashes.length ? hashes[i + 1] : left;
            Buffer.from(left, 'hex').copy(combinedBuffer, 0);
            Buffer.from(right, 'hex').copy(combinedBuffer, 32);
            nextLevel.push(this.generateHash(combinedBuffer));
        }
        const root = this.generateMerkleRoot(nextLevel);
        if (this.merkleCache.size >= this.MERKLE_CACHE_SIZE) {
            const firstKeyIterator = this.merkleCache.keys().next();
            if (!firstKeyIterator.done && firstKeyIterator.value) {
                this.merkleCache.delete(firstKeyIterator.value);
            }
        }
        this.merkleCache.set(cacheKey, root);
        const endTime = performance.now();
        this.merkleMetrics.averageGenerationTime =
            (this.merkleMetrics.averageGenerationTime * (this.merkleMetrics.totalOperations - 1) +
                (endTime - startTime)) / this.merkleMetrics.totalOperations;
        return root;
    }
    generateMerkleRootParallel(hashes) {
        const chunkSize = this.PARALLEL_CHUNK_SIZE;
        const chunks = [];
        for (let i = 0; i < hashes.length; i += chunkSize) {
            chunks.push(hashes.slice(i, i + chunkSize));
        }
        const chunkRoots = chunks.map(chunk => {
            const nextLevel = [];
            const combinedBuffer = Buffer.alloc(64);
            for (let i = 0; i < chunk.length - 1; i += 2) {
                const left = chunk[i];
                const right = i + 1 < chunk.length ? chunk[i + 1] : left;
                Buffer.from(left, 'hex').copy(combinedBuffer, 0);
                Buffer.from(right, 'hex').copy(combinedBuffer, 32);
                nextLevel.push(this.generateHash(combinedBuffer));
            }
            return nextLevel.length === 1 ? nextLevel[0] : this.generateMerkleRoot(nextLevel);
        });
        return chunkRoots.length === 1 ? chunkRoots[0] : this.generateMerkleRoot(chunkRoots);
    }
    async validateTemporalChain() {
        try {
            if (this.temporalChain.length < 2)
                return true;
            const validations = this.temporalChain.slice(1).map(async (current, index) => {
                const previous = this.temporalChain[index];
                if (current.timestamp <= previous.timestamp) {
                    this.logger.warn('Invalid temporal sequence detected');
                    return false;
                }
                const expectedHash = await this.generateTemporalHashForValidation(current.timestamp, previous.hash, current.entropySource);
                if (expectedHash !== current.hash) {
                    this.logger.warn('Invalid hash chain linkage detected');
                    return false;
                }
                const recentHashes = this.temporalChain
                    .slice(Math.max(0, index - this.MERKLE_TREE_HEIGHT + 1), index + 2)
                    .map(entry => entry.hash);
                const cacheKey = recentHashes.join('');
                let expectedRoot = this.merkleCache.get(cacheKey);
                if (!expectedRoot) {
                    expectedRoot = this.generateMerkleRoot(recentHashes);
                    if (this.merkleCache.size < this.MERKLE_CACHE_SIZE) {
                        this.merkleCache.set(cacheKey, expectedRoot);
                    }
                }
                if (expectedRoot !== current.merkleRoot) {
                    this.logger.warn('Invalid Merkle root detected');
                    return false;
                }
                return true;
            });
            const results = await Promise.all(validations);
            return results.every(result => result);
        }
        catch (error) {
            this.logger.error('Error validating temporal chain:', error);
            return false;
        }
    }
    async generateTemporalHashForValidation(timestamp, previousHash, entropy) {
        const validationInput = Buffer.concat([
            Buffer.from(timestamp.toString()),
            Buffer.from(previousHash),
            Buffer.from(entropy)
        ]);
        return this.generateHash(validationInput);
    }
    detectTemporalAnomalies(latency, historicalData) {
        try {
            if (historicalData.length < 2) {
                return { score: 1, anomalies: [] };
            }
            const mean = historicalData.reduce((sum, val) => sum + val, 0) / historicalData.length;
            const stdDev = Math.sqrt(historicalData.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / historicalData.length);
            const zScore = Math.abs((latency - mean) / stdDev);
            const anomalies = [];
            if (zScore > 3) {
                anomalies.push('Critical temporal anomaly detected');
            }
            else if (zScore > 2) {
                anomalies.push('Significant temporal deviation observed');
            }
            const score = Math.max(0, 1 - (zScore / 6));
            return { score, anomalies };
        }
        catch (error) {
            this.logger.error('Error detecting temporal anomalies:', error);
            return { score: 0, anomalies: ['Error in anomaly detection'] };
        }
    }
    validateTemporalConsistency(latency, historicalData) {
        try {
            const { score: anomalyScore } = this.detectTemporalAnomalies(latency, historicalData);
            const varianceScore = this.calculateVarianceScore(latency, historicalData);
            const trendScore = this.calculateTrendScore(latency, historicalData);
            const weightedScore = (anomalyScore * 0.4 +
                varianceScore * 0.3 +
                trendScore * 0.3);
            return Math.min(1, Math.max(0, weightedScore));
        }
        catch (error) {
            this.logger.error('Error validating temporal consistency:', error);
            return 0;
        }
    }
    calculateVarianceScore(latency, historicalData) {
        if (historicalData.length < 2)
            return 1;
        const mean = historicalData.reduce((sum, val) => sum + val, 0) / historicalData.length;
        const variance = historicalData.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / historicalData.length;
        const deviation = Math.abs(latency - mean);
        const stdDev = Math.sqrt(variance);
        const maxAcceptableDeviation = 3 * stdDev;
        return Math.max(0, 1 - (deviation / maxAcceptableDeviation));
    }
    calculateTrendScore(latency, historicalData) {
        if (historicalData.length < 2)
            return 1;
        const windowSize = Math.min(5, Math.floor(historicalData.length / 2));
        const recentData = historicalData.slice(-windowSize);
        const movingAvg = recentData.reduce((sum, val) => sum + val, 0) / recentData.length;
        const trendStrength = Math.abs(latency - movingAvg) / movingAvg;
        const maxAcceptableTrendStrength = 0.2;
        return Math.max(0, 1 - (trendStrength / maxAcceptableTrendStrength));
    }
    checkPerformanceAlerts() {
        this.merkleMetrics.alerts = [];
        if (this.merkleMetrics.averageGenerationTime > this.ALERT_THRESHOLDS.maxGenerationTime) {
            const severity = this.determineAlertSeverity(this.merkleMetrics.averageGenerationTime, this.ALERT_THRESHOLDS.maxGenerationTime, [1.0, 1.5, 2.0]);
            const alert = {
                message: `High average generation time: ${this.merkleMetrics.averageGenerationTime.toFixed(2)}ms`,
                severity,
                metric: 'averageGenerationTime',
                value: this.merkleMetrics.averageGenerationTime,
                threshold: this.ALERT_THRESHOLDS.maxGenerationTime,
                remediation: this.getRemediationStep('generation_time', severity)
            };
            this.merkleMetrics.alerts.push(alert);
            this.persistSecurityAlert(alert).catch((error) => {
                this.logger.error('Failed to persist alert:', error);
            });
            this.applyAutomatedRemediation('generation_time', severity);
        }
        const cacheHitRate = this.merkleMetrics.cacheHits /
            (this.merkleMetrics.cacheHits + this.merkleMetrics.cacheMisses);
        if (cacheHitRate < this.ALERT_THRESHOLDS.minCacheHitRate) {
            const severity = this.determineAlertSeverity(cacheHitRate, this.ALERT_THRESHOLDS.minCacheHitRate, [0.9, 0.7, 0.5]);
            const alert = {
                message: `Low cache hit rate: ${(cacheHitRate * 100).toFixed(2)}%`,
                severity,
                metric: 'cacheHitRate',
                value: cacheHitRate,
                threshold: this.ALERT_THRESHOLDS.minCacheHitRate,
                remediation: this.getRemediationStep('cache_hit_rate', severity)
            };
            this.merkleMetrics.alerts.push(alert);
            this.persistSecurityAlert(alert).catch((error) => {
                this.logger.error('Failed to persist alert:', error);
            });
            this.applyAutomatedRemediation('cache_hit_rate', severity);
        }
        const parallelOpsRatio = this.merkleMetrics.parallelOperations / this.merkleMetrics.totalOperations;
        if (parallelOpsRatio > this.ALERT_THRESHOLDS.maxParallelOpsRatio) {
            const severity = this.determineAlertSeverity(parallelOpsRatio, this.ALERT_THRESHOLDS.maxParallelOpsRatio, [1.1, 1.3, 1.5]);
            const alert = {
                message: `High parallel operations ratio: ${(parallelOpsRatio * 100).toFixed(2)}%`,
                severity,
                metric: 'parallelOpsRatio',
                value: parallelOpsRatio,
                threshold: this.ALERT_THRESHOLDS.maxParallelOpsRatio,
                remediation: this.getRemediationStep('parallel_ops', severity)
            };
            this.merkleMetrics.alerts.push(alert);
            this.persistSecurityAlert(alert).catch((error) => {
                this.logger.error('Failed to persist alert:', error);
            });
            this.applyAutomatedRemediation('parallel_ops', severity);
        }
        const bufferReuseRatio = this.merkleMetrics.bufferReuse / this.merkleMetrics.totalOperations;
        if (bufferReuseRatio > this.ALERT_THRESHOLDS.maxBufferReuseRatio) {
            const severity = this.determineAlertSeverity(bufferReuseRatio, this.ALERT_THRESHOLDS.maxBufferReuseRatio, [1.1, 1.3, 1.5]);
            const alert = {
                message: `High buffer reuse ratio: ${(bufferReuseRatio * 100).toFixed(2)}%`,
                severity,
                metric: 'bufferReuseRatio',
                value: bufferReuseRatio,
                threshold: this.ALERT_THRESHOLDS.maxBufferReuseRatio,
                remediation: this.getRemediationStep('buffer_reuse', severity)
            };
            this.merkleMetrics.alerts.push(alert);
            this.persistSecurityAlert(alert).catch((error) => {
                this.logger.error('Failed to persist alert:', error);
            });
            this.applyAutomatedRemediation('buffer_reuse', severity);
        }
        if (this.merkleMetrics.alerts.length > 0) {
            this.logger.warn('Merkle tree performance alerts:', {
                alerts: this.merkleMetrics.alerts.map(alert => ({
                    ...alert,
                    timestamp: Date.now()
                }))
            });
        }
    }
    determineAlertSeverity(value, threshold, [lowMult, mediumMult, highMult]) {
        const ratio = value / threshold;
        if (ratio >= highMult)
            return 'HIGH';
        if (ratio >= mediumMult)
            return 'MEDIUM';
        if (ratio >= lowMult)
            return 'LOW';
        return 'LOW';
    }
    getRemediationStep(metric, severity) {
        const remediations = {
            generation_time: {
                LOW: 'Consider increasing cache size or adjusting parallel chunk size',
                MEDIUM: 'Reduce tree height or increase parallel processing threshold',
                HIGH: 'Emergency: Switch to fallback mode with reduced tree complexity'
            },
            cache_hit_rate: {
                LOW: 'Monitor cache usage patterns and adjust size if needed',
                MEDIUM: 'Increase cache size or adjust eviction policy',
                HIGH: 'Clear cache and rebuild with optimized parameters'
            },
            parallel_ops: {
                LOW: 'Review parallel chunk size configuration',
                MEDIUM: 'Adjust parallel processing threshold',
                HIGH: 'Disable parallel processing temporarily'
            },
            buffer_reuse: {
                LOW: 'Monitor buffer allocation patterns',
                MEDIUM: 'Implement buffer pooling',
                HIGH: 'Reset buffer allocation strategy'
            }
        };
        return remediations[metric]?.[severity] || 'No specific remediation available';
    }
    async applyAutomatedRemediation(metric, severity) {
        if (severity !== 'HIGH')
            return;
        const occurrences = (this.merkleMetrics.remediationHistory.get(metric) || 0) + 1;
        this.merkleMetrics.remediationHistory.set(metric, occurrences);
        if (occurrences >= 3) {
            let remediationApplied = false;
            switch (metric) {
                case 'generation_time':
                    this.MERKLE_TREE_HEIGHT = Math.max(5, this.MERKLE_TREE_HEIGHT - 1);
                    remediationApplied = true;
                    break;
                case 'cache_hit_rate':
                    this.merkleCache.clear();
                    remediationApplied = true;
                    break;
                case 'parallel_ops':
                    this.PARALLEL_CHUNK_SIZE *= 2;
                    remediationApplied = true;
                    break;
                case 'buffer_reuse':
                    this.merkleMetrics.bufferReuse = 0;
                    remediationApplied = true;
                    break;
            }
            this.merkleMetrics.remediationHistory.delete(metric);
            const action = this.getRemediationStep(metric, severity);
            this.logger.info('Applied automated remediation:', {
                metric,
                action,
                timestamp: Date.now()
            });
            if (remediationApplied) {
                const activeAlerts = await this.alertService.getActiveAlerts();
                await this.handleRemediationAndResolution(metric, activeAlerts);
            }
        }
    }
    getMerkleMetrics() {
        this.checkPerformanceAlerts();
        const cacheHitRate = this.merkleMetrics.cacheHits /
            (this.merkleMetrics.cacheHits + this.merkleMetrics.cacheMisses);
        return {
            ...this.merkleMetrics,
            cacheHitRate
        };
    }
    async persistSecurityAlert(alert) {
        const alertData = {
            ...alert,
            type: 'SECURITY',
            timestamp: new Date(),
            status: 'ACTIVE'
        };
        await this.alertService.persistAlert(alertData).catch((error) => {
            this.logger.error('Failed to persist security alert', error);
        });
    }
    async handleRemediationAndResolution(metric, activeAlerts) {
        const latestAlert = activeAlerts.find((a) => a.metric === metric && !a.resolved);
        if (latestAlert) {
            await this.alertService.markRemediationApplied(latestAlert._id.toString());
            await this.alertService.markAlertResolved(latestAlert._id.toString());
        }
    }
}
exports.QuantumValidator = QuantumValidator;
//# sourceMappingURL=quantum_validator.js.map