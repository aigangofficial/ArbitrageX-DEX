import { HardhatRuntimeEnvironment } from 'hardhat/types';
import fs from 'fs';
import path from 'path';
import crypto from 'crypto';

interface ContractHash {
  path: string;
  hash: string;
  lastCompiled: number;
}

interface CompilationCache {
  contracts: ContractHash[];
  lastCompilation: number;
}

async function getFileHash(filePath: string): Promise<string> {
  const content = await fs.promises.readFile(filePath);
  return crypto.createHash('md5').update(content).digest('hex');
}

async function needsRecompilation(contractsDir: string, cacheFile: string): Promise<boolean> {
  // If no cache exists, we need to compile
  if (!fs.existsSync(cacheFile)) {
    return true;
  }

  try {
    const cache: CompilationCache = JSON.parse(await fs.promises.readFile(cacheFile, 'utf8'));
    const files = await fs.promises.readdir(contractsDir);

    for (const file of files) {
      if (!file.endsWith('.sol')) continue;

      const filePath = path.join(contractsDir, file);
      const stats = await fs.promises.stat(filePath);
      const currentHash = await getFileHash(filePath);

      const cached = cache.contracts.find(c => c.path === filePath);
      if (!cached || cached.hash !== currentHash || cached.lastCompiled < stats.mtimeMs) {
        return true;
      }
    }

    return false;
  } catch (error) {
    console.error('Error checking compilation cache:', error);
    return true;
  }
}

async function updateCache(contractsDir: string, cacheFile: string): Promise<void> {
  const cache: CompilationCache = {
    contracts: [],
    lastCompilation: Date.now(),
  };

  const files = await fs.promises.readdir(contractsDir);
  for (const file of files) {
    if (!file.endsWith('.sol')) continue;

    const filePath = path.join(contractsDir, file);
    const hash = await getFileHash(filePath);

    cache.contracts.push({
      path: filePath,
      hash,
      lastCompiled: Date.now(),
    });
  }

  await fs.promises.writeFile(cacheFile, JSON.stringify(cache, null, 2));
}

export async function smartCompile(hre: HardhatRuntimeEnvironment) {
  const contractsDir = path.join(hre.config.paths.root, 'contracts');
  const cacheFile = path.join(hre.config.paths.cache, 'compilation-cache.json');

  if (await needsRecompilation(contractsDir, cacheFile)) {
    console.log('🔄 Changes detected in contracts. Recompiling...');

    // Clean artifacts and cache
    await hre.run('clean');

    // Compile contracts
    await hre.run('compile');

    // Update cache
    await updateCache(contractsDir, cacheFile);

    console.log('✅ Compilation completed successfully.');
  } else {
    console.log('✅ No changes detected. Using existing artifacts.');
  }
}

// Allow command line usage
if (require.main === module) {
  const hre = require('hardhat');
  smartCompile(hre)
    .then(() => process.exit(0))
    .catch(error => {
      console.error('Error during compilation:', error);
      process.exit(1);
    });
}
