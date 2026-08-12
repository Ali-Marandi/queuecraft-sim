"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.defaultFilterHandler = void 0;
const path_1 = __importDefault(require("path"));
const minimatch_1 = __importDefault(require("minimatch"));
/**
 * Default filter handler that uses minimatch to accept/ignore files based on includeFilter and excludeFilter options.
 */
const defaultFilterHandler = (entry, relativePath, options) => {
    const path = path_1.default.join(relativePath, entry.name);
    if ((entry.stat.isFile() && options.includeFilter) && (!match(path, options.includeFilter))) {
        return false;
    }
    if ((options.excludeFilter) && (match(path, options.excludeFilter))) {
        return false;
    }
    return true;
};
exports.defaultFilterHandler = defaultFilterHandler;
/**
 * Matches path by pattern.
 */
function match(path, pattern) {
    const patternArray = pattern.split(',');
    for (let i = 0; i < patternArray.length; i++) {
        const pat = patternArray[i];
        if ((0, minimatch_1.default)(path, pat, { dot: true, matchBase: true })) { //nocase
            return true;
        }
    }
    return false;
}
//# sourceMappingURL=defaultFilterHandler.js.map