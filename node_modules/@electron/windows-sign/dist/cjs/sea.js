"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.createSeaSignTool = exports.DIRNAME = void 0;
const cross_dirname_1 = require("cross-dirname");
const path_1 = __importDefault(require("path"));
const os_1 = __importDefault(require("os"));
const fs_extra_1 = __importDefault(require("fs-extra"));
const postject_1 = __importDefault(require("postject"));
const spawn_1 = require("./spawn");
const log_1 = require("./utils/log");
/**
 * cross-dir uses new Error() stacks
 * to figure out our directory in a way
 * that's somewhat cross-compatible.
 *
 * We can't just use __dirname because it's
 * undefined in ESM - and we can't use import.meta.url
 * because TypeScript won't allow usage unless you're
 * _only_ compiling for ESM.
 */
exports.DIRNAME = (0, cross_dirname_1.getDirname)();
const FILENAMES = {
    SEA_CONFIG: 'sea-config.json',
    SEA_MAIN: 'sea.js',
    SEA_BLOB: 'sea.blob',
    SEA_RECEIVER: 'receiver.mjs'
};
const SEA_MAIN_SCRIPT = `
const bin = "%PATH_TO_BIN%";
const script = "%PATH_TO_SCRIPT%";
const options = %WINDOWS_SIGN_OPTIONS%

const { spawnSync } = require('child_process');

function main() {
  console.log("@electron/windows-sign sea");
  console.log({ bin, script });

  try {
    const spawn = spawnSync(
      bin,
      [ script, JSON.stringify(options), JSON.stringify(process.argv.slice(1)) ],
      { stdio: ['inherit', 'inherit', 'pipe'] }
    );

    if (spawn.status !== 0) {
      throw new Error(\`Spawn failed with code: \${spawn.status}. Stderr: \${spawn.stderr}\`);
    } 
  } catch (error) {
    // Do not rethrow the error or write it to stdout/stderr. Then the process won't terminate.
    // See: https://github.com/electron/windows-sign/pull/48
    process.exit(1);
  }
}

main();
`;
const SEA_RECEIVER_SCRIPT = `
import { sign } from '@electron/windows-sign';
import fs from 'fs-extra';
import path from 'path';

const logPath = path.join('electron-windows-sign.log');
const options = JSON.parse(process.argv[2]);
const signArgv = JSON.parse(process.argv[3]);
const files = signArgv.slice(-1);

try {
  fs.appendFileSync(logPath, \`\\nCalled with: \${JSON.stringify(process.argv, null, 2)}\`);

  sign({ ...options, files })
  .then((result) => {
    fs.appendFileSync(logPath, \`\\nSuccessfully signed with result: \${result}\`);
  })
  .catch((error) => {
    fs.appendFileSync(logPath, \`\\nError from sign: \${error}\`);
    throw new Error(error);
  });
} catch (error) {
  fs.appendFileSync(logPath, \`\\Error invoking sign: \${error}\`);
  throw new Error(error);
}
`;
/**
 * Uses Node's "Single Executable App" functionality
 * to create a Node-driven signtool.exe that calls this
 * module.
 *
 * This is useful with other tooling that _always_ calls
 * a signtool.exe to sign. Some of those tools cannot be
 * easily configured, but we _can_ override their signtool.exe.
 *
 * @category Single executable applications
 */
