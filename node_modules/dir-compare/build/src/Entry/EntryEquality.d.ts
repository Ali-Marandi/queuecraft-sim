import { DifferenceType, Entry, Reason } from '..';
import { AsyncDiffSet } from '../compareAsync';
import { ExtOptions } from '../ExtOptions';
/**
 * Compares two entries with identical name and type.
 */
export declare const EntryEquality: {
    isEntryEqualSync(entry1: Entry, entry2: Entry, type: DifferenceType, options: ExtOptions): FileEquality;
    isEntryEqualAsync(entry1: Entry, entry2: Entry, type: DifferenceType, asyncDiffSet: AsyncDiffSet, options: ExtOptions): FileEqualityPromise;
};
/**
 * Response given when testing identically named files for equality during synchronous comparison.
 */
export type FileEquality = {
    /**
     * True if files are identical.
     */
    same: boolean;
    /**
     * Provides reason if files are distinct
     */
    reason?: Reason;
};
/**
* Response given when testing identically named files for equality during asynchronous comparison.
*/
export type FileEqualityPromise = FileEqualityPromiseSync | FileEqualityPromiseAsync;
/**
 * Response given when testing identically named files for equality during asynchronous comparison.
 */
export type FileEqualityAsync = FileEqualityAsyncSuccess | FileEqualityAsyncError;
/**
* File equality response that represents a promise resolved synchronously.
* This can happen when files are compared by size avoiding async i/o calls.
*/
type FileEqualityPromiseSync = {
    isSync: true;
    /**
     * True if files are identical.
     */
    same: boolean;
    /**
     * Provides reason if files are distinct.
     */
    reason?: Reason;
};
/**
 * File equality response that represents a promise resolved asynchronously.
 */
type FileEqualityPromiseAsync = {
    isSync: false;
    fileEqualityAsyncPromise: Promise<FileEqualityAsync>;
};
/**
 * Successful file equality test result.
 */
type FileEqualityAsyncSuccess = {
    hasErrors: false;
    /**
     * True if files are identical.
     */
    same: boolean;
    /**
     * Provides reason if files are distinct
     */
    reason: Reason;
    /**
     * Provides comparison context during async operations.
     */
    context: FileEqualityAsyncContext;
};
/**
 * Failed file equality test result.
 */
type FileEqualityAsyncError = {
    hasErrors: true;
    error: unknown;
};
type FileEqualityAsyncContext = {
    entry1: Entry;
    entry2: Entry;
    asyncDiffSet: AsyncDiffSet;
    type1: DifferenceType;
    type2: DifferenceType;
};
export {};
//# sourceMappingURL=EntryEquality.d.ts.map