"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.compareAsync = void 0;
const path_1 = __importDefault(require("path"));
const EntryEquality_1 = require("./Entry/EntryEquality");
const FsPromise_1 = require("./FileSystem/FsPromise");
const EntryBuilder_1 = require("./Entry/EntryBuilder");
const LoopDetector_1 = require("./Symlink/LoopDetector");
const EntryComparator_1 = require("./Entry/EntryComparator");
const EntryType_1 = require("./Entry/EntryType");
const Permission_1 = require("./Permission/Permission");
const StatisticsUpdate_1 = require("./Statistics/StatisticsUpdate");
const p_limit_1 = __importDefault(require("p-limit"));
/**
 * Limits concurrent promises.
 */
const CONCURRENCY = 2;
/**
 * Returns the sorted list of entries in a directory.
 */
function getEntries(rootEntry, relativePath, loopDetected, origin, options) {
    if (!rootEntry || loopDetected) {
        return Promise.resolve([]);
    }
    if (rootEntry.isDirectory) {
        if (rootEntry.isPermissionDenied) {
            return Promise.resolve([]);
        }
        return FsPromise_1.FsPromise.readdir(rootEntry.absolutePath)
            .then(entries => EntryBuilder_1.EntryBuilder.buildDirEntries(rootEntry, entries, relativePath, origin, options));
    }
    return Promise.resolve([rootEntry]);
}
/**
 * Compares two directories asynchronously.
 */
