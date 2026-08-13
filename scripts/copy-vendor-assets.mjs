import { copyFileSync, mkdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';

const root = resolve(import.meta.dirname, '..');
const source = resolve(root, 'node_modules/chart.js/dist/chart.umd.js');
const destination = resolve(root, 'assets/vendor/chart.umd.js');

mkdirSync(dirname(destination), { recursive: true });
copyFileSync(source, destination);
console.log(`Copied ${source} -> ${destination}`);
