import ImageDirectoryEntry from './format/ImageDirectoryEntry.js';
import ImageDosHeader from './format/ImageDosHeader.js';
import ImageNtHeaders from './format/ImageNtHeaders.js';
import { ImageSectionHeader } from './format/ImageSectionHeaderArray.js';
export interface NtExecutableFromOptions {
    /** true to parse binary even if the binary contains Certificate data (i.e. 'signed') */
    ignoreCert?: boolean;
}
export interface NtExecutableSection {
    info: ImageSectionHeader;
    data: ArrayBuffer | null;
}
export default class NtExecutable {
    private readonly _headers;
    private readonly _sections;
    private _ex;
    private readonly _dh;
    private readonly _nh;
    private readonly _dda;
    private constructor();
    /**
     * Creates an NtExecutable instance with an 'empty' executable binary.
     * @param is32Bit set true if the binary is for 32-bit (default: false)
     * @param isDLL set true if the binary is DLL (default: true)
     * @return NtExecutable instance
     */
    static createEmpty(is32Bit?: boolean, isDLL?: boolean): NtExecutable;
    /**
     * Parse the binary and create NtExecutable instance.
     * An error will be thrown if the binary data is invalid
     * @param bin binary data
     * @param options additional option for parsing
     * @return NtExecutable instance
     */
    static from(bin: ArrayBuffer | ArrayBufferView, options?: NtExecutableFromOptions): NtExecutable;
    /**
     * Returns whether the executable is for 32-bit architecture
     */
    is32bit(): boolean;
    getTotalHeaderSize(): number;
    get dosHeader(): ImageDosHeader;
    get newHeader(): ImageNtHeaders;
    getRawHeader(): ArrayBuffer;
    getImageBase(): number;
    getFileAlignment(): number;
    getSectionAlignment(): number;
    /**
     * Return all sections. The returned array is sorted by raw address.
     */
    getAllSections(): readonly NtExecutableSection[];
    /**
     * Return the section data from ImageDirectoryEntry enum value.
     * @note
     * The returned instance is equal to the value in {@link getAllSections}'s return value.
     */
    getSectionByEntry(entry: ImageDirectoryEntry): Readonly<NtExecutableSection> | null;
    /**
     * Set the section data from ImageDirectoryEntry enum value.
     * If entry is found, then replaces the secion data. If not found, then adds the section data.
     *
     * NOTE: 'virtualAddress' and 'pointerToRawData' of section object is ignored
     * and calculated automatically. 'virtualSize' and 'sizeOfRawData' are used, but
     * if the 'section.data.byteLength' is larger than 'sizeOfRawData', then
     * these members are replaced.
     *
     * @param entry ImageDirectoryEntry enum value for the section
     * @param section the section data, or null to remove the section
     */
    setSectionByEntry(entry: ImageDirectoryEntry, section: Readonly<NtExecutableSection> | null): void;
    /**
     * Returns the extra data in the executable, or `null` if nothing.
     * You can rewrite the returned buffer without using `setExtraData` if
     * the size of the new data is equal to the old data.
     */
    getExtraData(): ArrayBuffer | null;
    /**
     * Specifies the new extra data in the executable.
     * The specified buffer will be cloned and you can release it after calling this method.
     * @param bin buffer containing the new data
     * @note
     * The extra data will not be aligned by `NtExecutable`.
     */
    setExtraData(bin: ArrayBuffer | ArrayBufferView | null): void;
    /**
     * Generates the executable binary data.
     */
    generate(paddingSize?: number): ArrayBuffer;
    private rearrangeSections;
    private replaceSectionImpl;
}
