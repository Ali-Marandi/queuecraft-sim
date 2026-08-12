import ImageDataDirectoryArray from './format/ImageDataDirectoryArray.js';
import ImageDirectoryEntry from './format/ImageDirectoryEntry.js';
import ImageDosHeader from './format/ImageDosHeader.js';
import ImageNtHeaders from './format/ImageNtHeaders.js';
import ImageSectionHeaderArray from './format/ImageSectionHeaderArray.js';
import { allocatePartialBinary, calculateCheckSumForPE, cloneObject, cloneToArrayBuffer, roundUp, } from './util/functions.js';
import { makeEmptyNtExecutableBinary } from './util/generate.js';
var NtExecutable = /** @class */ (function () {
    function NtExecutable(_headers, _sections, _ex) {
        this._headers = _headers;
        this._sections = _sections;
        this._ex = _ex;
        var dh = ImageDosHeader.from(_headers);
        var nh = ImageNtHeaders.from(_headers, dh.newHeaderAddress);
        this._dh = dh;
        this._nh = nh;
        this._dda = nh.optionalHeaderDataDirectory;
        _sections.sort(function (a, b) {
            var ra = a.info.pointerToRawData;
            var rb = a.info.pointerToRawData;
            if (ra !== rb) {
                return ra - rb;
            }
            var va = a.info.virtualAddress;
            var vb = b.info.virtualAddress;
            if (va === vb) {
                return a.info.virtualSize - b.info.virtualSize;
            }
            return va - vb;
        });
    }
    /**
     * Creates an NtExecutable instance with an 'empty' executable binary.
     * @param is32Bit set true if the binary is for 32-bit (default: false)
     * @param isDLL set true if the binary is DLL (default: true)
     * @return NtExecutable instance
     */
    NtExecutable.createEmpty = function (is32Bit, isDLL) {
        if (is32Bit === void 0) { is32Bit = false; }
        if (isDLL === void 0) { isDLL = true; }
        return this.from(makeEmptyNtExecutableBinary(is32Bit, isDLL));
    };
    /**
     * Parse the binary and create NtExecutable instance.
     * An error will be thrown if the binary data is invalid
     * @param bin binary data
     * @param options additional option for parsing
     * @return NtExecutable instance
     */
    NtExecutable.from = function (bin, options) {
        var dh = ImageDosHeader.from(bin);
        var nh = ImageNtHeaders.from(bin, dh.newHeaderAddress);
        if (!dh.isValid() || !nh.isValid()) {
            throw new TypeError('Invalid binary format');
        }
        if (nh.fileHeader.numberOfSymbols > 0) {
            throw new Error('Binary with symbols is not supported now');
        }
        var fileAlignment = nh.optionalHeader.fileAlignment;
        var securityEntry = nh.optionalHeaderDataDirectory.get(ImageDirectoryEntry.Certificate);
        if (securityEntry.size > 0) {
            // Signed executables should be parsed only when `ignoreCert` is true
            if (!(options === null || options === void 0 ? void 0 : options.ignoreCert)) {
                throw new Error('Parsing signed executable binary is not allowed by default.');
            }
        }
        var secOff = dh.newHeaderAddress + nh.getSectionHeaderOffset();
        var secCount = nh.fileHeader.numberOfSections;
        var sections = [];
        var tempSectionHeaderBinary = allocatePartialBinary(bin, secOff, secCount * ImageSectionHeaderArray.itemSize);
        var secArray = ImageSectionHeaderArray.from(tempSectionHeaderBinary, secCount, 0);
        var lastOffset = roundUp(secOff + secCount * ImageSectionHeaderArray.itemSize, fileAlignment);
        // console.log(`from data size 0x${bin.byteLength.toString(16)}:`);
        secArray.forEach(function (info) {
            if (!info.pointerToRawData || !info.sizeOfRawData) {
                info.pointerToRawData = 0;
                info.sizeOfRawData = 0;
                sections.push({
                    info: info,
                    data: null,
                });
            }
            else {
                // console.log(`  section ${info.name}: 0x${info.pointerToRawData.toString(16)}, size = 0x${info.sizeOfRawData.toString(16)}`);
                var secBin = allocatePartialBinary(bin, info.pointerToRawData, info.sizeOfRawData);
                sections.push({
                    info: info,
                    data: secBin,
                });
                var secEndOffset = roundUp(info.pointerToRawData + info.sizeOfRawData, fileAlignment);
                if (secEndOffset > lastOffset) {
                    lastOffset = secEndOffset;
                }
            }
        });
        // the size of DOS and NT headers is equal to section offset
        var headers = allocatePartialBinary(bin, 0, secOff);
        // extra data
        var exData = null;
        var lastExDataOffset = bin.byteLength;
        // It may contain that both extra data and certificate data are available.
        // In this case the extra data is followed by the certificate data.
        if (securityEntry.size > 0) {
            lastExDataOffset = securityEntry.virtualAddress;
        }
        if (lastOffset < lastExDataOffset) {
            exData = allocatePartialBinary(bin, lastOffset, lastExDataOffset - lastOffset);
        }
        return new NtExecutable(headers, sections, exData);
    };
    /**
     * Returns whether the executable is for 32-bit architecture
     */
    NtExecutable.prototype.is32bit = function () {
        return this._nh.is32bit();
    };
    NtExecutable.prototype.getTotalHeaderSize = function () {
        return this._headers.byteLength;
    };
    Object.defineProperty(NtExecutable.prototype, "dosHeader", {
        get: function () {
            return this._dh;
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(NtExecutable.prototype, "newHeader", {
        get: function () {
            return this._nh;
        },
        enumerable: false,
        configurable: true
    });
    NtExecutable.prototype.getRawHeader = function () {
        return this._headers;
    };
    NtExecutable.prototype.getImageBase = function () {
        return this._nh.optionalHeader.imageBase;
    };
    NtExecutable.prototype.getFileAlignment = function () {
        return this._nh.optionalHeader.fileAlignment;
    };
    NtExecutable.prototype.getSectionAlignment = function () {
        return this._nh.optionalHeader.sectionAlignment;
    };
    /**
     * Return all sections. The returned array is sorted by raw address.
     */
    NtExecutable.prototype.getAllSections = function () {
        return this._sections;
    };
    /**
     * Return the section data from ImageDirectoryEntry enum value.
     * @note
     * The returned instance is equal to the value in {@link getAllSections}'s return value.
     */
    NtExecutable.prototype.getSectionByEntry = function (entry) {
        var dd = this._dda.get(entry);
        var r = this._sections
            .filter(function (sec) {
            var vaEnd = sec.info.virtualAddress + sec.info.virtualSize;
            return (dd.virtualAddress >= sec.info.virtualAddress &&
                dd.virtualAddress < vaEnd);
        })
            .shift();
        return r !== undefined ? r : null;
    };
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
    NtExecutable.prototype.setSectionByEntry = function (entry, section) {
        var sec = section
            ? { data: section.data, info: section.info }
            : null;
        var dd = this._dda.get(entry);
        var hasEntry = dd.size > 0;
        if (!sec) {
            if (!hasEntry) {
                // no need to replace
            }
            else {
                // clear entry
                this._dda.set(entry, { size: 0, virtualAddress: 0 });
                var len = this._sections.length;
                for (var i = 0; i < len; ++i) {
                    var sec_1 = this._sections[i];
                    var vaStart = sec_1.info.virtualAddress;
                    var vaLast = vaStart + sec_1.info.virtualSize;
                    if (dd.virtualAddress >= vaStart &&
                        dd.virtualAddress < vaLast) {
                        this._sections.splice(i, 1);
                        // section count changed
                        this._nh.fileHeader.numberOfSections =
                            this._sections.length;
                        break;
                    }
                }
            }
        }
        else {
            var rawSize = !sec.data ? 0 : sec.data.byteLength;
            var fileAlign = this._nh.optionalHeader.fileAlignment;
            var secAlign = this._nh.optionalHeader.sectionAlignment;
            var alignedFileSize = !sec.data ? 0 : roundUp(rawSize, fileAlign);
            var alignedSecSize = !sec.data
                ? 0
                : roundUp(sec.info.virtualSize, secAlign);
            if (sec.info.sizeOfRawData < alignedFileSize) {
                sec.info.sizeOfRawData = alignedFileSize;
            }
            else {
                alignedFileSize = sec.info.sizeOfRawData;
            }
            if (!hasEntry) {
                var virtAddr_1 = 0;
                var rawAddr_1 = roundUp(this._headers.byteLength, fileAlign);
                // get largest addresses
                this._sections.forEach(function (secExist) {
                    if (secExist.info.pointerToRawData) {
                        if (rawAddr_1 <= secExist.info.pointerToRawData) {
                            rawAddr_1 =
                                secExist.info.pointerToRawData +
                                    secExist.info.sizeOfRawData;
                        }
                    }
                    if (virtAddr_1 <= secExist.info.virtualAddress) {
                        virtAddr_1 =
                            secExist.info.virtualAddress +
                                secExist.info.virtualSize;
                    }
                });
                if (!alignedFileSize) {
                    rawAddr_1 = 0;
                }
                if (!virtAddr_1) {
                    virtAddr_1 = this.newHeader.optionalHeader.baseOfCode;
                }
                virtAddr_1 = roundUp(virtAddr_1, secAlign);
                sec.info.pointerToRawData = rawAddr_1;
                sec.info.virtualAddress = virtAddr_1;
                // add entry
                this._dda.set(entry, {
                    size: rawSize,
                    virtualAddress: virtAddr_1,
                });
                this._sections.push(sec);
                // section count changed
                this._nh.fileHeader.numberOfSections = this._sections.length;
                // change image size
                this._nh.optionalHeader.sizeOfImage = roundUp(virtAddr_1 + alignedSecSize, this._nh.optionalHeader.sectionAlignment);
            }
            else {
                // replace entry
                this.replaceSectionImpl(dd.virtualAddress, sec.info, sec.data);
            }
        }
    };
    /**
     * Returns the extra data in the executable, or `null` if nothing.
     * You can rewrite the returned buffer without using `setExtraData` if
     * the size of the new data is equal to the old data.
     */
    NtExecutable.prototype.getExtraData = function () {
        return this._ex;
    };
    /**
     * Specifies the new extra data in the executable.
     * The specified buffer will be cloned and you can release it after calling this method.
     * @param bin buffer containing the new data
     * @note
     * The extra data will not be aligned by `NtExecutable`.
     */
    NtExecutable.prototype.setExtraData = function (bin) {
        if (bin === null) {
            this._ex = null;
        }
        else {
            this._ex = cloneToArrayBuffer(bin);
        }
    };
    /**
     * Generates the executable binary data.
     */
    NtExecutable.prototype.generate = function (paddingSize) {
        // calculate binary size
        var dh = this._dh;
        var nh = this._nh;
        var secOff = dh.newHeaderAddress + nh.getSectionHeaderOffset();
        var size = secOff;
        size += this._sections.length * ImageSectionHeaderArray.itemSize;
        var align = nh.optionalHeader.fileAlignment;
        size = roundUp(size, align);
        this._sections.forEach(function (sec) {
            if (!sec.info.pointerToRawData) {
                return;
            }
            var lastOff = sec.info.pointerToRawData + sec.info.sizeOfRawData;
            if (size < lastOff) {
                size = lastOff;
                size = roundUp(size, align);
            }
        });
        var lastPosition = size;
        if (this._ex !== null) {
            size += this._ex.byteLength;
        }
        if (typeof paddingSize === 'number') {
            size += paddingSize;
        }
        // make buffer
        var bin = new ArrayBuffer(size);
        var u8bin = new Uint8Array(bin);
        u8bin.set(new Uint8Array(this._headers, 0, secOff));
        // reset Security section offset (eliminate it)
        ImageDataDirectoryArray.from(bin, dh.newHeaderAddress + nh.getDataDirectoryOffset()).set(ImageDirectoryEntry.Certificate, {
            size: 0,
            virtualAddress: 0,
        });
        var secArray = ImageSectionHeaderArray.from(bin, this._sections.length, secOff);
        this._sections.forEach(function (sec, i) {
            if (!sec.data) {
                sec.info.pointerToRawData = 0;
                sec.info.sizeOfRawData = 0;
            }
            secArray.set(i, sec.info);
            if (!sec.data || !sec.info.pointerToRawData) {
                return;
            }
            u8bin.set(new Uint8Array(sec.data), sec.info.pointerToRawData);
        });
        if (this._ex !== null) {
            u8bin.set(new Uint8Array(this._ex), lastPosition);
        }
        // re-calc checksum
        if (nh.optionalHeader.checkSum !== 0) {
            calculateCheckSumForPE(bin, true);
        }
        return bin;
    };
    NtExecutable.prototype.rearrangeSections = function (rawAddressStart, rawDiff, virtualAddressStart, virtualDiff) {
        if (!rawDiff && !virtualDiff) {
            return;
        }
        var nh = this._nh;
        var secAlign = nh.optionalHeader.sectionAlignment;
        var dirs = this._dda;
        var len = this._sections.length;
        var lastVirtAddress = 0;
        for (var i = 0; i < len; ++i) {
            var sec = this._sections[i];
            var virtAddr = sec.info.virtualAddress;
            if (virtualDiff && virtAddr >= virtualAddressStart) {
                var iDir = dirs.findIndexByVirtualAddress(virtAddr);
                virtAddr += virtualDiff;
                if (iDir !== null) {
                    dirs.set(iDir, {
                        virtualAddress: virtAddr,
                        size: sec.info.virtualSize,
                    });
                }
                sec.info.virtualAddress = virtAddr;
            }
            var fileAddr = sec.info.pointerToRawData;
            if (rawDiff && fileAddr >= rawAddressStart) {
                sec.info.pointerToRawData = fileAddr + rawDiff;
            }
            lastVirtAddress = roundUp(sec.info.virtualAddress + sec.info.virtualSize, secAlign);
        }
        // fix image size from last virtual address
        nh.optionalHeader.sizeOfImage = lastVirtAddress;
    };
    // NOTE: info.virtualSize must be valid
    NtExecutable.prototype.replaceSectionImpl = function (virtualAddress, info, data) {
        var len = this._sections.length;
        for (var i = 0; i < len; ++i) {
            var s = this._sections[i];
            // console.log(`replaceSectionImpl: ${virtualAddress} <--> ${s.info.virtualAddress}`);
            if (s.info.virtualAddress === virtualAddress) {
                // console.log(`  found`);
                var secAlign = this._nh.optionalHeader.sectionAlignment;
                var fileAddr = s.info.pointerToRawData;
                var oldFileAddr = fileAddr + s.info.sizeOfRawData;
                var oldVirtAddr = virtualAddress + roundUp(s.info.virtualSize, secAlign);
                s.info = cloneObject(info);
                s.info.virtualAddress = virtualAddress;
                s.info.pointerToRawData = fileAddr;
                s.data = data;
                // shift addresses
                var newFileAddr = fileAddr + info.sizeOfRawData;
                var newVirtAddr = virtualAddress + roundUp(info.virtualSize, secAlign);
                this.rearrangeSections(oldFileAddr, newFileAddr - oldFileAddr, oldVirtAddr, newVirtAddr - oldVirtAddr);
                // BLOCK: rewrite DataDirectory entry for specified virtualAddress
                {
                    var dirs = this._dda;
                    var iDir = dirs.findIndexByVirtualAddress(virtualAddress);
                    if (iDir !== null) {
                        dirs.set(iDir, {
                            virtualAddress: virtualAddress,
                            size: info.virtualSize,
                        });
                    }
                }
                break;
            }
        }
    };
    return NtExecutable;
}());
export default NtExecutable;
