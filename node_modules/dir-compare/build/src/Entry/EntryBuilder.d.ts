import { Entry, EntryOrigin } from '..';
import { ExtOptions } from '../ExtOptions';
export declare const EntryBuilder: {
    /**
     * Returns the sorted list of entries in a directory.
     */
    buildDirEntries(rootEntry: Entry, dirEntries: string[], relativePath: string, origin: EntryOrigin, options: ExtOptions): Entry[];
    buildEntry(absolutePath: string, path: string, name: string, origin: EntryOrigin, options: ExtOptions): Entry;
};
//# sourceMappingURL=EntryBuilder.d.ts.map