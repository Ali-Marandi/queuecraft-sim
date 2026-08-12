import ArrayFormatBase from './ArrayFormatBase.js';
export interface ImageSectionHeader {
    name: string;
    virtualSize: number;
    virtualAddress: number;
    sizeOfRawData: number;
    pointerToRawData: number;
    pointerToRelocations: number;
    pointerToLineNumbers: number;
    numberOfRelocations: number;
    numberOfLineNumbers: number;
    characteristics: number;
}
export default class ImageSectionHeaderArray extends ArrayFormatBase<ImageSectionHeader> {
    readonly length: number;
    static readonly itemSize = 40;
    private constructor();
    static from(bin: ArrayBuffer, length: number, offset?: number): ImageSectionHeaderArray;
    get(index: number): Readonly<ImageSectionHeader>;
    set(index: number, data: ImageSectionHeader): void;
}
