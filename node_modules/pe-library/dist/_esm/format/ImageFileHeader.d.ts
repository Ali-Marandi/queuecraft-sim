import FormatBase from './FormatBase.js';
export default class ImageFileHeader extends FormatBase {
    static readonly size = 20;
    private constructor();
    static from(bin: ArrayBuffer, offset?: number): ImageFileHeader;
    get machine(): number;
    set machine(val: number);
    get numberOfSections(): number;
    set numberOfSections(val: number);
    get timeDateStamp(): number;
    set timeDateStamp(val: number);
    get pointerToSymbolTable(): number;
    set pointerToSymbolTable(val: number);
    get numberOfSymbols(): number;
    set numberOfSymbols(val: number);
    get sizeOfOptionalHeader(): number;
    set sizeOfOptionalHeader(val: number);
    get characteristics(): number;
    set characteristics(val: number);
}
