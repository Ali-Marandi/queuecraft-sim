/**
 * SHA-1 has been deprecated on Windows since 2016. We'll still dualsign.
 * https://social.technet.microsoft.com/wiki/contents/articles/32288.windows-enforcement-of-sha1-certificates.aspx#Post-February_TwentySeventeen_Plan
 */
export declare const enum HASHES {
    sha1 = "sha1",
    sha256 = "sha256"
}
/**
 * Signing can be either by specifying a directory of files to sign.
 *
 * @category Sign
 */
export type SignOptions = SignOptionsForDirectory | SignOptionsForFiles;
/**
 * Options for signing by passing a path to a directory to be codesigned.
 *
 * @category Sign
 */
export interface SignOptionsForDirectory extends SignToolOptions {
    /**
     * Path to the application directory. We will scan this
     * directory for any `.dll`, `.exe`, `.msi`, or `.node` files and
     * codesign them with `signtool.exe`.
     */
    appDirectory: string;
}
/**
 * Options for signing by passing an array of files to be codesigned.
 *
 * @category Sign
 */
export interface SignOptionsForFiles extends SignToolOptions {
    /**
     * Array of paths to files to be codesigned with `signtool.exe`.
     */
    files: Array<string>;
}
/**
 * @category Utility
 */
export interface SignToolOptions extends OptionalSignToolOptions, OptionalHookOptions {
}
export interface InternalSignOptions extends SignOptionsForFiles {
}
export interface InternalSignToolOptions extends OptionalSignToolOptions, OptionalHookOptions {
    signToolPath: string;
    timestampServer: string;
    files: Array<string>;
    hash: HASHES;
    appendSignature?: boolean;
}
/**
 * @category Utility
 */
export interface OptionalSignToolOptions {
    /**
     * Path to a `.pfx` code signing certificate.
     * Will use `process.env.WINDOWS_CERTIFICATE_FILE` if this option is not provided.
     */
    certificateFile?: string;
    /**
     * Password to {@link certificateFile}. If you don't provide this,
     * you need to provide the {@link signWithParams} option.
     * Will use `process.env.WINDOWS_CERTIFICATE_PASSWORD` if this option is not provided.
     */
    certificatePassword?: string;
    /**
     * Path to a timestamp server.
     * Will use `process.env.WINDOWS_TIMESTAMP_SERVER` if this option is not provided.
     *
     * @defaultValue http://timestamp.digicert.com
     */
    timestampServer?: string;
    /**
     * Description of the signed content. Will be passed to `signtool.exe` as `/d`.
     */
    description?: string;
    /**
     * URL for the expanded description of the signed content. Will be passed to `signtool.exe` as `/du`.
     */
    website?: string;
    /**
     * Path to the `signtool.exe` used to sign. Will use `vendor/signtool.exe` if not provided.
     */
    signToolPath?: string;
    /**
     * Additional parameters to pass to `signtool.exe`.
     *
     * @see Microsoft's {@link https://learn.microsoft.com/en-us/dotnet/framework/tools/signtool-exe SignTool.exe documentation}
     */
    signWithParams?: string | Array<string>;
    /**
     * Enables debug logging.
     *
     * @defaultValue false
     */
    debug?: boolean;
    /**
     * Automatically selects the best signing certificate according to SignTool. Will be passed to `signtool.exe` as `/a`.
     *
     * @defaultValue true
     */
    automaticallySelectCertificate?: boolean;
    /**
     * Whether or not to sign JavaScript files.
     *
     * @defaultValue false
     */
    signJavaScript?: boolean;
    /**
     * Hash algorithms to use for signing.
     */
    hashes?: HASHES[];
}
/**
 * Custom function that is called sequentially for each file that needs to be signed.
 *
 * @param fileToSign Absolute path to the file to sign
 *
 * @category Utility
 */
export type HookFunction = (fileToSign: string) => void | Promise<void>;
/**
 * @category Utility
 */
export interface OptionalHookOptions {
    /**
     * A hook function called for each file that needs to be signed.
     * Use this for full control over your app's signing logic.
     * `@electron/windows-sign` will not attempt to sign with SignTool if a custom hook is detected.
     */
    hookFunction?: HookFunction;
    /**
     * A path to a JavaScript file, exporting a single function that will be called for each file that needs to be signed.
     * Use this for full control over your app's signing logic.
     * `@electron/windows-sign` will not attempt to sign with SignTool if a custom hook is detected.
     */
    hookModulePath?: string;
}
export interface InternalHookOptions extends OptionalHookOptions {
    files: Array<string>;
}
