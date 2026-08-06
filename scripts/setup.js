const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log('                   Plane - Project Management Tool                    ');
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log('Setting up your development environment...\n');

// 1. Copy env files
const services = ['', 'web', 'api', 'space', 'admin', 'live'];
let success = true;

services.forEach((service) => {
  const prefix = service === '' ? './' : `./apps/${service}/`;
  const src = path.resolve(prefix, '.env.example');
  const dest = path.resolve(prefix, '.env');

  if (!fs.existsSync(src)) {
    console.error(`❌ Source file ${src} does not exist.`);
    success = false;
    return;
  }

  try {
    fs.copyFileSync(src, dest);
    console.log(`✓ Copied ${dest}`);
  } catch (err) {
    console.error(`✗ Failed to copy to ${dest}: ${err.message}`);
    success = false;
  }
});

// 2. Generate Django SECRET_KEY
const apiEnvPath = path.resolve('./apps/api/.env');
if (fs.existsSync(apiEnvPath)) {
  console.log('\nGenerating Django SECRET_KEY...');
  try {
    const currentContent = fs.readFileSync(apiEnvPath, 'utf8');
    if (!currentContent.includes('SECRET_KEY=')) {
      const chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+);,./';
      let secretKey = '';
      for (let i = 0; i < 50; i++) {
        secretKey += chars.charAt(Math.floor(Math.random() * chars.length));
      }
      fs.appendFileSync(apiEnvPath, `\nSECRET_KEY="${secretKey}"\n`);
      console.log('✓ Added SECRET_KEY to apps/api/.env');
    } else {
      console.log('✓ SECRET_KEY already exists in apps/api/.env');
    }
  } catch (err) {
    console.error(`✗ Failed to write SECRET_KEY: ${err.message}`);
    success = false;
  }
} else {
  console.error('✗ apps/api/.env not found. SECRET_KEY not added.');
  success = false;
}

// 3. Install dependencies
if (success) {
  console.log('\nInstalling Node dependencies using pnpm...');
  try {
    execSync('pnpm install', { stdio: 'inherit' });
    console.log('\n✓ Environment setup completed successfully!\n');
    console.log('Next steps:');
    console.log('1. Review the .env files in each folder if needed');
    console.log('2. Start local services: pnpm run start');
    console.log('3. Seed the databases: pnpm run seed');
    console.log('\nHappy coding! 🚀');
  } catch (err) {
    console.warn('\n⚠️ Standard pnpm install failed. Retrying with --ignore-engines...');
    try {
      execSync('pnpm install --ignore-engines', { stdio: 'inherit' });
      console.log('\n✓ Environment setup completed successfully with --ignore-engines!\n');
      console.log('Next steps:');
      console.log('1. Review the .env files in each folder if needed');
      console.log('2. Start local services: pnpm run start');
      console.log('3. Seed the databases: pnpm run seed');
      console.log('\nHappy coding! 🚀');
    } catch (retryErr) {
      console.error(`\n✗ Dependency installation failed: ${retryErr.message}`);
      process.exit(1);
    }
  }
} else {
  console.error('\n✗ Setup failed. Please check errors above.');
  process.exit(1);
}
