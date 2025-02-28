declare module '@tensorflow/tfjs-node' {
    export interface LayersModel {
        predict(inputs: Tensor): Tensor;
        compile(config: {
            optimizer: Optimizer;
            loss: string;
            metrics?: string[];
        }): void;
        trainOnBatch(x: Tensor, y: Tensor): Promise<number[]>;
        save(path: string): Promise<void>;
        layers: Layer[];
        trainable: boolean;
        add(layer: Layer): void;
    }

    export interface Layer {
        trainable: boolean;
        apply(inputs: Tensor | SymbolicTensor): Tensor | SymbolicTensor;
        clone(): Layer;
        getWeights(): Tensor[];
    }

    export interface Tensor {
        dataSync(): Float32Array;
        dispose(): void;
        reshape(shape: number[]): Tensor;
    }

    export interface SymbolicTensor {
        shape: number[];
    }

    export interface Optimizer {
        // Optimizer interface
    }

    export const layers: {
        dense(config: {
            units: number;
            inputShape?: number[];
            activation?: string;
        }): Layer;
    };

    export const train: {
        adam(learningRate?: number): Optimizer;
    };

    export function tidy<T>(fn: () => T): T;
    export function randomNormal(shape: number[]): Tensor;
    export function concat(tensors: Tensor[]): Tensor;
    export function norm(x: Tensor): Tensor;
    export function gradients(f: () => Tensor): Tensor[];

    export const sequential: (config?: { layers: Layer[] }) => LayersModel;
    export const model: (config: { inputs: SymbolicTensor, outputs: SymbolicTensor }) => LayersModel;
    export const input: (config: { shape: number[] }) => SymbolicTensor;
    export const tensor2d: (values: number[][]) => Tensor;
    export const ones: (shape: number[]) => Tensor;
    export const zeros: (shape: number[]) => Tensor;

    export const loadLayersModel: (path: string) => Promise<LayersModel>;
} 