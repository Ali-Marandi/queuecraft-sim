import { InitialStatistics, OptionalDiffSet } from '.';
import { ExtOptions } from './ExtOptions';
import { SymlinkCache } from './Symlink/LoopDetector';
import { OptionalEntry } from './Entry/EntryType';
/**
 * Compares two directories synchronously.
 */
export declare function compareSync(rootEntry1: OptionalEntry, rootEntry2: OptionalEntry, level: number, relativePath: string, options: ExtOptions, statistics: InitialStatistics, diffSet: OptionalDiffSet, symlinkCache: SymlinkCache): void;
//# sourceMappingURL=compareSync.d.ts.map