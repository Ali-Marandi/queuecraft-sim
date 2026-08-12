"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.signWithHook = void 0;
const path_1 = __importDefault(require("path"));
const log_1 = require("./utils/log");
let hookFunction;
function getHookFunction(options) {
    if (options.hookFunction) {
        return options.hookFunction;
    }
    if (options.hookModulePath) {
        const module = require(path_1.default.resolve(options.hookModulePath));
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
async function signWithHook(options) {
    hookFunction = getHookFunction(options);
    for (const file of options.files) {
        try {
            await hookFunction(file);
        }
        catch (error) {
            (0, log_1.log)(`Error signing ${file}`, error);
        }
    }
}
exports.signWithHook = signWithHook;
