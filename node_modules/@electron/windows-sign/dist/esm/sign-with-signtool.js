import path from 'path';
import { log } from './utils/log';
import { spawnPromise } from './spawn';
import { getDirname } from 'cross-dirname';
const DIRNAME = getDirname();
function getSigntoolArgs(options) {
    // See the following url for docs
    // https://learn.microsoft.com/en-us/dotnet/framework/tools/signtool-exe
    const { certificateFile, certificatePassword, hash, timestampServer } = options;
    const args = ['sign'];
    // Automatically select cert
    if (options.automaticallySelectCertificate) {
        args.push('/a');
    }
    // Dual-sign
    if (options.appendSignature) {
        args.push('/as');
    }
    // Timestamp
    if (hash === "sha256" /* HASHES.sha256 */) {
        args.push('/tr', timestampServer);
        args.push('/td', hash);
    }
    else {
        args.push('/t', timestampServer);
    }
    // Certificate file
    if (certificateFile) {
        args.push('/f', path.resolve(certificateFile));
    }
    // Certificate password
    if (certificatePassword) {
        args.push('/p', certificatePassword);
    }
    // Hash
    args.push('/fd', hash);
    // Description
    if (options.description) {
        args.push('/d', options.description);
    }
    // Website
    if (options.website) {
        args.push('/du', options.website);
    }
    // Debug
    if (options.debug) {
        args.push('/debug');
    }
    if (options.signWithParams) {
        const extraArgs = [];
        if (Array.isArray(options.signWithParams)) {
            extraArgs.push(...options.signWithParams);
        }
        else {
            // Split up at spaces and doublequotes
            extraArgs.push(...options.signWithParams.match(/(?:[^\s"]+|"[^"]*")+/g));
        }
        log('Parsed signWithParams as:', extraArgs);
        args.push(...extraArgs);
    }
    return args;
}
async function execute(options) {
    const { signToolPath, files } = options;
    const args = getSigntoolArgs(options);
    log('Executing signtool with args', { args, files });
    const { code, stderr, stdout } = await spawnPromise(signToolPath, [...args, ...files], {
        env: process.env,
        cwd: process.cwd()
    });
    if (code !== 0) {
        throw new Error(`Signtool exited with code ${code}. Stderr: ${stderr}. Stdout: ${stdout}`);
    }
}
export async function signWithSignTool(options) {
    const certificatePassword = options.certificatePassword || process.env.WINDOWS_CERTIFICATE_PASSWORD;
    const certificateFile = options.certificateFile || process.env.WINDOWS_CERTIFICATE_FILE;
    const signWithParams = options.signWithParams || process.env.WINDOWS_SIGN_WITH_PARAMS;
    const timestampServer = options.timestampServer || process.env.WINDOWS_TIMESTAMP_SERVER || 'http://timestamp.digicert.com';
    const signToolPath = options.signToolPath || process.env.WINDOWS_SIGNTOOL_PATH || path.join(DIRNAME, '../../vendor/signtool.exe');
    const description = options.description || process.env.WINDOWS_SIGN_DESCRIPTION;
    const website = options.website || process.env.WINDOWS_SIGN_WEBSITE;
    if (!certificateFile && !(signWithParams || signToolPath)) {
        throw new Error('You must provide a certificateFile and a signToolPath or signing parameters');
    }
    if (!signToolPath && !signWithParams && !certificatePassword) {
        throw new Error('You must provide a certificatePassword or signing parameters');
    }
    const internalOptions = {
        appendSignature: false,
        ...options,
        certificateFile,
        certificatePassword,
        signWithParams,
        signToolPath,
        description,
        timestampServer,
        website
    };
    const hashes = options.hashes == null || options.hashes.length === 0
        ? ["sha1" /* HASHES.sha1 */, "sha256" /* HASHES.sha256 */]
        : options.hashes;
    if (hashes.includes("sha1" /* HASHES.sha1 */)) {
        await execute({ ...internalOptions, hash: "sha1" /* HASHES.sha1 */ });
        // If we signed with SHA1, we need to append the SHA256 signature:
        internalOptions.appendSignature = true;
    }
    if (hashes.includes("sha256" /* HASHES.sha256 */)) {
        await execute({ ...internalOptions, hash: "sha256" /* HASHES.sha256 */ });
    }
}
