import NtExecutable from './NtExecutable.js';
import { ImageSectionHeader } from './format/ImageSectionHeaderArray.js';
import ResourceEntry from './type/ResourceEntry.js';
/** Manages resource data for NtExecutable */
export default class NtExecutableResource {
    /** The timestamp for resource */
    dateTime: number;
    /** The major version data for resource */
    majorVersion: number;
    /** The minor version data for resource */
    minorVersion: number;
    /** Resource entries */
    entries: ResourceEntry[];
    /**
     * The section data header of resource data (used by outputResource method).
     * This instance will be null if the base executable does not contain resource data.
     * You can override this field before calling outputResource method.
     * (Note that the addresses and sizes are ignored for output)
     */
    sectionDataHeader: ImageSectionHeader | null;
    private originalSize;
    private constructor();
    private parse;
    /**
     * Parses resource data for `NtExecutable`.
     * This function returns valid instance even if
     * the executable does not have resource data.
     * @param exe `NtExecutable` instance
     * @param ignoreUnparsableData (default: false) specify true if skipping 'unparsable' (e.g. unusual format) data.
     *   When true, the resource data may break on write operation.
     */
    static from(exe: NtExecutable, ignoreUnparsableData?: boolean): NtExecutableResource;
    /**
     * Add or replace the resource entry.
     * This method replaces the entry only if there is an entry with `type`, `id` and `lang` equal.
     */
    replaceResourceEntry(entry: ResourceEntry): void;
    /**
     * Returns all resource entries, which has specified type and id, as UTF-8 string data.
     * @param type Resource type
     * @param id Resource id
     * @returns an array of lang and value pair (tuple)
     */
    getResourceEntriesAsString(type: string | number, id: string | number): Array<[lang: string | number, value: string]>;
    /**
     * Add or replace the resource entry with UTF-8 string data.
     * This method is a wrapper of {@link NtExecutableResource.replaceResourceEntry}.
     */
    replaceResourceEntryFromString(type: string | number, id: string | number, lang: string | number, value: string): void;
    /**
     * Removes resource entries which has specified type and id.
     */
    removeResourceEntry(type: string | number, id: string | number, lang?: string | number): void;
    /**
     * Generates resource data binary for NtExecutable (not for .res file)
     * @param virtualAddress The virtual address for the section
     * @param alignment File alignment value of executable
     * @param noGrow Set true to disallow growing resource section (throw errors if data exceeds)
     * @param allowShrink Set true to allow shrinking resource section (if the data size is less than original)
     */
    generateResourceData(virtualAddress: number, alignment: number, noGrow?: boolean, allowShrink?: boolean): {
        bin: ArrayBuffer;
        rawSize: number;
        dataOffset: number;
        descEntryOffset: number;
        descEntryCount: number;
    };
    /**
     * Writes holding resource data to specified NtExecutable instance.
     * @param exeDest An NtExecutable instance to write resource section to
     * @param noGrow Set true to disallow growing resource section (throw errors if data exceeds)
     * @param allowShrink Set true to allow shrinking resource section (if the data size is less than original)
     */
    outputResource(exeDest: NtExecutable, noGrow?: boolean, allowShrink?: boolean): void;
}
