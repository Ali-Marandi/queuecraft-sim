"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.EntryEquality = void 0;
const fs_1 = __importDefault(require("fs"));
/**
 * Compares two entries with identical name and type.
 */
exports.EntryEquality = {
    isEntryEqualSync(entry1, entry2, type, options) {
        if (type === 'file') {
            return isFileEqualSync(entry1, entry2, options);
        }
        if (type === 'directory') {
            return isDirectoryEqual(entry1, entry2, options);
        }
        if (type === 'broken-link') {
            return isBrokenLinkEqual();
        }
        throw new Error('Unexpected type ' + type);
    },
    isEntryEqualAsync(entry1, entry2, type, asyncDiffSet, options) {
        if (type === 'file') {
            return isFileEqualAsync(entry1, entry2, type, asyncDiffSet, options);
        }
        if (type === 'directory') {
            return Object.assign({ isSync: true }, isDirectoryEqual(entry1, entry2, options));
        }
        if (type === 'broken-link') {
            return Object.assign({ isSync: true }, isBrokenLinkEqual());
        }
        throw new Error('Unexpected type ' + type);
    },
};
function isFileEqualSync(entry1, entry2, options) {
    if (options.compareSymlink && !isSymlinkEqual(entry1, entry2)) {
        return { same: false, reason: 'different-symlink' };
    }
    if (options.compareSize && entry1.stat.size !== entry2.stat.size) {
        return { same: false, reason: 'different-size' };
    }
    if (options.compareDate && !isDateEqual(entry1.stat.mtime, entry2.stat.mtime, options.dateTolerance)) {
        return { same: false, reason: 'different-date' };
    }
    if (options.compareContent && !options.compareFileSync(entry1.absolutePath, entry1.stat, entry2.absolutePath, entry2.stat, options)) {
        return { same: false, reason: 'different-content' };
    }
    return { same: true };
}
function isFileEqualAsync(entry1, entry2, type, asyncDiffSet, options) {
    if (options.compareSymlink && !isSymlinkEqual(entry1, entry2)) {
        return { isSync: true, same: false, reason: 'different-symlink' };
    }
    if (options.compareSize && entry1.stat.size !== entry2.stat.size) {
        return { isSync: true, same: false, reason: 'different-size' };
    }
    if (options.compareDate && !isDateEqual(entry1.stat.mtime, entry2.stat.mtime, options.dateTolerance)) {
        return { isSync: true, same: false, reason: 'different-date' };
    }
    if (options.compareContent) {
        let subDiffSet;
        if (!options.noDiffSet) {
            subDiffSet = [];
            asyncDiffSet.push(subDiffSet);
        }
        const samePromise = options.compareFileAsync(entry1.absolutePath, entry1.stat, entry2.absolutePath, entry2.stat, options)
            .then((comparisonResult) => {
            if (typeof (comparisonResult) !== "boolean") {
                return {
                    hasErrors: true,
                    error: comparisonResult
                };
            }
            const same = comparisonResult;
            const reason = same ? undefined : 'different-content';
            return {
                hasErrors: false,
                same, reason,
                context: {
                    entry1, entry2,
                    type1: type, type2: type,
                    asyncDiffSet: subDiffSet,
                }
            };
        })
            .catch((error) => ({
            hasErrors: true,
            error
        }));
        return { isSync: false, fileEqualityAsyncPromise: samePromise };
    }
    return { isSync: true, same: true };
}
function isDirectoryEqual(entry1, entry2, options) {
    if (options.compareSymlink && !isSymlinkEqual(entry1, entry2)) {
        return { same: false, reason: 'different-symlink' };
    }
    return { same: true, reason: undefined };
}
function isBrokenLinkEqual() {
    return { same: false, reason: 'broken-link' }; // broken links are never considered equal
}
/**
 * Compares two dates and returns true/false depending on tolerance (milliseconds).
 * Two dates are considered equal if the difference in milliseconds between them is less or equal than tolerance.
 */
function isDateEqual(date1, date2, tolerance) {
    return Math.abs(date1.getTime() - date2.getTime()) <= tolerance ? true : false;
}
/**
 * Compares two entries for symlink equality.
 */
function isSymlinkEqual(entry1, entry2) {
    if (!entry1.isSymlink && !entry2.isSymlink) {
        return true;
    }
    if (entry1.isSymlink && entry2.isSymlink && hasIdenticalLink(entry1.absolutePath, entry2.absolutePath)) {
        return true;
    }
    return false;
}
function hasIdenticalLink(path1, path2) {
    return fs_1.default.readlinkSync(path1) === fs_1.default.readlinkSync(path2);
}
//# sourceMappingURL=EntryEquality.js.map