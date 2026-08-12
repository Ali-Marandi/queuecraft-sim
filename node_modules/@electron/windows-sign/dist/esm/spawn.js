import { log } from './utils/log';
/**
 * Spawn a process as a promise
 *
 * @param {string} name
 * @param {Array<string>} args
 * @param {SpawnOptions} [options]
 * @returns {Promise<SpawnPromiseResult>}
 */
export function spawnPromise(name, args, options) {
    return new Promise((resolve) => {
        const { spawn } = require('child_process');
        const fork = spawn(name, args, options);
        log(`Spawning ${name} with ${args}`);
        let stdout = '';
        let stderr = '';
        fork.stdout.on('data', (data) => {
            log(`Spawn ${name} stdout: ${data}`);
            stdout += data;
        });
        fork.stderr.on('data', (data) => {
            log(`Spawn ${name} stderr: ${data}`);
            stderr += data;
        });
        fork.on('close', (code) => {
            log(`Spawn ${name}: Child process exited with code ${code}`);
            resolve({ stdout, stderr, code });
        });
    });
}
