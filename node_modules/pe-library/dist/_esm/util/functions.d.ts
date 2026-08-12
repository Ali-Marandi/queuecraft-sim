/// <reference lib="dom" />
export declare function cloneObject<T extends object>(object: Readonly<T>): T;
export declare function cloneObject<T extends object>(object: T): T;
export declare function createDataView(bin: ArrayBuffer | ArrayBufferView, byteOffset?: number, byteLength?: number): DataView;
export declare function calculateCheckSumForPE(bin: ArrayBuffer, storeToBinary?: boolean): number;
export declare function roundUp(val: number, align: number): number;
export declare function copyBuffer(dest: ArrayBuffer | ArrayBufferView, destOffset: number, src: ArrayBuffer | ArrayBufferView, srcOffset: number, length: number): void;
export declare function allocatePartialBinary(binBase: ArrayBuffer | ArrayBufferView, offset: number, length: number): ArrayBuffer;
export declare function cloneToArrayBuffer(binBase: ArrayBuffer | ArrayBufferView): ArrayBuffer;
export declare function getFixedString(view: DataView, offset: number, length: number): string;
export declare function setFixedString(view: DataView, offset: number, length: number, text: string): void;
export declare function binaryToString(bin: ArrayBuffer | ArrayBufferView): string;
export declare function stringToBinary(string: string): ArrayBuffer;
