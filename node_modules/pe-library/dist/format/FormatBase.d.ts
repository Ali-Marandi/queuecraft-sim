export default abstract class FormatBase {
    protected readonly view: DataView;
    protected constructor(view: DataView);
    copyTo(bin: ArrayBuffer, offset: number): void;
    get byteLength(): number;
}
