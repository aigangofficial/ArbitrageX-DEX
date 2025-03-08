const { resolvePluginNameToPath } = require('hardhat/plugins');
const path = require('path');

function resolver(name, containingFile) {
  // Handle all external dependencies from node_modules
  if (name.startsWith('@')) {
    return path.resolve(__dirname, '..', 'node_modules', name);
  }

  // For relative imports, maintain normal resolution
  if (name.startsWith('.')) {
    return path.resolve(path.dirname(containingFile), name);
  }

  // For absolute imports from node_modules
  return resolvePluginNameToPath(name);
}

module.exports = resolver;
