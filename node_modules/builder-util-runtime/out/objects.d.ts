export type Nullish = null | undefined;
type RecursiveMap = Map<any, RecursiveMap | any>;
export declare function mapToObject(map: RecursiveMap): any;
export declare function isValidKey(key: any): boolean;
export declare function asArray<T>(v: Nullish | T | Array<T>): Array<T>;
export declare function deepAssign<T>(target: T, ...objects: Array<any>): T;
export declare function objectToArgs(obj: Record<string, string | null>): readonly string[];
export {};