async function createSeaSignTool(options = {}) {
    checkCompatibility();
    const requiredOptions = await getOptions(options);
    await createFiles(requiredOptions);
    await createBlob(requiredOptions);
    await createBinary(requiredOptions);
    await createSeaReceiver(requiredOptions);
    await cleanup(requiredOptions);
    return requiredOptions;
}
exports.createSeaSignTool = createSeaSignTool;
async function createSeaReceiver(options) {
    const receiverPath = path_1.default.join(options.dir, FILENAMES.SEA_RECEIVER);
    await fs_extra_1.default.ensureFile(receiverPath);
    await fs_extra_1.default.writeFile(receiverPath, SEA_RECEIVER_SCRIPT);
}
async function createFiles(options) {
    const { dir, bin } = options;
    const receiverPath = path_1.default.join(options.dir, FILENAMES.SEA_RECEIVER);
    // sea-config.json
    await fs_extra_1.default.outputJSON(path_1.default.join(dir, FILENAMES.SEA_CONFIG), {
        main: FILENAMES.SEA_MAIN,
        output: FILENAMES.SEA_BLOB,
        disableExperimentalSEAWarning: true
    }, {
        spaces: 2
    });
    // signtool.js
    const binPath = bin || process.execPath;
    const script = SEA_MAIN_SCRIPT
        .replace('%PATH_TO_BIN%', escapeMaybe(binPath))
        .replace('%PATH_TO_SCRIPT%', escapeMaybe(receiverPath))
        .replace('%WINDOWS_SIGN_OPTIONS%', JSON.stringify(options.windowsSign));
    await fs_extra_1.default.outputFile(path_1.default.join(dir, FILENAMES.SEA_MAIN), script);
}
async function createBlob(options) {
    const args = ['--experimental-sea-config', 'sea-config.json'];
    const bin = process.execPath;
    const cwd = options.dir;
    (0, log_1.log)(`Calling ${bin} with options:`, args);
    const { stderr, stdout } = await (0, spawn_1.spawnPromise)(bin, args, {
        cwd
    });
    (0, log_1.log)('stdout:', stdout);
    (0, log_1.log)('stderr:', stderr);
}
async function createBinary(options) {
    const { dir, filename } = options;
    (0, log_1.log)(`Creating ${filename} in ${dir}`);
    // Copy Node over
    const seaPath = path_1.default.join(dir, filename);
    await fs_extra_1.default.copyFile(process.execPath, seaPath);
    // Remove the Node signature
    const signtool = path_1.default.join(exports.DIRNAME, '../../vendor/signtool.exe');
    await (0, spawn_1.spawnPromise)(signtool, [
        'remove',
        '/s',
        seaPath
    ]);
    // Inject the blob
    const blob = await fs_extra_1.default.readFile(path_1.default.join(dir, FILENAMES.SEA_BLOB));
    await postject_1.default.inject(seaPath, 'NODE_SEA_BLOB', blob, {
        sentinelFuse: 'NODE_SEA_FUSE_fce680ab2cc467b6e072b8b5df1996b2'
    });
}
async function cleanup(options) {
    const { dir } = options;
    const toRemove = [
        FILENAMES.SEA_BLOB,
        FILENAMES.SEA_MAIN,
        FILENAMES.SEA_CONFIG
    ];
    for (const file of toRemove) {
        try {
            await fs_extra_1.default.remove(path_1.default.join(dir, file));
        }
        catch (error) {
            console.warn(`Tried and failed to remove ${file}. Continuing.`, error);
        }
    }
}
async function getOptions(options) {
    const cloned = { ...options };
    if (!cloned.path) {
        cloned.path = path_1.default.join(os_1.default.homedir(), '.electron', 'windows-sign', 'sea.exe');
        await fs_extra_1.default.ensureFile(cloned.path);
    }
    if (!cloned.bin) {
        cloned.bin = process.execPath;
    }
    if (!cloned.windowsSign) {
        throw new Error('Did not find windowsSign options, which are required');
    }
    return {
        path: cloned.path,
        dir: path_1.default.dirname(cloned.path),
        filename: path_1.default.basename(cloned.path),
        bin: cloned.bin,
        windowsSign: cloned.windowsSign
    };
}
/**
 * Ensures that the current Node.js version supports SEA app generation and errors if not.
 */
function checkCompatibility() {
    const version = process.versions.node;
    const split = version.split('.');
    const major = parseInt(split[0], 10);
    if (major >= 20) {
        return true;
    }
    throw new Error(`Your Node.js version (${process.version}) does not support Single Executable Applications. Please upgrade your version of Node.js.`);
}
/** Make sure that the input string has escaped backwards slashes
 * - but never double-escaped backwards slashes.
 */
function escapeMaybe(input) {
    const result = input.split(path_1.default.sep).join('\\\\');
    if (result.includes('\\\\\\\\')) {
        throw new Error(`Your passed input ${input} contains escaped slashes. Please do not escape them`);
    }
    return result;
}
