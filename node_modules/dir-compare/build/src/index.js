"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __exportStar = (this && this.__exportStar) || function(m, exports) {
    for (var p in m) if (p !== "default" && !Object.prototype.hasOwnProperty.call(exports, p)) __createBinding(exports, m, p);
};
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.filterHandlers = exports.compareNameHandlers = exports.fileCompareHandlers = exports.compare = exports.compareSync = void 0;
const path_1 = __importDefault(require("path"));
const fs_1 = __importDefault(require("fs"));
const compareSync_1 = require("./compareSync");
const compareAsync_1 = require("./compareAsync");
const defaultFileCompare_1 = require("./FileCompareHandler/default/defaultFileCompare");
const lineBasedFileCompare_1 = require("./FileCompareHandler/lines/lineBasedFileCompare");
const defaultNameCompare_1 = require("./NameCompare/defaultNameCompare");
const EntryBuilder_1 = require("./Entry/EntryBuilder");
const StatisticsLifecycle_1 = require("./Statistics/StatisticsLifecycle");
const LoopDetector_1 = require("./Symlink/LoopDetector");
const defaultResultBuilderCallback_1 = require("./ResultBuilder/defaultResultBuilderCallback");
const fileBasedNameCompare_1 = require("./NameCompare/fileBasedNameCompare");
const defaultFilterHandler_1 = require("./FilterHandler/defaultFilterHandler");
const ROOT_PATH = path_1.default.sep;
__exportStar(require("./types"), exports);
/**
 * Synchronously compares given paths.
 * @param path1 Left file or directory to be compared.
 * @param path2 Right file or directory to be compared.
 * @param options Comparison options.
 */
function compareSync(path1, path2, options) {
    // realpathSync() is necessary for loop detection to work properly
    const absolutePath1 = path_1.default.normalize(path_1.default.resolve(fs_1.default.realpathSync(path1)));
    const absolutePath2 = path_1.default.normalize(path_1.default.resolve(fs_1.default.realpathSync(path2)));
    const compareInfo = getCompareInfo(absolutePath1, absolutePath2);
    const extOptions = prepareOptions(compareInfo, options);
    let diffSet;
    if (!extOptions.noDiffSet) {
        diffSet = [];
    }
    const initialStatistics = StatisticsLifecycle_1.StatisticsLifecycle.initStats(extOptions);
    if (compareInfo.mode === 'mixed') {
        compareMixedEntries(absolutePath1, absolutePath2, diffSet, initialStatistics, compareInfo);
    }
    else {
        (0, compareSync_1.compareSync)(EntryBuilder_1.EntryBuilder.buildEntry(absolutePath1, path1, path_1.default.basename(absolutePath1), 'left', extOptions), EntryBuilder_1.EntryBuilder.buildEntry(absolutePath2, path2, path_1.default.basename(absolutePath2), 'right', extOptions), 0, ROOT_PATH, extOptions, initialStatistics, diffSet, LoopDetector_1.LoopDetector.initSymlinkCache());
    }
    const result = StatisticsLifecycle_1.StatisticsLifecycle.completeStatistics(initialStatistics, extOptions);
    result.diffSet = diffSet;
    return result;
}
exports.compareSync = compareSync;
/**
 * Asynchronously compares given paths.
 * @param path1 Left file or directory to be compared.
 * @param path2 Right file or directory to be compared.
 * @param extOptions Comparison options.
 */
function compare(path1, path2, options) {
    let absolutePath1, absolutePath2;
    return Promise.resolve()
        .then(() => Promise.all([wrapper.realPath(path1), wrapper.realPath(path2)]))
        .then(realPaths => {
        const realPath1 = realPaths[0];
        const realPath2 = realPaths[1];
        // realpath() is necessary for loop detection to work properly
        absolutePath1 = path_1.default.normalize(path_1.default.resolve(realPath1));
        absolutePath2 = path_1.default.normalize(path_1.default.resolve(realPath2));
    })
        .then(() => {
        const compareInfo = getCompareInfo(absolutePath1, absolutePath2);
        const extOptions = prepareOptions(compareInfo, options);
        const asyncDiffSet = [];
        const initialStatistics = StatisticsLifecycle_1.StatisticsLifecycle.initStats(extOptions);
        if (compareInfo.mode === 'mixed') {
            let diffSet;
            if (!extOptions.noDiffSet) {
                diffSet = [];
            }
            compareMixedEntries(absolutePath1, absolutePath2, diffSet, initialStatistics, compareInfo);
            const result = StatisticsLifecycle_1.StatisticsLifecycle.completeStatistics(initialStatistics, extOptions);
            result.diffSet = diffSet;
            return result;
        }
        return (0, compareAsync_1.compareAsync)(EntryBuilder_1.EntryBuilder.buildEntry(absolutePath1, path1, path_1.default.basename(absolutePath1), 'left', extOptions), EntryBuilder_1.EntryBuilder.buildEntry(absolutePath2, path2, path_1.default.basename(absolutePath2), 'right', extOptions), 0, ROOT_PATH, extOptions, initialStatistics, asyncDiffSet, LoopDetector_1.LoopDetector.initSymlinkCache())
            .then(() => {
            const result = StatisticsLifecycle_1.StatisticsLifecycle.completeStatistics(initialStatistics, extOptions);
            if (!extOptions.noDiffSet) {
                const diffSet = [];
                rebuildAsyncDiffSet(result, asyncDiffSet, diffSet);
                result.diffSet = diffSet;
            }
            return result;
        });
    });
}
exports.compare = compare;
/**
 * List of {@link CompareFileHandler}s included with dir-compare.
 *
 * See [File content comparators](https://github.com/gliviu/dir-compare#file-content-comparators) for details.
 */
