import { getFilesToSign } from './files';
import { signWithHook } from './sign-with-hook';
import { signWithSignTool } from './sign-with-signtool';
import { enableDebugging, log } from './utils/log';
import { booleanFromEnv } from './utils/parse-env';
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
export async function sign(options) {
    const signJavaScript = options.signJavaScript || booleanFromEnv('WINDOWS_SIGN_JAVASCRIPT');
    const hookModulePath = options.hookModulePath || process.env.WINDOWS_SIGN_HOOK_MODULE_PATH;
    if (options.debug) {
        enableDebugging();
    }
    log('Called with options', { options });
    const files = getFilesToSign(options);
    const internalOptions = {
        ...options,
        signJavaScript,
        hookModulePath,
        files
    };
    // If a hook is provides, sign with the hook
    if (internalOptions.hookFunction || internalOptions.hookModulePath) {
        log('Signing with hook');
        return signWithHook(internalOptions);
    }
    // If we're going with the defaults, we're signing
    // with signtool. Custom signing tools are also
    // handled here.
    log('Signing with signtool');
    return signWithSignTool(internalOptions);
}
