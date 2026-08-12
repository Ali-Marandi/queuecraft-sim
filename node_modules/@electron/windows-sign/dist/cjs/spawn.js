"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.spawnPromise = void 0;
const log_1 = require("./utils/log");
/**
 * Spawn a process as a promise
 *
 * @param {string} name
 * @param {Array<string>} args
 * @param {SpawnOptions} [options]
 * @returns {Promise<SpawnPromiseResult>}
 */
function spawnPromise(name, args, options) {
    return new Promise((resolve) => {
        const { spawn } = require('child_process');
        const fork = spawn(name, args, options);
        (0, log_1.log)(`Spawning ${name} with ${args}`);
        let stdout = '';
        let stderr = '';
        fork.stdout.on('data', (data) => {
            (0, log_1.log)(`Spawn ${name} stdout: ${data}`);
            stdout += data;
        });
        fork.stderr.on('data', (data) => {
            (0, log_1.log)(`Spawn ${name} stderr: ${data}`);
            stderr += data;
        });
        fork.on('close', (code) => {
            (0, log_1.log)(`Spawn ${name}: Child process exited with code ${code}`);
            resolve({ stdout, stderr, code });
        });
    });
}
exports.spawnPromise = spawnPromise;
