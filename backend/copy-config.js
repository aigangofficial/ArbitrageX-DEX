const fs = require('fs');
const path = require('path');

// Create the dist/config directory if it doesn't exist
const configDir = path.join(__dirname, 'dist', 'config');
if (!fs.existsSync(configDir)) {
  fs.mkdirSync(configDir, { recursive: true });
}

// Copy all JSON files from config to dist/config
const sourceDir = path.join(__dirname, 'config');
fs.readdirSync(sourceDir).forEach(file => {
  if (file.endsWith('.json')) {
    const sourcePath = path.join(sourceDir, file);
    const destPath = path.join(configDir, file);
    fs.copyFileSync(sourcePath, destPath);
    console.log(`Copied ${sourcePath} to ${destPath}`);
  }
});

// Copy ABI files if they exist
const abiSourceDir = path.join(sourceDir, 'abis');
if (fs.existsSync(abiSourceDir)) {
  const abiDestDir = path.join(configDir, 'abis');
  if (!fs.existsSync(abiDestDir)) {
    fs.mkdirSync(abiDestDir, { recursive: true });
  }
  
  fs.readdirSync(abiSourceDir).forEach(file => {
    if (file.endsWith('.json')) {
      const sourcePath = path.join(abiSourceDir, file);
      const destPath = path.join(abiDestDir, file);
      fs.copyFileSync(sourcePath, destPath);
      console.log(`Copied ${sourcePath} to ${destPath}`);
    }
  });
}

console.log('Config files copied successfully!'); 