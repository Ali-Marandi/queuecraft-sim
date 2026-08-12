"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.defaultResultBuilderCallback = void 0;
const path_1 = __importDefault(require("path"));
const EntryType_1 = require("../Entry/EntryType");
function defaultResultBuilderCallback(entry1, entry2, state, level, relativePath, options, statistics, diffSet, reason, permissionDeniedState) {
    if (options.noDiffSet) {
        return;
    }
    diffSet.push({
        path1: entry1 ? path_1.default.dirname(entry1.path) : undefined,
        path2: entry2 ? path_1.default.dirname(entry2.path) : undefined,
        relativePath: relativePath,
        name1: entry1 ? entry1.name : undefined,
        name2: entry2 ? entry2.name : undefined,
        state: state,
        permissionDeniedState,
        type1: EntryType_1.EntryType.getType(entry1),
        type2: EntryType_1.EntryType.getType(entry2),
        level: level,
        size1: entry1 ? entry1.stat.size : undefined,
        size2: entry2 ? entry2.stat.size : undefined,
        date1: entry1 ? entry1.stat.mtime : undefined,
        date2: entry2 ? entry2.stat.mtime : undefined,
        reason: reason
    });
}
exports.defaultResultBuilderCallback = defaultResultBuilderCallback;
//# sourceMappingURL=defaultResultBuilderCallback.js.map