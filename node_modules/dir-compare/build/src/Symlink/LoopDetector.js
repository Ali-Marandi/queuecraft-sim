"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.LoopDetector = void 0;
const fs_1 = __importDefault(require("fs"));
/**
 * Provides symlink loop detection to directory traversal algorithm.
 */
exports.LoopDetector = {
    detectLoop(entry, symlinkCache) {
        if (entry && entry.isSymlink) {
            const realPath = fs_1.default.realpathSync(entry.absolutePath);
            if (symlinkCache[realPath]) {
                return true;
            }
        }
        return false;
    },
    initSymlinkCache() {
        return {
            dir1: {},
            dir2: {}
        };
    },
    updateSymlinkCache(symlinkCache, rootEntry1, rootEntry2, loopDetected1, loopDetected2) {
        let symlinkCachePath1, symlinkCachePath2;
        if (rootEntry1 && !loopDetected1) {
            symlinkCachePath1 = rootEntry1.isSymlink ? fs_1.default.realpathSync(rootEntry1.absolutePath) : rootEntry1.absolutePath;
            symlinkCache.dir1[symlinkCachePath1] = true;
        }
        if (rootEntry2 && !loopDetected2) {
            symlinkCachePath2 = rootEntry2.isSymlink ? fs_1.default.realpathSync(rootEntry2.absolutePath) : rootEntry2.absolutePath;
            symlinkCache.dir2[symlinkCachePath2] = true;
        }
    },
    cloneSymlinkCache(symlinkCache) {
        return {
            dir1: shallowClone(symlinkCache.dir1),
            dir2: shallowClone(symlinkCache.dir2)
        };
    },
};
function shallowClone(obj) {
    const cloned = {};
    Object.keys(obj).forEach(key => {
        cloned[key] = obj[key];
    });
    return cloned;
}
//# sourceMappingURL=LoopDetector.js.map