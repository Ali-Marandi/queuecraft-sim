import ArrayFormatBase from './ArrayFormatBase.js';
import FormatBase from './FormatBase.js';
import ImageDataDirectoryArray from './ImageDataDirectoryArray.js';
import ImageDirectoryEntry from './ImageDirectoryEntry.js';
import ImageDosHeader from './ImageDosHeader.js';
import ImageFileHeader from './ImageFileHeader.js';
import ImageNtHeaders from './ImageNtHeaders.js';
import ImageOptionalHeader from './ImageOptionalHeader.js';
import ImageOptionalHeader64 from './ImageOptionalHeader64.js';
import ImageSectionHeaderArray from './ImageSectionHeaderArray.js';
export { ArrayFormatBase, FormatBase, ImageDataDirectoryArray, ImageDirectoryEntry, ImageDosHeader, ImageFileHeader, ImageNtHeaders, ImageOptionalHeader, ImageOptionalHeader64, ImageSectionHeaderArray, };
export function getImageDosHeader(bin) {
    return ImageDosHeader.from(bin);
}
export function getImageNtHeadersByDosHeader(bin, dosHeader) {
    return ImageNtHeaders.from(bin, dosHeader.newHeaderAddress);
}
export function getImageSectionHeadersByNtHeaders(bin, dosHeader, ntHeaders) {
    return ImageSectionHeaderArray.from(bin, ntHeaders.fileHeader.numberOfSections, dosHeader.newHeaderAddress + ntHeaders.byteLength);
}
export function findImageSectionBlockByDirectoryEntry(bin, dosHeader, ntHeaders, entryType) {
    var arr = ImageSectionHeaderArray.from(bin, ntHeaders.fileHeader.numberOfSections, dosHeader.newHeaderAddress + ntHeaders.byteLength);
    var len = arr.length;
    var rva = ntHeaders.optionalHeaderDataDirectory.get(entryType).virtualAddress;
    for (var i = 0; i < len; ++i) {
        var sec = arr.get(i);
        var vaEnd = sec.virtualAddress + sec.virtualSize;
        if (rva >= sec.virtualAddress && rva < vaEnd) {
            var ptr = sec.pointerToRawData;
            if (!ptr) {
                return null;
            }
            return bin.slice(ptr, ptr + sec.sizeOfRawData);
        }
        if (rva < sec.virtualAddress) {
            return null;
        }
    }
    return null;
}
