import { SignOptions } from './types';
/**
 * Recursively goes through an entire directory and returns an array
 * of full paths for files ot sign.
 *
 * - Portable executable files (.exe, .dll, .sys, .efi, .scr, .node)
 * - Microsoft installers (.msi)
 * - APPX/MSIX packages (.appx, .appxbundle, .msix, .msixbundle)
 * - Catalog files (.cat)
 * - Cabinet files (.cab)
 * - Silverlight applications (.xap)
 * - Scripts (.vbs, .wsf, .ps1)
 * If configured:
 * - JavaScript files (.js)
 */
export declare function getFilesToSign(options: SignOptions, dir?: string): Array<string>;
