import ImageDirectoryEntry from './format/ImageDirectoryEntry.js';
import { binaryToString, cloneObject, copyBuffer, roundUp, stringToBinary, } from './util/functions.js';
function removeDuplicates(a) {
    return a.reduce(function (p, c) {
        return p.indexOf(c) >= 0 ? p : p.concat(c);
    }, []);
}
function readString(view, offset) {
    var length = view.getUint16(offset, true);
    var r = '';
    offset += 2;
    for (var i = 0; i < length; ++i) {
        r += String.fromCharCode(view.getUint16(offset, true));
        offset += 2;
    }
    return r;
}
function readLanguageTable(view, typeEntry, name, languageTable, cb) {
    var off = languageTable;
    var nameEntry = {
        name: name,
        languageTable: languageTable,
        characteristics: view.getUint32(off, true),
        dateTime: view.getUint32(off + 4, true),
        majorVersion: view.getUint16(off + 8, true),
        minorVersion: view.getUint16(off + 10, true),
    };
    var nameCount = view.getUint16(off + 12, true);
    var idCount = view.getUint16(off + 14, true);
    off += 16;
    for (var i = 0; i < nameCount; ++i) {
        var nameOffset = view.getUint32(off, true) & 0x7fffffff;
        var dataOffset = view.getUint32(off + 4, true);
        // ignore if the offset refers to the next table
        if ((dataOffset & 0x80000000) !== 0) {
            off += 8;
            continue;
        }
        var name_1 = readString(view, nameOffset);
        cb(typeEntry, nameEntry, { lang: name_1, dataOffset: dataOffset });
        off += 8;
    }
    for (var i = 0; i < idCount; ++i) {
        var id = view.getUint32(off, true) & 0x7fffffff;
        var dataOffset = view.getUint32(off + 4, true);
        // ignore if the offset refers to the next table
        if ((dataOffset & 0x80000000) !== 0) {
            off += 8;
            continue;
        }
        cb(typeEntry, nameEntry, { lang: id, dataOffset: dataOffset });
        off += 8;
    }
}
function readNameTable(view, type, nameTable, cb) {
    var off = nameTable;
    var typeEntry = {
        type: type,
        nameTable: nameTable,
        characteristics: view.getUint32(off, true),
        dateTime: view.getUint32(off + 4, true),
        majorVersion: view.getUint16(off + 8, true),
        minorVersion: view.getUint16(off + 10, true),
    };
    var nameCount = view.getUint16(off + 12, true);
    var idCount = view.getUint16(off + 14, true);
    off += 16;
    for (var i = 0; i < nameCount; ++i) {
        var nameOffset = view.getUint32(off, true) & 0x7fffffff;
        var nextTable = view.getUint32(off + 4, true);
        // ignore if no next table is available
        if (!(nextTable & 0x80000000)) {
            off += 8;
            continue;
        }
        nextTable &= 0x7fffffff;
        var name_2 = readString(view, nameOffset);
        readLanguageTable(view, typeEntry, name_2, nextTable, cb);
        off += 8;
    }
    for (var i = 0; i < idCount; ++i) {
        var id = view.getUint32(off, true) & 0x7fffffff;
        var nextTable = view.getUint32(off + 4, true);
        // ignore if no next table is available
        if (!(nextTable & 0x80000000)) {
            off += 8;
            continue;
        }
        nextTable &= 0x7fffffff;
        readLanguageTable(view, typeEntry, id, nextTable, cb);
        off += 8;
    }
}
function divideEntriesImplByID(r, names, entries) {
    var entriesByString = {};
    var entriesByNumber = {};
    entries.forEach(function (e) {
        if (typeof e.lang === 'string') {
            entriesByString[e.lang] = e;
            names.push(e.lang);
        }
        else {
            entriesByNumber[e.lang] = e;
        }
    });
    var strKeys = Object.keys(entriesByString);
    strKeys.sort().forEach(function (type) {
        r.s.push(entriesByString[type]);
    });
    var numKeys = Object.keys(entriesByNumber);
    numKeys
        .map(function (k) { return Number(k); })
        .sort(function (a, b) { return a - b; })
        .forEach(function (type) {
        r.n.push(entriesByNumber[type]);
    });
    return 16 + 8 * (strKeys.length + numKeys.length);
}
function divideEntriesImplByName(r, names, entries) {
    var entriesByString = {};
    var entriesByNumber = {};
    entries.forEach(function (e) {
        var _a, _b;
        if (typeof e.id === 'string') {
            var a = (_a = entriesByString[e.id]) !== null && _a !== void 0 ? _a : (entriesByString[e.id] = []);
            names.push(e.id);
            a.push(e);
        }
        else {
            var a = (_b = entriesByNumber[e.id]) !== null && _b !== void 0 ? _b : (entriesByNumber[e.id] = []);
            a.push(e);
        }
    });
    var sSum = Object.keys(entriesByString)
        .sort()
        .map(function (id) {
        var o = {
            id: id,
            s: [],
            n: [],
        };
        r.s.push(o);
        return divideEntriesImplByID(o, names, entriesByString[id]);
    })
        .reduce(function (p, c) { return p + 8 + c; }, 0);
    var nSum = Object.keys(entriesByNumber)
        .map(function (k) { return Number(k); })
        .sort(function (a, b) { return a - b; })
        .map(function (id) {
        var o = {
            id: id,
            s: [],
            n: [],
        };
        r.n.push(o);
        return divideEntriesImplByID(o, names, entriesByNumber[id]);
    })
        .reduce(function (p, c) { return p + 8 + c; }, 0);
    return 16 + sSum + nSum;
}
function divideEntriesImplByType(r, names, entries) {
    var entriesByString = {};
    var entriesByNumber = {};
    entries.forEach(function (e) {
        var _a, _b;
        if (typeof e.type === 'string') {
            var a = (_a = entriesByString[e.type]) !== null && _a !== void 0 ? _a : (entriesByString[e.type] = []);
            names.push(e.type);
            a.push(e);
        }
        else {
            var a = (_b = entriesByNumber[e.type]) !== null && _b !== void 0 ? _b : (entriesByNumber[e.type] = []);
            a.push(e);
        }
    });
    var sSum = Object.keys(entriesByString)
        .sort()
        .map(function (type) {
        var o = { type: type, s: [], n: [] };
        r.s.push(o);
        return divideEntriesImplByName(o, names, entriesByString[type]);
    })
        .reduce(function (p, c) { return p + 8 + c; }, 0);
    var nSum = Object.keys(entriesByNumber)
        .map(function (k) { return Number(k); })
        .sort(function (a, b) { return a - b; })
        .map(function (type) {
        var o = { type: type, s: [], n: [] };
        r.n.push(o);
        return divideEntriesImplByName(o, names, entriesByNumber[type]);
    })
        .reduce(function (p, c) { return p + 8 + c; }, 0);
    return 16 + sSum + nSum;
}
function calculateStringLengthForWrite(text) {
    var length = text.length;
    // limit to 65535 because the 'length' field is uint16
    return length > 65535 ? 65535 : length;
}
function getStringOffset(target, strings) {
    var l = strings.length;
    for (var i = 0; i < l; ++i) {
        var s = strings[i];
        if (s.text === target) {
            return s.offset;
        }
    }
    throw new Error('Unexpected');
}
/** (returns offset just after the written text) */
function writeString(view, offset, text) {
    var length = calculateStringLengthForWrite(text);
    view.setUint16(offset, length, true);
    offset += 2;
    for (var i = 0; i < length; ++i) {
        view.setUint16(offset, text.charCodeAt(i), true);
        offset += 2;
    }
    return offset;
}
function writeLanguageTable(view, offset, strings, data) {
    // characteristics
    view.setUint32(offset, 0, true);
    // timestamp
    view.setUint32(offset + 4, 0, true);
    // major version / minor version
    view.setUint32(offset + 8, 0, true);
    // name entries
    view.setUint16(offset + 12, data.s.length, true);
    // id entries
    view.setUint16(offset + 14, data.n.length, true);
    offset += 16;
    // name entries (not in specification)
    data.s.forEach(function (e) {
        var strOff = getStringOffset(e.lang, strings);
        view.setUint32(offset, strOff, true);
        view.setUint32(offset + 4, e.offset, true);
        offset += 8;
    });
    // id entries
    data.n.forEach(function (e) {
        view.setUint32(offset, e.lang, true);
        view.setUint32(offset + 4, e.offset, true);
        offset += 8;
    });
    return offset;
}
function writeNameTable(view, offset, leafOffset, strings, data) {
    // characteristics
    view.setUint32(offset, 0, true);
    // timestamp
    view.setUint32(offset + 4, 0, true);
    // major version / minor version
    view.setUint32(offset + 8, 0, true);
    // name entries
    view.setUint16(offset + 12, data.s.length, true);
    // id entries
    view.setUint16(offset + 14, data.n.length, true);
    offset += 16;
    data.s.forEach(function (e) {
        e.offset = leafOffset;
        leafOffset = writeLanguageTable(view, leafOffset, strings, e);
    });
    data.n.forEach(function (e) {
        e.offset = leafOffset;
        leafOffset = writeLanguageTable(view, leafOffset, strings, e);
    });
    data.s.forEach(function (e) {
        var strOff = getStringOffset(e.id, strings);
        view.setUint32(offset, strOff + 0x80000000, true);
        view.setUint32(offset + 4, e.offset + 0x80000000, true);
        offset += 8;
    });
    data.n.forEach(function (e) {
        view.setUint32(offset, e.id, true);
        view.setUint32(offset + 4, e.offset + 0x80000000, true);
        offset += 8;
    });
    return leafOffset;
}
function writeTypeTable(view, offset, strings, data) {
    // characteristics
    view.setUint32(offset, 0, true);
    // timestamp
    view.setUint32(offset + 4, 0, true);
    // major version / minor version
    view.setUint32(offset + 8, 0, true);
    // name entries
    view.setUint16(offset + 12, data.s.length, true);
    // id entries
    view.setUint16(offset + 14, data.n.length, true);
    offset += 16;
    var nextTableOffset = offset + 8 * (data.s.length + data.n.length);
    data.s.forEach(function (e) {
        e.offset = nextTableOffset;
        nextTableOffset += 16 + 8 * (e.s.length + e.n.length);
    });
    data.n.forEach(function (e) {
        e.offset = nextTableOffset;
        nextTableOffset += 16 + 8 * (e.s.length + e.n.length);
    });
    data.s.forEach(function (e) {
        var strOff = getStringOffset(e.type, strings);
        view.setUint32(offset, strOff + 0x80000000, true);
        view.setUint32(offset + 4, e.offset + 0x80000000, true);
        offset += 8;
        nextTableOffset = writeNameTable(view, e.offset, nextTableOffset, strings, e);
    });
    data.n.forEach(function (e) {
        view.setUint32(offset, e.type, true);
        view.setUint32(offset + 4, e.offset + 0x80000000, true);
        offset += 8;
        nextTableOffset = writeNameTable(view, e.offset, nextTableOffset, strings, e);
    });
    return nextTableOffset;
}
////////////////////////////////////////////////////////////////////////////////
/** Manages resource data for NtExecutable */
var NtExecutableResource = /** @class */ (function () {
    function NtExecutableResource() {
        /** The timestamp for resource */
        this.dateTime = 0;
        /** The major version data for resource */
        this.majorVersion = 0;
        /** The minor version data for resource */
        this.minorVersion = 0;
        /** Resource entries */
        this.entries = [];
        /**
         * The section data header of resource data (used by outputResource method).
         * This instance will be null if the base executable does not contain resource data.
         * You can override this field before calling outputResource method.
         * (Note that the addresses and sizes are ignored for output)
         */
        this.sectionDataHeader = null;
        this.originalSize = 0;
    }
    NtExecutableResource.prototype.parse = function (section, ignoreUnparsableData) {
        if (!section.data) {
            return;
        }
        var view = new DataView(section.data);
        // --- First: Resource Directory Table ---
        // (off: 0 -- Characteristics (uint32))
        this.dateTime = view.getUint32(4, true);
        this.majorVersion = view.getUint16(8, true);
        this.minorVersion = view.getUint16(10, true);
        var nameCount = view.getUint16(12, true);
        var idCount = view.getUint16(14, true);
        var off = 16;
        var res = [];
        var cb = function (t, n, l) {
            var off = view.getUint32(l.dataOffset, true) -
                section.info.virtualAddress;
            var size = view.getUint32(l.dataOffset + 4, true);
            var cp = view.getUint32(l.dataOffset + 8, true);
            if (off >= 0) {
                var bin = new Uint8Array(size);
                bin.set(new Uint8Array(section.data, off, size));
                res.push({
                    type: t.type,
                    id: n.name,
                    lang: l.lang,
                    codepage: cp,
                    bin: bin.buffer,
                });
            }
            else {
                if (!ignoreUnparsableData) {
                    throw new Error('Cannot parse resource directory entry; RVA seems to be invalid.');
                }
                res.push({
                    type: t.type,
                    id: n.name,
                    lang: l.lang,
                    codepage: cp,
                    bin: new ArrayBuffer(0),
                    rva: l.dataOffset,
                });
            }
        };
        for (var i = 0; i < nameCount; ++i) {
            var nameOffset = view.getUint32(off, true) & 0x7fffffff;
            var nextTable = view.getUint32(off + 4, true);
            // ignore if no next table is available
            if (!(nextTable & 0x80000000)) {
                off += 8;
                continue;
            }
            nextTable &= 0x7fffffff;
            var name_3 = readString(view, nameOffset);
            readNameTable(view, name_3, nextTable, cb);
            off += 8;
        }
        for (var i = 0; i < idCount; ++i) {
            var typeId = view.getUint32(off, true) & 0x7fffffff;
            var nextTable = view.getUint32(off + 4, true);
            // ignore if no next table is available
            if (!(nextTable & 0x80000000)) {
                off += 8;
                continue;
            }
            nextTable &= 0x7fffffff;
            readNameTable(view, typeId, nextTable, cb);
            off += 8;
        }
        this.entries = res;
        this.originalSize = section.data.byteLength;
    };
    /**
     * Parses resource data for `NtExecutable`.
     * This function returns valid instance even if
     * the executable does not have resource data.
     * @param exe `NtExecutable` instance
     * @param ignoreUnparsableData (default: false) specify true if skipping 'unparsable' (e.g. unusual format) data.
     *   When true, the resource data may break on write operation.
     */
    NtExecutableResource.from = function (exe, ignoreUnparsableData) {
        if (ignoreUnparsableData === void 0) { ignoreUnparsableData = false; }
        var secs = []
            .concat(exe.getAllSections())
            .sort(function (a, b) { return a.info.virtualAddress - b.info.virtualAddress; });
        var entry = exe.getSectionByEntry(ImageDirectoryEntry.Resource);
        // check if the section order is supported
        // (not supported if any other sections except 'relocation' is available,
        // because the recalculation of virtual address is not simple)
        if (entry) {
            var reloc = exe.getSectionByEntry(ImageDirectoryEntry.BaseRelocation);
            for (var i = 0; i < secs.length; ++i) {
                var s = secs[i];
                if (s === entry) {
                    for (var j = i + 1; j < secs.length; ++j) {
                        if (!reloc || secs[j] !== reloc) {
                            throw new Error('After Resource section, sections except for relocation are not supported');
                        }
                    }
                    break;
                }
            }
        }
        var r = new NtExecutableResource();
        r.sectionDataHeader = entry ? cloneObject(entry.info) : null;
        if (entry) {
            r.parse(entry, ignoreUnparsableData);
        }
        return r;
    };
    /**
     * Add or replace the resource entry.
     * This method replaces the entry only if there is an entry with `type`, `id` and `lang` equal.
     */
    NtExecutableResource.prototype.replaceResourceEntry = function (entry) {
        for (var len = this.entries.length, i = 0; i < len; ++i) {
            var e = this.entries[i];
            if (e.type === entry.type &&
                e.id === entry.id &&
                e.lang === entry.lang) {
                this.entries[i] = entry;
                return;
            }
        }
        this.entries.push(entry);
    };
    /**
     * Returns all resource entries, which has specified type and id, as UTF-8 string data.
     * @param type Resource type
     * @param id Resource id
     * @returns an array of lang and value pair (tuple)
     */
    NtExecutableResource.prototype.getResourceEntriesAsString = function (type, id) {
        return this.entries
            .filter(function (entry) { return entry.type === type && entry.id === id; })
            .map(function (entry) { return [entry.lang, binaryToString(entry.bin)]; });
    };
    /**
     * Add or replace the resource entry with UTF-8 string data.
     * This method is a wrapper of {@link NtExecutableResource.replaceResourceEntry}.
     */
    NtExecutableResource.prototype.replaceResourceEntryFromString = function (type, id, lang, value) {
        var entry = {
            type: type,
            id: id,
            lang: lang,
            codepage: 1200,
            bin: stringToBinary(value),
        };
        this.replaceResourceEntry(entry);
    };
    /**
     * Removes resource entries which has specified type and id.
     */
    NtExecutableResource.prototype.removeResourceEntry = function (type, id, lang) {
        this.entries = this.entries.filter(function (entry) {
            return !(entry.type === type &&
                entry.id === id &&
                (typeof lang === 'undefined' || entry.lang === lang));
        });
    };
    /**
     * Generates resource data binary for NtExecutable (not for .res file)
     * @param virtualAddress The virtual address for the section
     * @param alignment File alignment value of executable
     * @param noGrow Set true to disallow growing resource section (throw errors if data exceeds)
     * @param allowShrink Set true to allow shrinking resource section (if the data size is less than original)
     */
    NtExecutableResource.prototype.generateResourceData = function (virtualAddress, alignment, noGrow, allowShrink) {
        if (noGrow === void 0) { noGrow = false; }
        if (allowShrink === void 0) { allowShrink = false; }
        // estimate data size and divide to output table
        var r = {
            s: [],
            n: [],
        };
        var strings = [];
        var size = divideEntriesImplByType(r, strings, this.entries);
        strings = removeDuplicates(strings);
        var stringsOffset = size;
        size += strings.reduce(function (prev, cur) {
            return prev + 2 + calculateStringLengthForWrite(cur) * 2;
        }, 0);
        size = roundUp(size, 8);
        var descOffset = size;
        size = this.entries.reduce(function (p, e) {
            e.offset = p;
            return p + 16;
        }, descOffset);
        var dataOffset = size;
        size = this.entries.reduce(function (p, e) {
            return roundUp(p, 8) + e.bin.byteLength;
        }, dataOffset);
        var alignedSize = roundUp(size, alignment);
        var originalAlignedSize = roundUp(this.originalSize, alignment);
        if (noGrow) {
            if (alignedSize > originalAlignedSize) {
                throw new Error('New resource data is larger than original');
            }
        }
        if (!allowShrink) {
            if (alignedSize < originalAlignedSize) {
                alignedSize = originalAlignedSize;
            }
        }
        // generate binary
        var bin = new ArrayBuffer(alignedSize);
        var view = new DataView(bin);
        var o = descOffset;
        var va = virtualAddress + dataOffset;
        this.entries.forEach(function (e) {
            var len = e.bin.byteLength;
            if (typeof e.rva !== 'undefined') {
                // RVA
                view.setUint32(o, e.rva, true);
            }
            else {
                va = roundUp(va, 8);
                // RVA
                view.setUint32(o, va, true);
                va += len;
            }
            // size
            view.setUint32(o + 4, len, true);
            // codepage
            view.setUint32(o + 8, e.codepage, true);
            // (zero)
            view.setUint32(o + 12, 0, true);
            o += 16;
        });
        o = dataOffset;
        this.entries.forEach(function (e) {
            var len = e.bin.byteLength;
            copyBuffer(bin, o, e.bin, 0, len);
            o += roundUp(len, 8);
        });
        var stringsData = [];
        o = stringsOffset;
        strings.forEach(function (s) {
            stringsData.push({
                offset: o,
                text: s,
            });
            o = writeString(view, o, s);
        });
        writeTypeTable(view, 0, stringsData, r);
        // fill with 'PADDINGX'
        if (alignedSize > size) {
            var pad = 'PADDINGX';
            for (var i = size, j = 0; i < alignedSize; ++i, ++j) {
                if (j === 8) {
                    j = 0;
                }
                view.setUint8(i, pad.charCodeAt(j));
            }
        }
        return {
            bin: bin,
            rawSize: size,
            dataOffset: dataOffset,
            descEntryOffset: descOffset,
            descEntryCount: this.entries.length,
        };
    };
    /**
     * Writes holding resource data to specified NtExecutable instance.
     * @param exeDest An NtExecutable instance to write resource section to
     * @param noGrow Set true to disallow growing resource section (throw errors if data exceeds)
     * @param allowShrink Set true to allow shrinking resource section (if the data size is less than original)
     */
    NtExecutableResource.prototype.outputResource = function (exeDest, noGrow, allowShrink) {
        if (noGrow === void 0) { noGrow = false; }
        if (allowShrink === void 0) { allowShrink = false; }
        // make section data
        var fileAlign = exeDest.getFileAlignment();
        var sectionData;
        if (this.sectionDataHeader) {
            sectionData = {
                data: null,
                info: cloneObject(this.sectionDataHeader),
            };
        }
        else {
            sectionData = {
                data: null,
                info: {
                    name: '.rsrc',
                    virtualSize: 0,
                    virtualAddress: 0,
                    sizeOfRawData: 0,
                    pointerToRawData: 0,
                    pointerToRelocations: 0,
                    pointerToLineNumbers: 0,
                    numberOfRelocations: 0,
                    numberOfLineNumbers: 0,
                    characteristics: 0x40000040, // read access and initialized data
                },
            };
        }
        // first, set virtualAddress to 0 because
        // the virtual address is not determined now
        var data = this.generateResourceData(0, fileAlign, noGrow, allowShrink);
        sectionData.data = data.bin;
        sectionData.info.sizeOfRawData = data.bin.byteLength;
        sectionData.info.virtualSize = data.rawSize;
        // write as section
        exeDest.setSectionByEntry(ImageDirectoryEntry.Resource, sectionData);
        // rewrite section raw-data
        var generatedSection = exeDest.getSectionByEntry(ImageDirectoryEntry.Resource);
        var view = new DataView(generatedSection.data);
        // set RVA
        var o = data.descEntryOffset;
        var va = generatedSection.info.virtualAddress + data.dataOffset;
        for (var i = 0; i < data.descEntryCount; ++i) {
            var len = view.getUint32(o + 4, true);
            va = roundUp(va, 8);
            // RVA
            view.setUint32(o, va, true);
            va += len;
            o += 16;
        }
    };
    return NtExecutableResource;
}());
export default NtExecutableResource;
