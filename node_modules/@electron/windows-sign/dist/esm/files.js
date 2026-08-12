import path from 'path';
import fs from 'fs-extra';
const IS_PE_REGEX = /\.(exe|dll|sys|efi|scr|node)$/i;
const IS_MSI_REGEX = /\.msi$/i;
const IS_PACKAGE_REGEX = /\.(appx|appxbundle|msix|msixbundle)$/i;
const IS_CATCAB_REGEX = /\.(cat|cab)$/i;
const IS_SILVERLIGHT_REGEX = /\.xap$/i;
const IS_SCRIPT_REGEX = /\.(vbs|wsf|ps1)$/i;
const IS_JS_REGEX = /\.js$/i;
/**
 * Recursively goes through an entire directory and returns an array
 * of full paths for files ot sign.
 *
 * - Portable executable files (.exe, .dll, .sys, .efi, .scr, .node)
 * - Microsoft installers (.msi)
 * - APPX/MSIX packages (.appx, .appxbundle, .msix, .msixbundle)
 * - Catalog files (.cat)
 * - Cabinet files (.cab)
 * - Silverlight applications (.xap)
 * - Scripts (.vbs, .wsf, .ps1)
 * If configured:
 * - JavaScript files (.js)
 */
export function getFilesToSign(options, dir) {
    if (isSignOptionsForFiles(options)) {
        return options.files;
    }
    dir = dir || options.appDirectory;
    // Array of file paths to sign
    const result = [];
    // Iterate over the app directory, looking for files to sign
    const files = fs.readdirSync(dir);
    const regexes = [
        IS_PE_REGEX,
        IS_MSI_REGEX,
        IS_PACKAGE_REGEX,
        IS_CATCAB_REGEX,
        IS_SILVERLIGHT_REGEX,
        IS_SCRIPT_REGEX
    ];
    if (options.signJavaScript) {
        regexes.push(IS_JS_REGEX);
    }
    for (const file of files) {
        const fullPath = path.resolve(dir, file);
        if (fs.statSync(fullPath).isDirectory()) {
            // If it's a directory, recurse
            result.push(...getFilesToSign(options, fullPath));
        }
        else if (regexes.some((regex) => regex.test(file))) {
            // If it's a match, add it to the list
            result.push(fullPath);
        }
    }
    return result;
}
function isSignOptionsForFiles(input) {
    return !!input.files;
}