function compareAsync(rootEntry1, rootEntry2, level, relativePath, options, statistics, asyncDiffSet, symlinkCache) {
    const limit = (0, p_limit_1.default)(CONCURRENCY);
    const loopDetected1 = LoopDetector_1.LoopDetector.detectLoop(rootEntry1, symlinkCache.dir1);
    const loopDetected2 = LoopDetector_1.LoopDetector.detectLoop(rootEntry2, symlinkCache.dir2);
    LoopDetector_1.LoopDetector.updateSymlinkCache(symlinkCache, rootEntry1, rootEntry2, loopDetected1, loopDetected2);
    return Promise.all([getEntries(rootEntry1, relativePath, loopDetected1, 'left', options), getEntries(rootEntry2, relativePath, loopDetected2, 'right', options)])
        .then(entriesResult => {
        const entries1 = entriesResult[0];
        const entries2 = entriesResult[1];
        let i1 = 0, i2 = 0;
        const comparePromises = [];
        const fileEqualityAsyncPromises = [];
        while (i1 < entries1.length || i2 < entries2.length) {
            const entry1 = entries1[i1];
            const entry2 = entries2[i2];
            let type1, type2;
            // compare entry name (-1, 0, 1)
            let cmp;
            if (i1 < entries1.length && i2 < entries2.length) {
                cmp = EntryComparator_1.EntryComparator.compareEntry(entry1, entry2, options);
                type1 = EntryType_1.EntryType.getType(entry1);
                type2 = EntryType_1.EntryType.getType(entry2);
            }
            else if (i1 < entries1.length) {
                type1 = EntryType_1.EntryType.getType(entry1);
                type2 = EntryType_1.EntryType.getType(undefined);
                cmp = -1;
            }
            else {
                type1 = EntryType_1.EntryType.getType(undefined);
                type2 = EntryType_1.EntryType.getType(entry2);
                cmp = 1;
            }
            // process entry
            if (cmp === 0) {
                // Both left/right exist and have the same name and type
                const permissionDeniedState = Permission_1.Permission.getPermissionDeniedState(entry1, entry2);
                if (permissionDeniedState === "access-ok") {
                    const compareEntryRes = EntryEquality_1.EntryEquality.isEntryEqualAsync(entry1, entry2, type1, asyncDiffSet, options);
                    if (compareEntryRes.isSync) {
                        options.resultBuilder(entry1, entry2, compareEntryRes.same ? 'equal' : 'distinct', level, relativePath, options, statistics, asyncDiffSet, compareEntryRes.reason, permissionDeniedState);
                        StatisticsUpdate_1.StatisticsUpdate.updateStatisticsBoth(entry1, entry2, compareEntryRes.same, compareEntryRes.reason, type1, permissionDeniedState, statistics, options);
                    }
                    else {
                        fileEqualityAsyncPromises.push(compareEntryRes.fileEqualityAsyncPromise);
                    }
                }
                else {
                    const state = 'distinct';
                    const reason = "permission-denied";
                    const same = false;
                    options.resultBuilder(entry1, entry2, state, level, relativePath, options, statistics, asyncDiffSet, reason, permissionDeniedState);
                    StatisticsUpdate_1.StatisticsUpdate.updateStatisticsBoth(entry1, entry2, same, reason, type1, permissionDeniedState, statistics, options);
                }
                i1++;
                i2++;
                if (!options.skipSubdirs && type1 === 'directory') {
                    const subDiffSet = [];
                    if (!options.noDiffSet) {
                        asyncDiffSet.push(subDiffSet);
                    }
                    const comparePromise = limit(() => compareAsync(entry1, entry2, level + 1, path_1.default.join(relativePath, entry1.name), options, statistics, subDiffSet, LoopDetector_1.LoopDetector.cloneSymlinkCache(symlinkCache)));
                    comparePromises.push(comparePromise);
                }
            }
            else if (cmp < 0) {
                // Right missing
                const permissionDeniedState = Permission_1.Permission.getPermissionDeniedStateWhenRightMissing(entry1);
                options.resultBuilder(entry1, undefined, 'left', level, relativePath, options, statistics, asyncDiffSet, undefined, permissionDeniedState);
                StatisticsUpdate_1.StatisticsUpdate.updateStatisticsLeft(entry1, type1, permissionDeniedState, statistics, options);
                i1++;
                if (type1 === 'directory' && !options.skipSubdirs) {
                    const subDiffSet = [];
                    if (!options.noDiffSet) {
                        asyncDiffSet.push(subDiffSet);
                    }
                    const comparePromise = limit(() => compareAsync(entry1, undefined, level + 1, path_1.default.join(relativePath, entry1.name), options, statistics, subDiffSet, LoopDetector_1.LoopDetector.cloneSymlinkCache(symlinkCache)));
                    comparePromises.push(comparePromise);
                }
            }
            else {
                // Left missing
                const permissionDeniedState = Permission_1.Permission.getPermissionDeniedStateWhenLeftMissing(entry2);
                options.resultBuilder(undefined, entry2, 'right', level, relativePath, options, statistics, asyncDiffSet, undefined, permissionDeniedState);
                StatisticsUpdate_1.StatisticsUpdate.updateStatisticsRight(entry2, type2, permissionDeniedState, statistics, options);
                i2++;
                if (type2 === 'directory' && !options.skipSubdirs) {
                    const subDiffSet = [];
                    if (!options.noDiffSet) {
                        asyncDiffSet.push(subDiffSet);
                    }
                    const comparePromise = limit(() => compareAsync(undefined, entry2, level + 1, path_1.default.join(relativePath, entry2.name), options, statistics, subDiffSet, LoopDetector_1.LoopDetector.cloneSymlinkCache(symlinkCache)));
                    comparePromises.push(comparePromise);
                }
            }
        }
        return Promise.all(comparePromises)
            .then(() => Promise.all(fileEqualityAsyncPromises)
            .then(fileEqualityAsyncResults => {
            for (let i = 0; i < fileEqualityAsyncResults.length; i++) {
                const fileEqualityAsync = fileEqualityAsyncResults[i];
                if (fileEqualityAsync.hasErrors) {
                    return Promise.reject(fileEqualityAsync.error);
                }
                const permissionDeniedState = "access-ok";
                options.resultBuilder(fileEqualityAsync.context.entry1, fileEqualityAsync.context.entry2, fileEqualityAsync.same ? 'equal' : 'distinct', level, relativePath, options, statistics, fileEqualityAsync.context.asyncDiffSet, fileEqualityAsync.reason, permissionDeniedState);
                StatisticsUpdate_1.StatisticsUpdate.updateStatisticsBoth(fileEqualityAsync.context.entry1, fileEqualityAsync.context.entry2, fileEqualityAsync.same, fileEqualityAsync.reason, fileEqualityAsync.context.type1, permissionDeniedState, statistics, options);
            }
        }));
    });
}
exports.compareAsync = compareAsync;
//# sourceMappingURL=compareAsync.js.map