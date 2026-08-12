import FormatBase from './FormatBase.js';
/** abstract class that support array-like methods and 'for...of' operation */
declare abstract class ArrayFormatBase<T> extends FormatBase {
    protected constructor(view: DataView);
    abstract readonly length: number;
    abstract get(index: number): Readonly<T>;
    abstract set(index: number, data: T): void;
    forEach(callback: (value: T, index: number, base: this) => void): void;
    _iterator(): Iterator<Readonly<T>>;
}
interface ArrayFormatBase<T> {
    [Symbol.iterator]: () => Iterator<Readonly<T>>;
}
export default ArrayFormatBase;
