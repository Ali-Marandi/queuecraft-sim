import { InternalSignOptions } from './types';
/**
 * Sign with a hook function, basically letting everyone
 * write completely custom sign logic
 *
 * @param {InternalSignOptions} options
 */
export declare function signWithHook(options: InternalSignOptions): Promise<void>;
