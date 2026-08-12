import { SignToolOptions } from './types';
/**
 * Options for signing with a Node.js single executable application.
 *
 * @category Single executable applications
 */
export interface SeaOptions {
    /**
     * Full path to the Node.js single executable application. Needs to end with `.exe`.
     */
    path: string;
    /**
     * A binary to use. Will use the current executable (process.execPath) by default.
     *
     * @defaultValue The Node.js {@link https://nodejs.org/api/process.html#processexecpath | `process.execPath`}
     */
    bin?: string;
    /**
     * Options to pass to SignTool.
     */
    windowsSign: SignToolOptions;
}
/**
 * This interface represents {@link SeaOptions} with all optional properties
 * inferred by `@electron/windows-sign` if not passed in by the user.
 *
 * @category Single executable applications
 */
export interface InternalSeaOptions extends Required<SeaOptions> {
    /**
     * Directory of the Node.js single executable application.
     */
    dir: string;
    /**
     * File name of the Node.js single executable application.
     */
    filename: string;
}
/**
 * cross-dir uses new Error() stacks
 * to figure out our directory in a way
 * that's somewhat cross-compatible.
 *
 * We can't just use __dirname because it's
 * undefined in ESM - and we can't use import.meta.url
 * because TypeScript won't allow usage unless you're
 * _only_ compiling for ESM.
 */
export declare const DIRNAME: string;
/**
 * Uses Node's "Single Executable App" functionality
 * to create a Node-driven signtool.exe that calls this
 * module.
 *
 * This is useful with other tooling that _always_ calls
 * a signtool.exe to sign. Some of those tools cannot be
 * easily configured, but we _can_ override their signtool.exe.
 *
 * @category Single executable applications
 */
export declare function createSeaSignTool(options?: Partial<SeaOptions>): Promise<InternalSeaOptions>;
