// To make the binary (DOS_STUB_PROGRAM):
// $ cd tools/dos-stub
// $ nasm -f bin -o dos-stub.bin dos-stub.asm
// $ node -e "console.log([].map.call(fs.readFileSync('tools/dos-stub/dos-stub.bin'), (v)=>`0x${Buffer.from([v]).toString('hex')}`).join(','))"
//
// NOTE: the original dos-stub.asm program and the bit code in DOS_STUB_PROGRAM are under the 0-BSD license.
import ImageDataDirectoryArray from '../format/ImageDataDirectoryArray.js';
import ImageDosHeader from '../format/ImageDosHeader.js';
import ImageFileHeader from '../format/ImageFileHeader.js';
import ImageNtHeaders from '../format/ImageNtHeaders.js';
import ImageOptionalHeader from '../format/ImageOptionalHeader.js';
import ImageOptionalHeader64 from '../format/ImageOptionalHeader64.js';
import { copyBuffer, roundUp } from './functions.js';
// fill with '0x00' to make 8-bytes alignment
// prettier-ignore
var DOS_STUB_PROGRAM = new Uint8Array([
    0x0e, 0x1f, 0xba, 0x0e, 0x00, 0xb4, 0x09, 0xcd, 0x21, 0xb8, 0x01, 0x4c, 0xcd, 0x21, 0x44, 0x4f,
    0x53, 0x20, 0x6d, 0x6f, 0x64, 0x65, 0x20, 0x6e, 0x6f, 0x74, 0x20, 0x73, 0x75, 0x70, 0x70, 0x6f,
    0x72, 0x74, 0x65, 0x64, 0x2e, 0x0d, 0x0d, 0x0a, 0x24, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
]);
var DOS_STUB_SIZE = roundUp(ImageDosHeader.size + DOS_STUB_PROGRAM.length, 0x80);
var DEFAULT_FILE_ALIGNMENT = 512;
export function getDosStubDataSize() {
    return DOS_STUB_SIZE;
}
export function fillDosStubData(bin) {
    var dos = ImageDosHeader.from(bin);
    dos.magic = ImageDosHeader.DEFAULT_MAGIC;
    // last page size
    dos.lastPageSize = DOS_STUB_SIZE % 512;
    // total page count
    dos.pages = Math.ceil(DOS_STUB_SIZE / 512);
    // no relocations
    dos.relocations = 0;
    // header size as paragraph count (1 paragraph = 16 bytes)
    dos.headerSizeInParagraph = Math.ceil(ImageDosHeader.size / 16);
    dos.minAllocParagraphs = 0;
    dos.maxAllocParagraphs = 0xffff;
    dos.initialSS = 0;
    dos.initialSP = 0x80;
    // (no relocations, but set offset after the header)
    dos.relocationTableAddress = ImageDosHeader.size;
    dos.newHeaderAddress = DOS_STUB_SIZE;
    copyBuffer(bin, ImageDosHeader.size, DOS_STUB_PROGRAM, 0, DOS_STUB_PROGRAM.length);
}
export function estimateNewHeaderSize(is32Bit) {
    return (
    // magic
    4 +
        ImageFileHeader.size +
        (is32Bit ? ImageOptionalHeader.size : ImageOptionalHeader64.size) +
        ImageDataDirectoryArray.size);
}
export function fillPeHeaderEmptyData(bin, offset, totalBinSize, is32Bit, isDLL) {
    var _bin;
    var _offset;
    if ('buffer' in bin) {
        _bin = bin.buffer;
        _offset = bin.byteOffset + offset;
    }
    else {
        _bin = bin;
        _offset = offset;
    }
    new DataView(_bin, _offset).setUint32(0, ImageNtHeaders.DEFAULT_SIGNATURE, true);
    var fh = ImageFileHeader.from(_bin, _offset + 4);
    fh.machine = is32Bit ? 0x14c : 0x8664;
    fh.numberOfSections = 0; // no sections
    fh.timeDateStamp = 0;
    fh.pointerToSymbolTable = 0;
    fh.numberOfSymbols = 0;
    fh.sizeOfOptionalHeader =
        (is32Bit ? ImageOptionalHeader.size : ImageOptionalHeader64.size) +
            ImageDataDirectoryArray.size;
    fh.characteristics = isDLL ? 0x2102 : 0x102;
    var oh = (is32Bit ? ImageOptionalHeader : ImageOptionalHeader64).from(_bin, _offset + 4 + ImageFileHeader.size);
    oh.magic = is32Bit
        ? ImageOptionalHeader.DEFAULT_MAGIC
        : ImageOptionalHeader64.DEFAULT_MAGIC;
    // oh.majorLinkerVersion = 0;
    // oh.minorLinkerVersion = 0;
    oh.sizeOfCode = 0;
    oh.sizeOfInitializedData = 0;
    oh.sizeOfUninitializedData = 0;
    oh.addressOfEntryPoint = 0;
    oh.baseOfCode = 0x1000;
    // oh.baseOfData = 0; // for 32bit only
    oh.imageBase = is32Bit ? 0x1000000 : 0x180000000;
    oh.sectionAlignment = 4096;
    oh.fileAlignment = DEFAULT_FILE_ALIGNMENT;
    oh.majorOperatingSystemVersion = 6;
    oh.minorOperatingSystemVersion = 0;
    // oh.majorImageVersion = 0;
    // oh.minorImageVersion = 0;
    oh.majorSubsystemVersion = 6;
    oh.minorSubsystemVersion = 0;
    // oh.win32VersionValue = 0;
    oh.sizeOfHeaders = roundUp(totalBinSize, oh.fileAlignment);
    // oh.checkSum = 0;
    oh.subsystem = 2; // IMAGE_SUBSYSTEM_WINDOWS_GUI
    oh.dllCharacteristics =
        (is32Bit ? 0 : 0x20) + // IMAGE_DLL_CHARACTERISTICS_HIGH_ENTROPY_VA
            0x40 + // IMAGE_DLLCHARACTERISTICS_DYNAMIC_BASE
            0x100; // IMAGE_DLLCHARACTERISTICS_NX_COMPAT
    oh.sizeOfStackReserve = 0x100000;
    oh.sizeOfStackCommit = 0x1000;
    oh.sizeOfHeapReserve = 0x100000;
    oh.sizeOfHeapCommit = 0x1000;
    // oh.loaderFlags = 0;
    oh.numberOfRvaAndSizes =
        ImageDataDirectoryArray.size / ImageDataDirectoryArray.itemSize;
}
export function makeEmptyNtExecutableBinary(is32Bit, isDLL) {
    var bufferSize = roundUp(DOS_STUB_SIZE + estimateNewHeaderSize(is32Bit), DEFAULT_FILE_ALIGNMENT);
    var bin = new ArrayBuffer(bufferSize);
    fillDosStubData(bin);
    fillPeHeaderEmptyData(bin, DOS_STUB_SIZE, bufferSize, is32Bit, isDLL);
    return bin;
}
