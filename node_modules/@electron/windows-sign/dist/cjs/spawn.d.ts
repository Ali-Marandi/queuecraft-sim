/// <reference types="node" />
import { SpawnOptions } from 'child_process';
export interface SpawnPromiseResult {
    stdout: string;
    stderr: string;
    code: number;
}
/**
 * Spawn a process as a promise
 *
 * @param {string} name
 * @param {Array<string>} args
 * @param {SpawnOptions} [options]
 * @returns {Promise<SpawnPromiseResult>}
 */
export declare function spawnPromise(name: string, args: Array<string>, options?: SpawnOptions): Promise<SpawnPromiseResult>;
