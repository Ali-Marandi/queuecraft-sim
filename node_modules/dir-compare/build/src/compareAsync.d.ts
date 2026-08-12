import { ExtOptions } from './ExtOptions';
import { Difference, InitialStatistics } from '.';
import { SymlinkCache } from './Symlink/LoopDetector';
import { OptionalEntry } from './Entry/EntryType';
/**
 * List of differences occurred during comparison.
 * Async DiffSets are kept into recursive structures.
 */
export type AsyncDiffSet = Array<Difference | AsyncDiffSet>;
/**
 * Compares two directories asynchronously.
 */
export declare function compareAsync(rootEntry1: OptionalEntry, rootEntry2: OptionalEntry, level: number, relativePath: string, options: ExtOptions, statistics: InitialStatistics, asyncDiffSet: AsyncDiffSet, symlinkCache: SymlinkCache): Promise<void>;
//# sourceMappingURL=compareAsync.d.ts.map