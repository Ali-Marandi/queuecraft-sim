import path from 'path';
import { log } from './utils/log';
let hookFunction;
function getHookFunction(options) {
    if (options.hookFunction) {
        return options.hookFunction;
    }
    if (options.hookModulePath) {
        const module = require(path.resolve(options.hookModulePath));
        if (module.default) {
            return module.default;
        }
        if (typeof module === 'function') {
            return module;
        }
    }
    if (!hookFunction) {
        throw new Error('No hook function found. Signing will not be possible. Please see the documentation for how to pass a hook function to @electron/windows-sign');
    }
    return hookFunction;
}
/**
 * Sign with a hook function, basically letting everyone
 * write completely custom sign logic
 *
 * @param {InternalSignOptions} options
 */
export async function signWithHook(options) {
    hookFunction = getHookFunction(options);
    for (const file of options.files) {
        try {
            await hookFunction(file);
        }
        catch (error) {
            log(`Error signing ${file}`, error);
        }
    }
}
