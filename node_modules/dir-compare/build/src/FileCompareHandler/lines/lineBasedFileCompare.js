"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.lineBasedFileCompare = void 0;
const lineBasedCompareSync_1 = require("./lineBasedCompareSync");
const lineBasedCompareAsync_1 = require("./lineBasedCompareAsync");
/**
 * Compare files line by line with options to ignore
 * line endings and white space differences.
 */
exports.lineBasedFileCompare = {
    compareSync: lineBasedCompareSync_1.lineBasedCompareSync,
    compareAsync: lineBasedCompareAsync_1.lineBasedCompareAsync
};
//# sourceMappingURL=lineBasedFileCompare.js.map