export declare function getDosStubDataSize(): number;
export declare function fillDosStubData(bin: ArrayBuffer | ArrayBufferView): void;
export declare function estimateNewHeaderSize(is32Bit: boolean): number;
export declare function fillPeHeaderEmptyData(bin: ArrayBuffer | ArrayBufferView, offset: number, totalBinSize: number, is32Bit: boolean, isDLL: boolean): void;
export declare function makeEmptyNtExecutableBinary(is32Bit: boolean, isDLL: boolean): ArrayBuffer;