exports.fileCompareHandlers = {
    defaultFileCompare: defaultFileCompare_1.defaultFileCompare,
    lineBasedFileCompare: lineBasedFileCompare_1.lineBasedFileCompare
};
/**
 * List of {@link CompareNameHandler}s included with dir-compare.
 *
 * See [Name comparators](https://github.com/gliviu/dir-compare#name-comparators) for details.
 */
exports.compareNameHandlers = {
    defaultNameCompare: defaultNameCompare_1.defaultNameCompare
};
/**
 * List of {@link FilterHandler}s included with dir-compare.
 *
 * See [Glob filter](https://github.com/gliviu/dir-compare#glob-filter) for details.
 */
exports.filterHandlers = {
    defaultFilterHandler: defaultFilterHandler_1.defaultFilterHandler
};
const wrapper = {
    realPath(path, options) {
        return new Promise((resolve, reject) => {
            fs_1.default.realpath(path, options, (err, resolvedPath) => {
                if (err) {
                    reject(err);
                }
                else {
                    resolve(resolvedPath);
                }
            });
        });
    }
};
function prepareOptions(compareInfo, options) {
    options = options || {};
    const clone = JSON.parse(JSON.stringify(options));
    clone.resultBuilder = options.resultBuilder;
    clone.compareFileSync = options.compareFileSync;
    clone.compareFileAsync = options.compareFileAsync;
    clone.compareNameHandler = options.compareNameHandler;
    clone.filterHandler = options.filterHandler;
    if (!clone.resultBuilder) {
        clone.resultBuilder = defaultResultBuilderCallback_1.defaultResultBuilderCallback;
    }
    if (!clone.compareFileSync) {
        clone.compareFileSync = defaultFileCompare_1.defaultFileCompare.compareSync;
    }
    if (!clone.compareFileAsync) {
        clone.compareFileAsync = defaultFileCompare_1.defaultFileCompare.compareAsync;
    }
    if (!clone.compareNameHandler) {
        const isFileBasedCompare = compareInfo.mode === 'files';
        clone.compareNameHandler = isFileBasedCompare ? fileBasedNameCompare_1.fileBasedNameCompare : defaultNameCompare_1.defaultNameCompare;
    }
    if (!clone.filterHandler) {
        clone.filterHandler = defaultFilterHandler_1.defaultFilterHandler;
    }
    clone.dateTolerance = clone.dateTolerance || 1000;
    clone.dateTolerance = Number(clone.dateTolerance);
    if (isNaN(clone.dateTolerance)) {
        throw new Error('Date tolerance is not a number');
    }
    return clone;
}
// Async DiffSets are kept into recursive structures.
// This method transforms them into one dimensional arrays.
function rebuildAsyncDiffSet(statistics, asyncDiffSet, diffSet) {
    asyncDiffSet.forEach(rawDiff => {
        if (!Array.isArray(rawDiff)) {
            diffSet.push(rawDiff);
        }
        else {
            rebuildAsyncDiffSet(statistics, rawDiff, diffSet);
        }
    });
}
function getCompareInfo(path1, path2) {
    const stat1 = fs_1.default.lstatSync(path1);
    const stat2 = fs_1.default.lstatSync(path2);
    if (stat1.isDirectory() && stat2.isDirectory()) {
        return {
            mode: 'directories',
            type1: 'directory',
            type2: 'directory',
            size1: stat1.size,
            size2: stat2.size,
            date1: stat1.mtime,
            date2: stat2.mtime,
        };
    }
    if (stat1.isFile() && stat2.isFile()) {
        return {
            mode: 'files',
            type1: 'file',
            type2: 'file',
            size1: stat1.size,
            size2: stat2.size,
            date1: stat1.mtime,
            date2: stat2.mtime,
        };
    }
    return {
        mode: 'mixed',
        type1: stat1.isFile() ? 'file' : 'directory',
        type2: stat2.isFile() ? 'file' : 'directory',
        size1: stat1.size,
        size2: stat2.size,
        date1: stat1.mtime,
        date2: stat2.mtime,
    };
}
/**
 * Normally dir-compare is used to compare either two directories or two files.
 * This method is used when one directory is compared to a file.
 */
function compareMixedEntries(path1, path2, diffSet, initialStatistics, compareInfo) {
    initialStatistics.distinct = 2;
    initialStatistics.distinctDirs = 1;
    initialStatistics.distinctFiles = 1;
    if (diffSet) {
        diffSet.push({
            path1,
            path2,
            relativePath: '',
            name1: path_1.default.basename(path1),
            name2: path_1.default.basename(path2),
            state: 'distinct',
            permissionDeniedState: 'access-ok',
            type1: compareInfo.type1,
            type2: compareInfo.type2,
            level: 0,
            size1: compareInfo.size1,
            size2: compareInfo.size2,
            date1: compareInfo.date1,
            date2: compareInfo.date2,
            reason: 'different-content',
        });
    }
}
//# sourceMappingURL=index.js.map