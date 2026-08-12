import FormatBase from './FormatBase.js';
import ImageFileHeader from './ImageFileHeader.js';
import ImageOptionalHeader from './ImageOptionalHeader.js';
import ImageOptionalHeader64 from './ImageOptionalHeader64.js';
import ImageDataDirectoryArray from './ImageDataDirectoryArray.js';
export default class ImageNtHeaders extends FormatBase {
    static readonly DEFAULT_SIGNATURE = 17744;
    private constructor();
    static from(bin: ArrayBuffer | ArrayBufferView, offset?: number): ImageNtHeaders;
    isValid(): boolean;
    is32bit(): boolean;
    get signature(): number;
    set signature(val: number);
    get fileHeader(): ImageFileHeader;
    get optionalHeader(): ImageOptionalHeader | ImageOptionalHeader64;
    get optionalHeaderDataDirectory(): ImageDataDirectoryArray;
    getDataDirectoryOffset(): number;
    getSectionHeaderOffset(): number;
}
