/**
 * Cross platform implementation for `__dirname`.
 *
 * @note Please do not use this method in nested other methods,
 * instead always use it in the root of your file, otherwise it may return wrong results.
 * @returns What `__dirname` would return in CJS
 */
export declare const getDirname: () => string;
/**
 * Cross platform implementation for `__filename`.
 *
 * @note Please do not use this method in nested other methods,
 * instead always use it in the root of your file, otherwise it may return wrong results.
 * @returns What `__filename` would return in CJS
 */
export declare const getFilename: () => string;
