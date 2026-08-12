"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.defaultNameCompare = void 0;
/**
 * The default implementation uses the 'strcmp' function for comparing file or directory names.
 */
const defaultNameCompare = (name1, name2, options) => {
    if (options.ignoreCase) {
        name1 = name1.toLowerCase();
        name2 = name2.toLowerCase();
    }
    return strcmp(name1, name2);
};
exports.defaultNameCompare = defaultNameCompare;
function strcmp(str1, str2) {
    return ((str1 === str2) ? 0 : ((str1 > str2) ? 1 : -1));
}
//# sourceMappingURL=defaultNameCompare.js.map