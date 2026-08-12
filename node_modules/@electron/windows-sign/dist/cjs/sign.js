"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.sign = void 0;
const files_1 = require("./files");
const sign_with_hook_1 = require("./sign-with-hook");
const sign_with_signtool_1 = require("./sign-with-signtool");
const log_1 = require("./utils/log");
const parse_env_1 = require("./utils/parse-env");
/**
 * This is the main function exported from this module. It'll
 * look at your options, determine the best way to sign a file,
 * and then return one of our internal functions to do the actual
 * signing.
 *
 * @param options
 * @returns {Promise<void>}
 *
 * @category Sign
 */
async function sign(options) {
    const signJavaScript = options.signJavaScript || (0, parse_env_1.booleanFromEnv)('WINDOWS_SIGN_JAVASCRIPT');
    const hookModulePath = options.hookModulePath || process.env.WINDOWS_SIGN_HOOK_MODULE_PATH;
    if (options.debug) {
        (0, log_1.enableDebugging)();
    }
    (0, log_1.log)('Called with options', { options });
    const files = (0, files_1.getFilesToSign)(options);
    const internalOptions = {
        ...options,
        signJavaScript,
        hookModulePath,
        files
    };
    // If a hook is provides, sign with the hook
    if (internalOptions.hookFunction || internalOptions.hookModulePath) {
        (0, log_1.log)('Signing with hook');
        return (0, sign_with_hook_1.signWithHook)(internalOptions);
    }
    // If we're going with the defaults, we're signing
    // with signtool. Custom signing tools are also
    // handled here.
    (0, log_1.log)('Signing with signtool');
    return (0, sign_with_signtool_1.signWithSignTool)(internalOptions);
}
exports.sign = sign;
