"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.EntryType = void 0;
exports.EntryType = {
    /**
     * One of 'missing','file','directory','broken-link'
     */
    getType(entry) {
        if (!entry) {
            return 'missing';
        }
        if (entry.isBrokenLink) {
            return 'broken-link';
        }
        if (entry.isDirectory) {
            return 'directory';
        }
        return 'file';
    }
};
//# sourceMappingURL=EntryType.js.map