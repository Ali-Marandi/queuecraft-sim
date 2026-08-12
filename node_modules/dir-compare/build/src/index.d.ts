import { Options, Result, FileCompareHandlers, FilterHandlers, CompareNameHandlers } from './types';
export * from './types';
/**
 * Synchronously compares given paths.
 * @param path1 Left file or directory to be compared.
 * @param path2 Right file or directory to be compared.
 * @param options Comparison options.
 */
export declare function compareSync(path1: string, path2: string, options?: Options): Result;
/**
 * Asynchronously compares given paths.
 * @param path1 Left file or directory to be compared.
 * @param path2 Right file or directory to be compared.
 * @param extOptions Comparison options.
 */
export declare function compare(path1: string, path2: string, options?: Options): Promise<Result>;
/**
 * List of {@link CompareFileHandler}s included with dir-compare.
 *
 * See [File content comparators](https://github.com/gliviu/dir-compare#file-content-comparators) for details.
 */
export declare const fileCompareHandlers: FileCompareHandlers;
/**
 * List of {@link CompareNameHandler}s included with dir-compare.
 *
 * See [Name comparators](https://github.com/gliviu/dir-compare#name-comparators) for details.
 */
export declare const compareNameHandlers: CompareNameHandlers;
/**
 * List of {@link FilterHandler}s included with dir-compare.
 *
 * See [Glob filter](https://github.com/gliviu/dir-compare#glob-filter) for details.
 */
export declare const filterHandlers: FilterHandlers;
//# sourceMappingURL=index.d.ts.map