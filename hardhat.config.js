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
require("@nomicfoundation/hardhat-chai-matchers");
require("@nomicfoundation/hardhat-ethers");
require("@typechain/hardhat");
const dotenv = __importStar(require("dotenv"));
require("hardhat-gas-reporter");
const path_1 = require("path");
require("solidity-coverage");
// Load environment variables from .env.contracts
dotenv.config({ path: (0, path_1.resolve)(__dirname, './.env.contracts') });
// Ensure required environment variables are set
const REQUIRED_ENV_VARS = ['AMOY_RPC', 'DEPLOYER_PRIVATE_KEY', 'POLYGONSCAN_API_KEY'];
for (const envVar of REQUIRED_ENV_VARS) {
    if (!process.env[envVar]) {
        console.warn(`Warning: ${envVar} is not set in config/.env`);
    }
}
const config = {
    solidity: {
        version: '0.8.21',
        settings: {
            optimizer: {
                enabled: true,
                runs: 200,
            },
            viaIR: true,
        },
    },
    networks: {
        hardhat: {
            chainId: 80002,
        },
        amoy: {
            url: process.env.AMOY_RPC || 'https://polygon-amoy.public.blastapi.io',
            accounts: process.env.DEPLOYER_PRIVATE_KEY ? [process.env.DEPLOYER_PRIVATE_KEY] : [],
            chainId: 80002,
            gasPrice: 'auto',
        },
        sepolia: {
            url: process.env.SEPOLIA_RPC || '',
            accounts: process.env.DEPLOYER_PRIVATE_KEY ? [process.env.DEPLOYER_PRIVATE_KEY] : [],
            gasPrice: 'auto',
        },
    },
    gasReporter: {
        enabled: process.env.REPORT_GAS !== undefined,
        currency: 'USD',
    },
    paths: {
        sources: './contracts',
        tests: './test',
        cache: './cache',
        artifacts: './artifacts',
    },
    typechain: {
        outDir: 'typechain-types',
        target: 'ethers-v6',
    },
};
exports.default = config;
