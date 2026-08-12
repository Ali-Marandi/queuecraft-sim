"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.log = exports.enableDebugging = void 0;
const debug_1 = require("debug");
function enableDebugging() {
    debug_1.debug.enable('electron-windows-sign');
}
exports.enableDebugging = enableDebugging;
exports.log = (0, debug_1.debug)('electron-windows-sign');
