"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.findImageSectionBlockByDirectoryEntry = exports.getImageSectionHeadersByNtHeaders = exports.getImageNtHeadersByDosHeader = exports.getImageDosHeader = exports.ImageSectionHeaderArray = exports.ImageOptionalHeader64 = exports.ImageOptionalHeader = exports.ImageNtHeaders = exports.ImageFileHeader = exports.ImageDosHeader = exports.ImageDirectoryEntry = exports.ImageDataDirectoryArray = exports.FormatBase = exports.ArrayFormatBase = void 0;
var ArrayFormatBase_js_1 = require("./ArrayFormatBase.js");
exports.ArrayFormatBase = ArrayFormatBase_js_1.default;
var FormatBase_js_1 = require("./FormatBase.js");
exports.FormatBase = FormatBase_js_1.default;
var ImageDataDirectoryArray_js_1 = require("./ImageDataDirectoryArray.js");
exports.ImageDataDirectoryArray = ImageDataDirectoryArray_js_1.default;
var ImageDirectoryEntry_js_1 = require("./ImageDirectoryEntry.js");
exports.ImageDirectoryEntry = ImageDirectoryEntry_js_1.default;
var ImageDosHeader_js_1 = require("./ImageDosHeader.js");
exports.ImageDosHeader = ImageDosHeader_js_1.default;
var ImageFileHeader_js_1 = require("./ImageFileHeader.js");
exports.ImageFileHeader = ImageFileHeader_js_1.default;
var ImageNtHeaders_js_1 = require("./ImageNtHeaders.js");
exports.ImageNtHeaders = ImageNtHeaders_js_1.default;
var ImageOptionalHeader_js_1 = require("./ImageOptionalHeader.js");
exports.ImageOptionalHeader = ImageOptionalHeader_js_1.default;
var ImageOptionalHeader64_js_1 = require("./ImageOptionalHeader64.js");
exports.ImageOptionalHeader64 = ImageOptionalHeader64_js_1.default;
var ImageSectionHeaderArray_js_1 = require("./ImageSectionHeaderArray.js");
exports.ImageSectionHeaderArray = ImageSectionHeaderArray_js_1.default;
function getImageDosHeader(bin) {
    return ImageDosHeader_js_1.default.from(bin);
}
exports.getImageDosHeader = getImageDosHeader;
function getImageNtHeadersByDosHeader(bin, dosHeader) {
    return ImageNtHeaders_js_1.default.from(bin, dosHeader.newHeaderAddress);
}
exports.getImageNtHeadersByDosHeader = getImageNtHeadersByDosHeader;
function getImageSectionHeadersByNtHeaders(bin, dosHeader, ntHeaders) {
    return ImageSectionHeaderArray_js_1.default.from(bin, ntHeaders.fileHeader.numberOfSections, dosHeader.newHeaderAddress + ntHeaders.byteLength);
}
exports.getImageSectionHeadersByNtHeaders = getImageSectionHeadersByNtHeaders;
function findImageSectionBlockByDirectoryEntry(bin, dosHeader, ntHeaders, entryType) {
    var arr = ImageSectionHeaderArray_js_1.default.from(bin, ntHeaders.fileHeader.numberOfSections, dosHeader.newHeaderAddress + ntHeaders.byteLength);
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
exports.findImageSectionBlockByDirectoryEntry = findImageSectionBlockByDirectoryEntry;
