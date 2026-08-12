"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.fileBasedNameCompare = void 0;
/**
 * Name comparator used when dir-compare is called to compare two files by content.
 * In this case the file name is ignored (ie. comparing a1.txt and a2.txt
 * will return true if file contents are identical).
 */
function fileBasedNameCompare(name1, name2, options) {
    return 0;
}
exports.fileBasedNameCompare = fileBasedNameCompare;
//# sourceMappingURL=fileBasedNameCompare.js.map