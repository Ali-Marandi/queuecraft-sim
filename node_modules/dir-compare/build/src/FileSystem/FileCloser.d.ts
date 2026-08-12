import { FileDescriptorQueue } from './FileDescriptorQueue';
declare function closeFilesSync(fd1?: number, fd2?: number): void;
declare function closeFilesAsync(fd1: number | undefined, fd2: number | undefined, fdQueue: FileDescriptorQueue): Promise<void>;
export declare const FileCloser: {
    closeFilesSync: typeof closeFilesSync;
    closeFilesAsync: typeof closeFilesAsync;
};
export {};
//# sourceMappingURL=FileCloser.d.ts.map