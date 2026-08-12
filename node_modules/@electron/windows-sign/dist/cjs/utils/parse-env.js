"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.booleanFromEnv = void 0;
/**
 * Tries to parse an process.env string to a boolean.
 * Will understand undefined as the default value
 * Will understand "false", "False", "fAlse", or "0" as `false`
 * Will understand everything else as true
 *
 * @export
 * @param {string} name
 * @return {*}  {boolean}
 */
function booleanFromEnv(name) {
    const value = process.env[name];
    if (value === undefined) {
        return undefined;
    }
    if (value.toLowerCase() === 'false' || value === '0') {
        return false;
    }
    return !!value;
}
exports.booleanFromEnv = booleanFromEnv;
