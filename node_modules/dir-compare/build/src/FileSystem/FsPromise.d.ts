/// <reference types="node" />
type BytesRead = number;
export declare const FsPromise: {
    readdir(path: string): Promise<string[]>;
    read(fd: number, buffer: Buffer, offset: number, length: number, position: number | null): Promise<BytesRead>;
};
export {};
//# sourceMappingURL=FsPromise.d.ts.map