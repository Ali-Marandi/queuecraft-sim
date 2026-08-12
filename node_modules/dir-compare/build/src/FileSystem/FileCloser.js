"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.FileCloser = void 0;
const fs_1 = __importDefault(require("fs"));
function closeFilesSync(fd1, fd2) {
    if (fd1) {
        fs_1.default.closeSync(fd1);
    }
    if (fd2) {
        fs_1.default.closeSync(fd2);
    }
}
function closeFilesAsync(fd1, fd2, fdQueue) {
    if (fd1 && fd2) {
        return fdQueue.closePromise(fd1).then(() => fdQueue.closePromise(fd2));
    }
    if (fd1) {
        return fdQueue.closePromise(fd1);
    }
    if (fd2) {
        return fdQueue.closePromise(fd2);
    }
    return Promise.resolve();
}
exports.FileCloser = {
    closeFilesSync,
    closeFilesAsync
};
//# sourceMappingURL=FileCloser.js.map