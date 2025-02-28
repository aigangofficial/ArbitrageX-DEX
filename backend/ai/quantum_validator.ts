import { ethers } from 'ethers';
import { Logger } from 'winston';
import { CompetitorPattern } from './competitor_analyzer';
import * as crypto from 'crypto';
import { AlertService } from '../api/services/alertService';
import { IAlert } from '../api/models/AlertModel';

interface QuantumResistantSignature {
    r: string;
    s: string;
    recoveryParam: number;
    latticeParams: {
        dimension: number;
        basis: number[][];
        challenge: string;
    };
}

interface ValidationResult {
    isValid: boolean;
    quantumSafetyScore: number;
    threatLevel: 'LOW' | 'MEDIUM' | 'HIGH';
    recommendations: string[];
}

export interface ModelStateValidation {
    isValid: boolean;
    quantumSafetyScore: number;
    threatLevel: 'LOW' | 'MEDIUM' | 'HIGH';
    recommendations: string[];
}

interface PerformanceAlert {
    message: string;
    severity: 'LOW' | 'MEDIUM' | 'HIGH';
    metric: string;
    value: number;
    threshold: number;
    remediation: string;
}

export class QuantumValidator {
    private readonly LATTICE_DIMENSION = 512; // NIST recommended dimension
    private readonly MIN_QUANTUM_SAFETY_SCORE = 0.8;
    private MERKLE_TREE_HEIGHT = 10;  // Made mutable for dynamic adjustment
    private readonly TEMPORAL_WINDOW_SIZE = 1000; // ms
    private readonly MERKLE_CACHE_SIZE = 1000;
    private PARALLEL_CHUNK_SIZE = 64;  // Made mutable for dynamic adjustment
    
    // Performance alert thresholds
    private readonly ALERT_THRESHOLDS = {
        maxGenerationTime: 100, // ms
        minCacheHitRate: 0.7,
        maxParallelOpsRatio: 0.8,
        maxBufferReuseRatio: 0.9
    };
    
    private merkleMetrics = {
        totalOperations: 0,
        cacheHits: 0,
        cacheMisses: 0,
        averageGenerationTime: 0,
        parallelOperations: 0,
        maxTreeDepth: 0,
        bufferReuse: 0,
        alerts: [] as PerformanceAlert[],
        remediationHistory: new Map<string, number>()
    };
    
    private temporalChain: {
        hash: string;
        timestamp: number;
        merkleRoot: string;
        entropySource: string;
    }[] = [];
    
    private merkleCache: Map<string, string> = new Map();
    
    constructor(
        private readonly logger: Logger,
        private readonly config: {
            minLatticeSecurityLevel: number;
            postQuantumScheme: 'FALCON' | 'DILITHIUM' | 'SPHINCS+';
            challengeWindowMs: number;
        },
        private readonly alertService: AlertService
    ) {}

    async validateTransaction(
        tx: ethers.Transaction,
        competitor: CompetitorPattern
    ): Promise<ValidationResult> {
        try {
            // Generate quantum-resistant signature verification parameters
            const qrSignature = await this.generateQuantumSignature(Buffer.from(tx.hash || ''));
            
            // Verify lattice-based signature
            const signatureValid = await this.verifyLatticeSignature(
                tx,
                qrSignature,
                competitor
            );

            // Calculate quantum safety metrics
            const safetyMetrics = this.calculateQuantumSafetyMetrics(
                qrSignature,
                competitor
            );

            // Generate validation result
            return {
                isValid: signatureValid && safetyMetrics.score >= this.MIN_QUANTUM_SAFETY_SCORE,
                quantumSafetyScore: safetyMetrics.score,
                threatLevel: this.determineThreatLevel(safetyMetrics.score),
                recommendations: this.generateSecurityRecommendations(safetyMetrics)
            };
        } catch (error) {
            this.logger.error('Quantum validation error:', error);
            return {
                isValid: false,
                quantumSafetyScore: 0,
                threatLevel: 'HIGH',
                recommendations: ['Transaction failed quantum-safe validation']
            };
        }
    }

    async validateModelState(modelState: number[][]): Promise<ModelStateValidation> {
        try {
            // Calculate quantum safety metrics for model state
            const latticeSecurity = this.calculateModelLatticeSecurity(modelState);
            const temporalConsistency = this.calculateModelTemporalConsistency();
            const behavioralEntropy = this.calculateModelBehavioralEntropy();

            // Combine metrics into overall quantum safety score
            const quantumSafetyScore = (
                latticeSecurity * 0.4 +
                temporalConsistency * 0.3 +
                behavioralEntropy * 0.3
            );

            // Determine threat level
            const threatLevel = this.determineThreatLevel(quantumSafetyScore);

            // Generate recommendations
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
        } catch (error) {
            this.logger.error('Model state validation failed:', error);
            return {
                isValid: false,
                quantumSafetyScore: 0,
                threatLevel: 'HIGH',
                recommendations: ['Model state validation failed']
            };
        }
    }

