import ArrayFormatBase from './ArrayFormatBase.js';
export interface ImageDataDirectory {
    virtualAddress: number;
    size: number;
}
export default class ImageDataDirectoryArray extends ArrayFormatBase<ImageDataDirectory> {
    static readonly size = 128;
    static readonly itemSize = 8;
    readonly length = 16;
    private constructor();
    /** @note This does not clone binary data; the changes to the array will modify the specified buffer `bin` */
    static from(bin: ArrayBuffer, offset?: number): ImageDataDirectoryArray;
    get(index: number): Readonly<ImageDataDirectory>;
    set(index: number, data: ImageDataDirectory): void;
    findIndexByVirtualAddress(virtualAddress: number): number | null;
}
