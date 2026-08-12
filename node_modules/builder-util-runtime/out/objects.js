"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.mapToObject = mapToObject;
exports.isValidKey = isValidKey;
exports.asArray = asArray;
exports.deepAssign = deepAssign;
exports.objectToArgs = objectToArgs;
function mapToObject(map) {
    const obj = {};
    for (const [key, value] of map) {
        if (!isValidKey(key)) {
            continue;
        }
        if (value instanceof Map) {
            obj[key] = mapToObject(value);
        }
        else {
            obj[key] = value;
        }
    }
    return obj;
}
function isValidKey(key) {
    const protectedProperties = ["__proto__", "prototype", "constructor"];
    if (protectedProperties.includes(key)) {
        return false;
    }
    return ["string", "number", "symbol", "boolean"].includes(typeof key) || key === null;
}
function asArray(v) {
    if (v == null) {
        return [];
    }
    else if (Array.isArray(v)) {
        return v;
    }
    else {
        return [v];
    }
}
function isObject(x) {
    if (Array.isArray(x)) {
        return false;
    }
    const type = typeof x;
    return type === "object" || type === "function";
}
function assignKey(target, from, key) {
    const value = from[key];
    // https://github.com/electron-userland/electron-builder/pull/562
    if (value === undefined) {
        return;
    }
    const prevValue = target[key];
    if (prevValue == null || value == null || !isObject(prevValue) || !isObject(value)) {
        // Merge arrays.
        if (Array.isArray(prevValue) && Array.isArray(value)) {
            target[key] = Array.from(new Set(prevValue.concat(value)));
        }
        else {
            target[key] = value;
        }
    }
    else {
        target[key] = assign(prevValue, value);
    }
}
function assign(to, from) {
    if (to !== from) {
        for (const key of Object.getOwnPropertyNames(from)) {
            if (isValidKey(key)) {
                assignKey(to, from, key);
            }
        }
    }
    return to;
}
function deepAssign(target, ...objects) {
    for (const o of objects) {
        if (o != null) {
            assign(target, o);
        }
    }
    return target;
}
// Flag names must be letters/digits/hyphens only (e.g. "maintainer", "deb-priority").
// Anything else could inject extra flags into the argument array.
const SAFE_FLAG_NAME_RE = /^[a-zA-Z][a-zA-Z0-9-]*$/;
// Null bytes truncate arguments at the C layer; newlines can split arguments in some parsers.
const UNSAFE_VALUE_RE = /[\0\r\n]/;
function objectToArgs(obj) {
    const args = Object.entries(obj).reduce((args, [name, value]) => {
        if (!isValidKey(name) || value == null) {
            return args;
        }
        if (!SAFE_FLAG_NAME_RE.test(name)) {
            throw new Error(`objectToArgs: unsafe flag name rejected: ${JSON.stringify(name)}`);
        }
        if (UNSAFE_VALUE_RE.test(value)) {
            throw new Error(`objectToArgs: value for --${name} contains a null byte or newline`);
        }
        return args.concat([`--${name}`, value]);
    }, []);
    return Object.freeze(args);
}
//# sourceMappingURL=objects.js.map