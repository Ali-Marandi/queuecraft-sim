/**
 * Tries to parse an process.env string to a boolean.
 * Will understand undefined as the default value
 * Will understand "false", "False", "fAlse", or "0" as `false`
 * Will understand everything else as true
 *
 * @export
 * @param {string} name
 * @return {*}  {boolean}
 */
export declare function booleanFromEnv(name: string): boolean | undefined;
