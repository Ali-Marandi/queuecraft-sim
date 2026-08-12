"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.compareSync = void 0;
const fs_1 = __importDefault(require("fs"));
const path_1 = __importDefault(require("path"));
const EntryEquality_1 = require("./Entry/EntryEquality");
const EntryBuilder_1 = require("./Entry/EntryBuilder");
const LoopDetector_1 = require("./Symlink/LoopDetector");
const EntryComparator_1 = require("./Entry/EntryComparator");
const EntryType_1 = require("./Entry/EntryType");
const Permission_1 = require("./Permission/Permission");
const StatisticsUpdate_1 = require("./Statistics/StatisticsUpdate");
/**
 * Returns the sorted list of entries in a directory.
 */
function getEntries(rootEntry, relativePath, loopDetected, origin, options) {
    if (!rootEntry || loopDetected) {
        return [];
    }
    if (rootEntry.isDirectory) {
        if (rootEntry.isPermissionDenied) {
            return [];
        }
        const entries = fs_1.default.readdirSync(rootEntry.absolutePath);
        return EntryBuilder_1.EntryBuilder.buildDirEntries(rootEntry, entries, relativePath, origin, options);
    }
    return [rootEntry];
}
/**
 * Compares two directories synchronously.
 */
function compareSync(rootEntry1, rootEntry2, level, relativePath, options, statistics, diffSet, symlinkCache) {
    const loopDetected1 = LoopDetector_1.LoopDetector.detectLoop(rootEntry1, symlinkCache.dir1);
    const loopDetected2 = LoopDetector_1.LoopDetector.detectLoop(rootEntry2, symlinkCache.dir2);
    LoopDetector_1.LoopDetector.updateSymlinkCache(symlinkCache, rootEntry1, rootEntry2, loopDetected1, loopDetected2);
    const entries1 = getEntries(rootEntry1, relativePath, loopDetected1, 'left', options);
    const entries2 = getEntries(rootEntry2, relativePath, loopDetected2, 'right', options);
    let i1 = 0, i2 = 0;
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
            let same, reason, state;
            const permissionDeniedState = Permission_1.Permission.getPermissionDeniedState(entry1, entry2);
            if (permissionDeniedState === "access-ok") {
                const compareEntryRes = EntryEquality_1.EntryEquality.isEntryEqualSync(entry1, entry2, type1, options);
                state = compareEntryRes.same ? 'equal' : 'distinct';
                same = compareEntryRes.same;
                reason = compareEntryRes.reason;
            }
            else {
                state = 'distinct';
                same = false;
                reason = "permission-denied";
            }
            options.resultBuilder(entry1, entry2, state, level, relativePath, options, statistics, diffSet, reason, permissionDeniedState);
            StatisticsUpdate_1.StatisticsUpdate.updateStatisticsBoth(entry1, entry2, same, reason, type1, permissionDeniedState, statistics, options);
            i1++;
            i2++;
            if (!options.skipSubdirs && type1 === 'directory') {
                compareSync(entry1, entry2, level + 1, path_1.default.join(relativePath, entry1.name), options, statistics, diffSet, LoopDetector_1.LoopDetector.cloneSymlinkCache(symlinkCache));
            }
        }
        else if (cmp < 0) {
            // Right missing
            const permissionDeniedState = Permission_1.Permission.getPermissionDeniedStateWhenRightMissing(entry1);
            options.resultBuilder(entry1, undefined, 'left', level, relativePath, options, statistics, diffSet, undefined, permissionDeniedState);
            StatisticsUpdate_1.StatisticsUpdate.updateStatisticsLeft(entry1, type1, permissionDeniedState, statistics, options);
            i1++;
            if (type1 === 'directory' && !options.skipSubdirs) {
                compareSync(entry1, undefined, level + 1, path_1.default.join(relativePath, entry1.name), options, statistics, diffSet, LoopDetector_1.LoopDetector.cloneSymlinkCache(symlinkCache));
            }
        }
        else {
            // Left missing
            const permissionDeniedState = Permission_1.Permission.getPermissionDeniedStateWhenLeftMissing(entry2);
            options.resultBuilder(undefined, entry2, "right", level, relativePath, options, statistics, diffSet, undefined, permissionDeniedState);
            StatisticsUpdate_1.StatisticsUpdate.updateStatisticsRight(entry2, type2, permissionDeniedState, statistics, options);
            i2++;
            if (type2 === 'directory' && !options.skipSubdirs) {
                compareSync(undefined, entry2, level + 1, path_1.default.join(relativePath, entry2.name), options, statistics, diffSet, LoopDetector_1.LoopDetector.cloneSymlinkCache(symlinkCache));
            }
        }
    }
}
exports.compareSync = compareSync;
//# sourceMappingURL=compareSync.js.map