    async signModelState(modelState: number[][]): Promise<string> {
        try {
            // Generate lattice basis for model state
            const basis = this.generateLatticeBasis(this.LATTICE_DIMENSION);
            
            // Create quantum-resistant challenge from model state
            const modelChallenge = this.generateModelChallenge(modelState);
            
            // Generate quantum-resistant signature
            const signature = await this.generateQuantumSignature(Buffer.from(modelChallenge));

            return signature.r + signature.s;
        } catch (error) {
            this.logger.error('Model state signing failed:', error);
            throw error;
        }
    }

    public async generateQuantumSignature(data: Buffer): Promise<QuantumResistantSignature> {
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

    public async createCommitment(data: Buffer): Promise<string> {
        const commitment = this.generateHash(data);
        const signature = await this.generateQuantumSignature(data);
        
        return JSON.stringify({
            commitment,
            signature,
            timestamp: Date.now()
        });
    }

    public async getLatticeParams(signature: QuantumResistantSignature): Promise<{
        dimension: number;
        basis: number[][];
        challenge: string;
    }> {
        return signature.latticeParams;
    }

    public async calculateLatticeSecurity(params: {
        dimension: number;
        basis: number[][];
        challenge: string;
    }): Promise<number> {
        try {
            // Validate lattice parameters against NIST standards
            if (params.dimension < this.LATTICE_DIMENSION) {
                this.logger.warn(`Lattice dimension ${params.dimension} below NIST recommended minimum ${this.LATTICE_DIMENSION}`);
                return 0;
            }

            // Calculate security score based on basis orthogonality
            const orthogonalityScore = this.calculateOrthogonalityScore(params.basis);
            
            // Weight the scores (70% orthogonality, 30% dimension)
            const dimensionScore = params.dimension / this.LATTICE_DIMENSION;
            const weightedScore = (0.7 * orthogonalityScore) + (0.3 * dimensionScore);

            return Math.min(1, Math.max(0, weightedScore));
        } catch (error) {
            this.logger.error('Error calculating lattice security:', error);
            return 0;
        }
    }

    private calculateOrthogonalityScore(basis: number[][]): number {
        // Calculate Gram-Schmidt orthogonalization score
        // This is a simplified implementation - production would use a more robust algorithm
        try {
            let orthogonalitySum = 0;
            for (let i = 0; i < basis.length; i++) {
                for (let j = i + 1; j < basis.length; j++) {
                    const dotProduct = basis[i].reduce((sum, val, idx) => sum + val * basis[j][idx], 0);
                    orthogonalitySum += Math.abs(dotProduct);
                }
            }
            
            // Normalize the score between 0 and 1
            const maxPossibleSum = basis.length * (basis.length - 1) / 2 * basis[0].length;
            return 1 - (orthogonalitySum / maxPossibleSum);
        } catch (error) {
            this.logger.error('Error calculating orthogonality score:', error);
            return 0;
        }
    }

    public generateHash(data: Buffer): string {
        // Use quantum-resistant hash function (e.g., SPHINCS+)
        const hash = crypto.createHash('sha3-256');
        hash.update(data);
        return hash.digest('hex');
    }

    public async aggregateSignatures(proofs: Buffer[]): Promise<string> {
        const aggregatedHash = this.generateHash(Buffer.concat(proofs));
        const signature = await this.generateQuantumSignature(Buffer.from(aggregatedHash));
        
        return JSON.stringify({
            hash: aggregatedHash,
            signature,
            timestamp: Date.now()
        });
    }

    private async verifyLatticeSignature(
        tx: ethers.Transaction,
        signature: QuantumResistantSignature,
        competitor: CompetitorPattern
    ): Promise<boolean> {
        try {
            // Verify lattice parameters
            const latticeParams = await this.getLatticeParams(signature);
            const securityScore = await this.calculateLatticeSecurity(latticeParams);
            
            if (securityScore < this.MIN_QUANTUM_SAFETY_SCORE) {
                this.logger.warn('Lattice security score below threshold:', securityScore);
                return false;
            }

            // Verify signature using post-quantum scheme
            const isValid = await this.verifySignature(
                tx,
                signature,
                competitor
            );

            return isValid;
        } catch (error) {
            this.logger.error('Error verifying lattice signature:', error);
            return false;
        }
    }

    private async verifySignature(
        tx: ethers.Transaction,
        signature: QuantumResistantSignature,
        competitor: CompetitorPattern
    ): Promise<boolean> {
        try {
            // Reconstruct challenge
            const challenge = this.generateChallenge(Buffer.from(tx.hash || ''));
            
            // Verify signature matches challenge
            const signatureValid = signature.r === challenge;
            
            if (!signatureValid) {
                this.logger.warn('Invalid signature challenge match');
                return false;
            }
            
            // Verify temporal consistency
            const temporalValid = await this.verifyTemporalConsistency(
                signature,
                competitor
            );
            
            if (!temporalValid) {
                this.logger.warn('Invalid temporal consistency');
                return false;
            }
            
            return true;
        } catch (error) {
            this.logger.error('Error verifying signature:', error);
            return false;
        }
    }

    private async verifyTemporalConsistency(
        signature: QuantumResistantSignature,
        competitor: CompetitorPattern
    ): Promise<boolean> {
        try {
            // Check if signature is within acceptable time window
            const timeSinceLastSeen = Date.now() - competitor.lastSeen;
            const isWithinWindow = timeSinceLastSeen <= this.config.challengeWindowMs;
            
            if (!isWithinWindow) {
                this.logger.warn('Signature outside acceptable time window');
                return false;
            }
            
            return true;
        } catch (error) {
            this.logger.error('Error verifying temporal consistency:', error);
            return false;
        }
    }

    private calculateQuantumSafetyMetrics(
        signature: QuantumResistantSignature,
        competitor: CompetitorPattern
    ): { score: number; metrics: any } {
        try {
            // Calculate lattice security score
            const latticeScore = this.calculateOrthogonalityScore(signature.latticeParams.basis);
            
            // Calculate temporal consistency score
            const temporalScore = this.calculateTemporalConsistency(competitor);
            
            // Calculate behavioral entropy score
            const entropyScore = this.calculateBehavioralEntropy();
            
            // Combine scores with weights
            const score = (
                latticeScore * 0.4 +
                temporalScore * 0.3 +
                entropyScore * 0.3
            );
            
            return {
                score,
                metrics: {
                    latticeScore,
                    temporalScore,
                    entropyScore
                }
            };
        } catch (error) {
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

    private calculateTemporalConsistency(competitor: CompetitorPattern): number {
        try {
            // Calculate temporal consistency based on competitor pattern
            // This is a simplified implementation
            const patternScore = competitor.patternStrength || 0.5;
            const timeScore = competitor.timeConsistency || 0.5;
            return (patternScore + timeScore) / 2;
        } catch (error) {
            this.logger.error('Error calculating temporal consistency:', error);
            return 0;
        }
    }

    private generateLatticeBasis(dimension: number): number[][] {
        // Generate a random lattice basis with the given dimension
        // This is a simplified implementation - production would use a more secure method
        const basis: number[][] = [];
        for (let i = 0; i < dimension; i++) {
            const row: number[] = [];
            for (let j = 0; j < dimension; j++) {
                // Generate random integers between -10 and 10 for the basis vectors
                row.push(Math.floor(Math.random() * 21) - 10);
            }
            basis.push(row);
        }
        return basis;
    }

    private generateChallenge(data: Buffer): string {
        // Generate a challenge string from the input data
        // This is a simplified implementation - production would use a more secure method
        const challengeInput = Buffer.concat([
            data,
            Buffer.from(Date.now().toString())
        ]);
        
        return crypto.createHash('sha3-512')
            .update(challengeInput)
            .digest('hex');
    }

    private verifyLatticeParameters(
        params: QuantumResistantSignature['latticeParams'],
        minSecurityLevel: number
    ): boolean {
        // Verify lattice parameters meet minimum security requirements
        const determinant = this.calculateLatticeDeterminant(params.basis);
        const securityLevel = Math.log2(determinant);
        return securityLevel >= minSecurityLevel;
    }

    private calculateLatticeDeterminant(basis: number[][]): number {
        // Calculate approximate lattice determinant using LLL algorithm
        // This is a simplified version for demonstration
        let det = 1;
        for (let i = 0; i < basis.length; i++) {
            det *= basis[i][i];
        }
        return Math.abs(det);
    }

    private calculateBehavioralEntropy(): number {
        // Calculate behavioral entropy score
        // This is a simplified implementation - actual calculation would depend on the model's behavior
        return 0.90; // Placeholder value
    }

    private determineThreatLevel(score: number): ValidationResult['threatLevel'] {
        if (score >= 0.8) return 'LOW';
        if (score >= 0.5) return 'MEDIUM';
        return 'HIGH';
    }

    private generateSecurityRecommendations(metrics: { 
        score: number; 
        metrics: Record<string, number>; 
    }): string[] {
        const recommendations: string[] = [];

        if (metrics.metrics.latticeScore < 0.8) {
            recommendations.push(
                'Increase lattice dimension for stronger quantum resistance'
            );
        }

        if (metrics.metrics.temporalScore < 0.7) {
            recommendations.push(
                'Suspicious temporal pattern detected - consider additional verification'
            );
        }

        if (metrics.metrics.entropyScore < 0.6) {
            recommendations.push(
                'Unusual behavior pattern - implement additional monitoring'
            );
        }

        if (recommendations.length === 0) {
            recommendations.push('No security recommendations at this time');
        }

        return recommendations;
    }

    private generateModelChallenge(modelState: number[][]): string {
        // Generate challenge from model state
        const stateBuffer = Buffer.from(
            modelState.map(row => row.join(',')).join(';')
        );
        
        return this.generateHash(stateBuffer);
    }

    private calculateModelLatticeSecurity(modelState: number[][]): number {
        try {
            const basis = this.generateLatticeBasis(this.LATTICE_DIMENSION);
            return this.calculateOrthogonalityScore(basis);
        } catch (error) {
            this.logger.error('Error calculating model lattice security:', error);
            return 0;
        }
    }

    private calculateModelTemporalConsistency(): number {
        try {
            // Simplified temporal consistency check
            // In production, this would analyze historical model states
            return 0.95;
        } catch (error) {
            this.logger.error('Error calculating model temporal consistency:', error);
            return 0;
        }
    }

    private calculateModelBehavioralEntropy(): number {
        try {
            // Simplified behavioral entropy calculation
            // In production, this would analyze model behavior patterns
            return 0.90;
        } catch (error) {
            this.logger.error('Error calculating model behavioral entropy:', error);
            return 0;
        }
    }

    private async signChallenge(challenge: string, latticeParams: number[][]): Promise<string> {
        // Implement quantum-resistant signature using chosen scheme
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

    private async signWithFalcon(challenge: string, latticeParams: number[][]): Promise<string> {
        // Implement FALCON signature
        // This is a placeholder - actual implementation would use FALCON library
        return crypto.createHmac('sha256', Buffer.from(latticeParams.toString()))
            .update(challenge)
            .digest('hex');
    }

    private async signWithDilithium(challenge: string, latticeParams: number[][]): Promise<string> {
        // Implement DILITHIUM signature
        // This is a placeholder - actual implementation would use DILITHIUM library
        return crypto.createHmac('sha384', Buffer.from(latticeParams.toString()))
            .update(challenge)
            .digest('hex');
    }

    private async signWithSphincsPLus(challenge: string, latticeParams: number[][]): Promise<string> {
        // Implement SPHINCS+ signature
        // This is a placeholder - actual implementation would use SPHINCS+ library
        return crypto.createHmac('sha512', Buffer.from(latticeParams.toString()))
            .update(challenge)
            .digest('hex');
    }

    private async validateLatencyWithQuantumProof(
        latency: number,
        historicalData: number[],
        networkLoad: number
    ): Promise<{
        isValid: boolean;
        temporalHash: string;
        latticeSignature: string;
        networkLoadProof: string;
        aggregatedProof: string;
    }> {
        try {
            // Generate temporal hash chain
            const temporalHash = await this.generateTemporalHash(latency, historicalData);

            // Create lattice-based signature
            const latticeSignature = await this.generateLatticeSignature(latency, temporalHash);

            // Calculate temporal consistency
            const consistencyScore = await this.validateTemporalConsistency(latency, historicalData);
            if (consistencyScore < this.MIN_QUANTUM_SAFETY_SCORE) {
                throw new Error('Temporal consistency check failed');
            }

            // Generate network load proof
            const networkLoadProof = await this.generateNetworkLoadProof(networkLoad);

            // Aggregate all proofs into quantum-resistant signature
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
        } catch (error) {
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

    private async generateLatticeSignature(latency: number, temporalHash: string): Promise<string> {
        try {
            // Generate lattice basis for signature
            const basis = this.generateLatticeBasis(this.LATTICE_DIMENSION);
            
            // Create signature input
            const signatureInput = Buffer.concat([
                Buffer.from(latency.toString()),
                Buffer.from(temporalHash)
            ]);
            
            // Generate quantum-resistant signature
            const signature = await this.generateQuantumSignature(signatureInput);
            return signature.r + signature.s;
        } catch (error) {
            this.logger.error('Error generating lattice signature:', error);
            throw error;
        }
    }

    private async generateNetworkLoadProof(networkLoad: number): Promise<string> {
        try {
            // Create commitment to network load
            const loadBuffer = Buffer.from(networkLoad.toString());
            const timestamp = Date.now().toString();
            
            // Generate quantum-resistant commitment
            const commitment = await this.generateQuantumSignature(Buffer.from(timestamp));
            return commitment.r;
        } catch (error) {
            this.logger.error('Error generating network load proof:', error);
            throw error;
        }
    }

    private async aggregateQuantumProofs(proofs: string[]): Promise<string> {
        try {
            // Combine all proofs
            const combinedProofs = proofs.join('|');
            
            // Generate quantum-resistant aggregate signature
            const signature = await this.generateQuantumSignature(Buffer.from(combinedProofs));
            return signature.r;
        } catch (error) {
            this.logger.error('Error aggregating quantum proofs:', error);
            throw error;
        }
    }

    private async generateTemporalHash(latency: number, historicalData: number[]): Promise<string> {
        try {
            // Generate quantum entropy source
            const quantumEntropy = await this.generateQuantumEntropy();
            
            // Create temporal chain input with forward secrecy
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
            
            // Generate quantum-resistant hash
            const newHash = this.generateHash(chainInput);
            
            // Create Merkle tree from recent temporal chain entries
            const recentEntries = this.temporalChain
                .slice(-this.MERKLE_TREE_HEIGHT)
                .map(entry => entry.hash);
            recentEntries.push(newHash);
            
            const merkleRoot = this.generateMerkleRoot(recentEntries);
            
            // Add new entry to temporal chain with pruning
            this.temporalChain.push({
                hash: newHash,
                timestamp: Date.now(),
                merkleRoot,
                entropySource: quantumEntropy
            });
            
            // Prune old entries beyond window size
            const oldestValidTime = Date.now() - this.TEMPORAL_WINDOW_SIZE;
            this.temporalChain = this.temporalChain.filter(
                entry => entry.timestamp >= oldestValidTime
            );
            
            return newHash;
        } catch (error) {
            this.logger.error('Error generating temporal hash:', error);
            throw error;
        }
    }

    private async generateQuantumEntropy(): Promise<string> {
        try {
            // Combine multiple entropy sources for quantum resistance
            const timestamp = Date.now().toString();
            const randomBytes = crypto.randomBytes(32).toString('hex');
            const performanceNow = process.hrtime.bigint().toString();
            
            // Mix entropy sources with quantum-resistant hash
            const entropyInput = Buffer.concat([
                Buffer.from(timestamp),
                Buffer.from(randomBytes),
                Buffer.from(performanceNow)
            ]);
            
            return this.generateHash(entropyInput);
        } catch (error) {
            this.logger.error('Error generating quantum entropy:', error);
            throw error;
        }
    }

    private generateMerkleRoot(hashes: string[]): string {
        const startTime = performance.now();
        this.merkleMetrics.totalOperations++;
        
        if (hashes.length === 0) return '0'.repeat(64);
        if (hashes.length === 1) return hashes[0];
        
        // Track max tree depth
        this.merkleMetrics.maxTreeDepth = Math.max(
            this.merkleMetrics.maxTreeDepth,
            Math.ceil(Math.log2(hashes.length))
        );
        
        // Check cache first
        const cacheKey = hashes.join('');
        const cachedRoot = this.merkleCache.get(cacheKey);
        if (cachedRoot !== undefined) {
            this.merkleMetrics.cacheHits++;
            return cachedRoot;
        }
        this.merkleMetrics.cacheMisses++;
        
        // Process chunks in parallel for large trees
        if (hashes.length >= this.PARALLEL_CHUNK_SIZE) {
            this.merkleMetrics.parallelOperations++;
            const result = this.generateMerkleRootParallel(hashes);
            
            // Update average generation time
            const endTime = performance.now();
            this.merkleMetrics.averageGenerationTime = 
                (this.merkleMetrics.averageGenerationTime * (this.merkleMetrics.totalOperations - 1) + 
                (endTime - startTime)) / this.merkleMetrics.totalOperations;
                
            return result;
        }
        
        const nextLevel: string[] = [];
        
        // Generate parent nodes with optimized buffer allocation
        const combinedBuffer = Buffer.alloc(64); // Pre-allocate buffer for efficiency
        this.merkleMetrics.bufferReuse++;
        
        for (let i = 0; i < hashes.length - 1; i += 2) {
            const left = hashes[i];
            const right = i + 1 < hashes.length ? hashes[i + 1] : left;
            
            // Reuse buffer for combining hashes
            Buffer.from(left, 'hex').copy(combinedBuffer, 0);
            Buffer.from(right, 'hex').copy(combinedBuffer, 32);
            
            nextLevel.push(this.generateHash(combinedBuffer));
        }
        
        // Cache result before returning
        const root = this.generateMerkleRoot(nextLevel);
        if (this.merkleCache.size >= this.MERKLE_CACHE_SIZE) {
            // Remove oldest entry if cache is full
            const firstKeyIterator = this.merkleCache.keys().next();
            if (!firstKeyIterator.done && firstKeyIterator.value) {
                this.merkleCache.delete(firstKeyIterator.value);
            }
        }
        this.merkleCache.set(cacheKey, root);
        
        // Update average generation time
        const endTime = performance.now();
        this.merkleMetrics.averageGenerationTime = 
            (this.merkleMetrics.averageGenerationTime * (this.merkleMetrics.totalOperations - 1) + 
            (endTime - startTime)) / this.merkleMetrics.totalOperations;
        
        return root;
    }
    
    private generateMerkleRootParallel(hashes: string[]): string {
        // Split hashes into chunks for parallel processing
        const chunkSize = this.PARALLEL_CHUNK_SIZE;
        const chunks: string[][] = [];
        
        for (let i = 0; i < hashes.length; i += chunkSize) {
            chunks.push(hashes.slice(i, i + chunkSize));
        }
        
        // Process chunks
        const chunkRoots = chunks.map(chunk => {
            const nextLevel: string[] = [];
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
        
        // Combine chunk roots
        return chunkRoots.length === 1 ? chunkRoots[0] : this.generateMerkleRoot(chunkRoots);
    }
    
    private async validateTemporalChain(): Promise<boolean> {
        try {
            if (this.temporalChain.length < 2) return true;
            
            // Verify hash chain integrity with parallel validation
            const validations = this.temporalChain.slice(1).map(async (current, index) => {
                const previous = this.temporalChain[index];
                
                // Verify temporal sequence
                if (current.timestamp <= previous.timestamp) {
                    this.logger.warn('Invalid temporal sequence detected');
                    return false;
                }
                
                // Verify hash chain linkage
                const expectedHash = await this.generateTemporalHashForValidation(
                    current.timestamp,
                    previous.hash,
                    current.entropySource
                );
                
                if (expectedHash !== current.hash) {
                    this.logger.warn('Invalid hash chain linkage detected');
                    return false;
                }
                
                // Verify Merkle root with caching
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
            
            // Wait for all validations to complete
            const results = await Promise.all(validations);
            return results.every(result => result);
            
        } catch (error) {
            this.logger.error('Error validating temporal chain:', error);
            return false;
        }
    }

    private async generateTemporalHashForValidation(
        timestamp: number,
        previousHash: string,
        entropy: string
    ): Promise<string> {
        const validationInput = Buffer.concat([
            Buffer.from(timestamp.toString()),
            Buffer.from(previousHash),
            Buffer.from(entropy)
        ]);
        
        return this.generateHash(validationInput);
    }

    private detectTemporalAnomalies(
        latency: number,
        historicalData: number[]
    ): { score: number; anomalies: string[] } {
        try {
            if (historicalData.length < 2) {
                return { score: 1, anomalies: [] };
            }

            const mean = historicalData.reduce((sum, val) => sum + val, 0) / historicalData.length;
            const stdDev = Math.sqrt(
                historicalData.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / historicalData.length
            );

            // Calculate z-score for current latency
            const zScore = Math.abs((latency - mean) / stdDev);

            // Detect anomalies
            const anomalies: string[] = [];
            if (zScore > 3) {
                anomalies.push('Critical temporal anomaly detected');
            } else if (zScore > 2) {
                anomalies.push('Significant temporal deviation observed');
            }

            // Calculate anomaly score (inverse of normalized z-score)
            const score = Math.max(0, 1 - (zScore / 6)); // Normalize to 0-1 range

            return { score, anomalies };
        } catch (error) {
            this.logger.error('Error detecting temporal anomalies:', error);
            return { score: 0, anomalies: ['Error in anomaly detection'] };
        }
    }

    private validateTemporalConsistency(
        latency: number,
        historicalData: number[]
    ): number {
        try {
            // Calculate temporal consistency score based on:
            // 1. Variance score from historical data
            // 2. Anomaly detection score
            // 3. Trend analysis score

            // Get anomaly detection score
            const { score: anomalyScore } = this.detectTemporalAnomalies(latency, historicalData);

            // Calculate variance score
            const varianceScore = this.calculateVarianceScore(latency, historicalData);

            // Calculate trend score
            const trendScore = this.calculateTrendScore(latency, historicalData);

            // Combine scores with weights
            const weightedScore = (
                anomalyScore * 0.4 +
                varianceScore * 0.3 +
                trendScore * 0.3
            );

            return Math.min(1, Math.max(0, weightedScore));
        } catch (error) {
            this.logger.error('Error validating temporal consistency:', error);
            return 0;
        }
    }

    private calculateVarianceScore(latency: number, historicalData: number[]): number {
        if (historicalData.length < 2) return 1;

        // Calculate variance of historical data
        const mean = historicalData.reduce((sum, val) => sum + val, 0) / historicalData.length;
        const variance = historicalData.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / historicalData.length;

        // Calculate how well current latency fits within historical variance
        const deviation = Math.abs(latency - mean);
        const stdDev = Math.sqrt(variance);

        // Convert to a 0-1 score (lower deviation = higher score)
        const maxAcceptableDeviation = 3 * stdDev; // 3 sigma rule
        return Math.max(0, 1 - (deviation / maxAcceptableDeviation));
    }

    private calculateTrendScore(latency: number, historicalData: number[]): number {
        if (historicalData.length < 2) return 1;

        // Calculate moving average
        const windowSize = Math.min(5, Math.floor(historicalData.length / 2));
        const recentData = historicalData.slice(-windowSize);
        const movingAvg = recentData.reduce((sum, val) => sum + val, 0) / recentData.length;

        // Calculate trend direction and strength
        const trendStrength = Math.abs(latency - movingAvg) / movingAvg;

        // Convert to a 0-1 score (lower trend strength = higher score)
        const maxAcceptableTrendStrength = 0.2; // 20% deviation from moving average
        return Math.max(0, 1 - (trendStrength / maxAcceptableTrendStrength));
    }

    private checkPerformanceAlerts(): void {
        this.merkleMetrics.alerts = [];
        
        // Check generation time
        if (this.merkleMetrics.averageGenerationTime > this.ALERT_THRESHOLDS.maxGenerationTime) {
            const severity = this.determineAlertSeverity(
                this.merkleMetrics.averageGenerationTime,
                this.ALERT_THRESHOLDS.maxGenerationTime,
                [1.0, 1.5, 2.0]
            );
            
            const alert = {
                message: `High average generation time: ${this.merkleMetrics.averageGenerationTime.toFixed(2)}ms`,
                severity,
                metric: 'averageGenerationTime',
                value: this.merkleMetrics.averageGenerationTime,
                threshold: this.ALERT_THRESHOLDS.maxGenerationTime,
                remediation: this.getRemediationStep('generation_time', severity)
            };
            
            this.merkleMetrics.alerts.push(alert);
            this.alertService.persistAlert(alert).catch((error: Error) => {
                this.logger.error('Failed to persist alert:', error);
            });
            
            this.applyAutomatedRemediation('generation_time', severity);
        }

        // Check cache hit rate
        const cacheHitRate = this.merkleMetrics.cacheHits / 
            (this.merkleMetrics.cacheHits + this.merkleMetrics.cacheMisses);
        if (cacheHitRate < this.ALERT_THRESHOLDS.minCacheHitRate) {
            const severity = this.determineAlertSeverity(
                cacheHitRate,
                this.ALERT_THRESHOLDS.minCacheHitRate,
                [0.9, 0.7, 0.5]
            );
            
            const alert = {
                message: `Low cache hit rate: ${(cacheHitRate * 100).toFixed(2)}%`,
                severity,
                metric: 'cacheHitRate',
                value: cacheHitRate,
                threshold: this.ALERT_THRESHOLDS.minCacheHitRate,
                remediation: this.getRemediationStep('cache_hit_rate', severity)
            };
            
            this.merkleMetrics.alerts.push(alert);
            this.alertService.persistAlert(alert).catch((error: Error) => {
                this.logger.error('Failed to persist alert:', error);
            });
            
            this.applyAutomatedRemediation('cache_hit_rate', severity);
        }

        // Check parallel operations ratio
        const parallelOpsRatio = this.merkleMetrics.parallelOperations / this.merkleMetrics.totalOperations;
        if (parallelOpsRatio > this.ALERT_THRESHOLDS.maxParallelOpsRatio) {
            const severity = this.determineAlertSeverity(
                parallelOpsRatio,
                this.ALERT_THRESHOLDS.maxParallelOpsRatio,
                [1.1, 1.3, 1.5]
            );
            
            const alert = {
                message: `High parallel operations ratio: ${(parallelOpsRatio * 100).toFixed(2)}%`,
                severity,
                metric: 'parallelOpsRatio',
                value: parallelOpsRatio,
                threshold: this.ALERT_THRESHOLDS.maxParallelOpsRatio,
                remediation: this.getRemediationStep('parallel_ops', severity)
            };
            
            this.merkleMetrics.alerts.push(alert);
            this.alertService.persistAlert(alert).catch((error: Error) => {
                this.logger.error('Failed to persist alert:', error);
            });
            
            this.applyAutomatedRemediation('parallel_ops', severity);
        }

        // Check buffer reuse ratio
        const bufferReuseRatio = this.merkleMetrics.bufferReuse / this.merkleMetrics.totalOperations;
        if (bufferReuseRatio > this.ALERT_THRESHOLDS.maxBufferReuseRatio) {
            const severity = this.determineAlertSeverity(
                bufferReuseRatio,
                this.ALERT_THRESHOLDS.maxBufferReuseRatio,
                [1.1, 1.3, 1.5]
            );
            
            const alert = {
                message: `High buffer reuse ratio: ${(bufferReuseRatio * 100).toFixed(2)}%`,
                severity,
                metric: 'bufferReuseRatio',
                value: bufferReuseRatio,
                threshold: this.ALERT_THRESHOLDS.maxBufferReuseRatio,
                remediation: this.getRemediationStep('buffer_reuse', severity)
            };
            
            this.merkleMetrics.alerts.push(alert);
            this.alertService.persistAlert(alert).catch((error: Error) => {
                this.logger.error('Failed to persist alert:', error);
            });
            
            this.applyAutomatedRemediation('buffer_reuse', severity);
        }

        // Log alerts if any
        if (this.merkleMetrics.alerts.length > 0) {
            this.logger.warn('Merkle tree performance alerts:', {
                alerts: this.merkleMetrics.alerts.map(alert => ({
                    ...alert,
                    timestamp: Date.now()
                }))
            });
        }
    }

    private determineAlertSeverity(
        value: number,
        threshold: number,
        [lowMult, mediumMult, highMult]: number[]
    ): 'LOW' | 'MEDIUM' | 'HIGH' {
        const ratio = value / threshold;
        if (ratio >= highMult) return 'HIGH';
        if (ratio >= mediumMult) return 'MEDIUM';
        if (ratio >= lowMult) return 'LOW';
        return 'LOW';
    }

    private getRemediationStep(metric: string, severity: 'LOW' | 'MEDIUM' | 'HIGH'): string {
        const remediations: Record<string, Record<string, string>> = {
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

    private async applyAutomatedRemediation(metric: string, severity: 'LOW' | 'MEDIUM' | 'HIGH'): Promise<void> {
        // Only apply automated remediation for HIGH severity after multiple occurrences
        if (severity !== 'HIGH') return;

        const occurrences = (this.merkleMetrics.remediationHistory.get(metric) || 0) + 1;
        this.merkleMetrics.remediationHistory.set(metric, occurrences);

        // Apply remediation after 3 consecutive HIGH severity alerts
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
                    // Reset buffer reuse counter
                    this.merkleMetrics.bufferReuse = 0;
                    remediationApplied = true;
                    break;
            }
            
            // Reset counter after applying remediation
            this.merkleMetrics.remediationHistory.delete(metric);
            
            // Log remediation action
            const action = this.getRemediationStep(metric, severity);
            this.logger.info('Applied automated remediation:', {
                metric,
                action,
                timestamp: Date.now()
            });

            // Update alert status in database
            if (remediationApplied) {
                const activeAlerts = await this.alertService.getActiveAlerts();
                const latestAlert = activeAlerts.find((a: IAlert) => a.metric === metric && !a.resolved);
                if (latestAlert) {
                    await this.alertService.markRemediationApplied(latestAlert._id);
                    await this.alertService.markAlertResolved(latestAlert._id);
                }
            }
        }
    }

    public getMerkleMetrics(): {
        totalOperations: number;
        cacheHits: number;
        cacheMisses: number;
        averageGenerationTime: number;
        parallelOperations: number;
        maxTreeDepth: number;
        bufferReuse: number;
        cacheHitRate: number;
        alerts: PerformanceAlert[];
    } {
        this.checkPerformanceAlerts();
        const cacheHitRate = this.merkleMetrics.cacheHits / 
            (this.merkleMetrics.cacheHits + this.merkleMetrics.cacheMisses);
        
        return {
            ...this.merkleMetrics,
            cacheHitRate
        };
    }
} 