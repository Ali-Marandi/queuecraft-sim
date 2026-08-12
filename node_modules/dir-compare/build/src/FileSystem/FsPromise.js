"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.FsPromise = void 0;
const fs_1 = __importDefault(require("fs"));
exports.FsPromise = {
    readdir(path) {
        return new Promise((resolve, reject) => {
            fs_1.default.readdir(path, (err, files) => {
                if (err) {
                    reject(err);
                }
                else {
                    resolve(files);
                }
            });
        });
    },
    read(fd, buffer, offset, length, position) {
        return new Promise((resolve, reject) => {
            fs_1.default.read(fd, buffer, offset, length, position, (err, bytesRead) => {
                if (err) {
                    reject(err);
                }
                else {
                    resolve(bytesRead);
                }
            });
        });
    },
};
//# sourceMappingURL=FsPromise.js.map