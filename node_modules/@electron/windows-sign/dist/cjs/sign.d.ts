import { SignOptions } from './types';
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
export declare function sign(options: SignOptions): Promise<void>;
