"use strict";
var __extends = (this && this.__extends) || (function () {
    var extendStatics = function (d, b) {
        extendStatics = Object.setPrototypeOf ||
            ({ __proto__: [] } instanceof Array && function (d, b) { d.__proto__ = b; }) ||
            function (d, b) { for (var p in b) if (Object.prototype.hasOwnProperty.call(b, p)) d[p] = b[p]; };
        return extendStatics(d, b);
    };
    return function (d, b) {
        if (typeof b !== "function" && b !== null)
            throw new TypeError("Class extends value " + String(b) + " is not a constructor or null");
        extendStatics(d, b);
        function __() { this.constructor = d; }
        d.prototype = b === null ? Object.create(b) : (__.prototype = b.prototype, new __());
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
var FormatBase_js_1 = require("./FormatBase.js");
function getUint64LE(view, offset) {
    return (view.getUint32(offset + 4, true) * 0x100000000 +
        view.getUint32(offset, true));
}
function setUint64LE(view, offset, val) {
    view.setUint32(offset, val & 0xffffffff, true);
    view.setUint32(offset + 4, Math.floor(val / 0x100000000), true);
}
function getUint64LEBigInt(view, offset) {
    /* istanbul ignore if */
    if (typeof BigInt === 'undefined') {
        throw new Error('BigInt not supported');
    }
    return (BigInt(0x100000000) * BigInt(view.getUint32(offset + 4, true)) +
        BigInt(view.getUint32(offset, true)));
}
function setUint64LEBigInt(view, offset, val) {
    /* istanbul ignore if */
    if (typeof BigInt === 'undefined') {
        throw new Error('BigInt not supported');
    }
    view.setUint32(offset, Number(val & BigInt(0xffffffff)), true);
    view.setUint32(offset + 4, Math.floor(Number((val / BigInt(0x100000000)) & BigInt(0xffffffff))), true);
}
var ImageOptionalHeader64 = /** @class */ (function (_super) {
    __extends(ImageOptionalHeader64, _super);
    function ImageOptionalHeader64(view) {
        return _super.call(this, view) || this;
    }
    ImageOptionalHeader64.from = function (bin, offset) {
        if (offset === void 0) { offset = 0; }
        return new ImageOptionalHeader64(new DataView(bin, offset, 112));
    };
    Object.defineProperty(ImageOptionalHeader64.prototype, "magic", {
        get: function () {
            return this.view.getUint16(0, true);
        },
        set: function (val) {
            this.view.setUint16(0, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageOptionalHeader64.prototype, "majorLinkerVersion", {
        get: function () {
            return this.view.getUint8(2);
        },
        set: function (val) {
            this.view.setUint8(2, val);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageOptionalHeader64.prototype, "minorLinkerVersion", {
        get: function () {
            return this.view.getUint8(3);
        },
        set: function (val) {
            this.view.setUint8(3, val);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageOptionalHeader64.prototype, "sizeOfCode", {
        get: function () {
            return this.view.getUint32(4, true);
        },
        set: function (val) {
            this.view.setUint32(4, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageOptionalHeader64.prototype, "sizeOfInitializedData", {
        get: function () {
            return this.view.getUint32(8, true);
        },
        set: function (val) {
            this.view.setUint32(8, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageOptionalHeader64.prototype, "sizeOfUninitializedData", {
        get: function () {
            return this.view.getUint32(12, true);
        },
        set: function (val) {
            this.view.setUint32(12, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageOptionalHeader64.prototype, "addressOfEntryPoint", {
        get: function () {
            return this.view.getUint32(16, true);
        },
        set: function (val) {
            this.view.setUint32(16, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageOptionalHeader64.prototype, "baseOfCode", {
        get: function () {
            return this.view.getUint32(20, true);
        },
        set: function (val) {
            this.view.setUint32(20, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageOptionalHeader64.prototype, "imageBase", {
        get: function () {
            return getUint64LE(this.view, 24);
        },
        set: function (val) {
            setUint64LE(this.view, 24, val);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageOptionalHeader64.prototype, "imageBaseBigInt", {
        get: function () {
            return getUint64LEBigInt(this.view, 24);
        },
        set: function (val) {
            setUint64LEBigInt(this.view, 24, val);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageOptionalHeader64.prototype, "sectionAlignment", {
        get: function () {
            return this.view.getUint32(32, true);
        },
        set: function (val) {
            this.view.setUint32(32, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageOptionalHeader64.prototype, "fileAlignment", {
        get: function () {
            return this.view.getUint32(36, true);
        },
        set: function (val) {
            this.view.setUint32(36, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageOptionalHeader64.prototype, "majorOperatingSystemVersion", {
        get: function () {
            return this.view.getUint16(40, true);
        },
        set: function (val) {
            this.view.setUint16(40, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageOptionalHeader64.prototype, "minorOperatingSystemVersion", {
        get: function () {
            return this.view.getUint16(42, true);
        },
        set: function (val) {
            this.view.setUint16(42, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageOptionalHeader64.prototype, "majorImageVersion", {
        get: function () {
            return this.view.getUint16(44, true);
        },
        set: function (val) {
            this.view.setUint16(44, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageOptionalHeader64.prototype, "minorImageVersion", {
        get: function () {
            return this.view.getUint16(46, true);
        },
        set: function (val) {
            this.view.setUint16(46, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageOptionalHeader64.prototype, "majorSubsystemVersion", {
        get: function () {
            return this.view.getUint16(48, true);
        },
        set: function (val) {
            this.view.setUint16(48, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageOptionalHeader64.prototype, "minorSubsystemVersion", {
        get: function () {
            return this.view.getUint16(50, true);
        },
        set: function (val) {
            this.view.setUint16(50, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageOptionalHeader64.prototype, "win32VersionValue", {
        get: function () {
            return this.view.getUint32(52, true);
        },
        set: function (val) {
            this.view.setUint32(52, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageOptionalHeader64.prototype, "sizeOfImage", {
        get: function () {
            return this.view.getUint32(56, true);
        },
        set: function (val) {
            this.view.setUint32(56, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageOptionalHeader64.prototype, "sizeOfHeaders", {
        get: function () {
            return this.view.getUint32(60, true);
        },
        set: function (val) {
            this.view.setUint32(60, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageOptionalHeader64.prototype, "checkSum", {
        get: function () {
            return this.view.getUint32(64, true);
        },
        set: function (val) {
            this.view.setUint32(64, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageOptionalHeader64.prototype, "subsystem", {
        get: function () {
            return this.view.getUint16(68, true);
        },
        set: function (val) {
            this.view.setUint16(68, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageOptionalHeader64.prototype, "dllCharacteristics", {
        get: function () {
            return this.view.getUint16(70, true);
        },
        set: function (val) {
            this.view.setUint16(70, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageOptionalHeader64.prototype, "sizeOfStackReserve", {
        get: function () {
            return getUint64LE(this.view, 72);
        },
        set: function (val) {
            setUint64LE(this.view, 72, val);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageOptionalHeader64.prototype, "sizeOfStackReserveBigInt", {
        get: function () {
            return getUint64LEBigInt(this.view, 72);
        },
        set: function (val) {
            setUint64LEBigInt(this.view, 72, val);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageOptionalHeader64.prototype, "sizeOfStackCommit", {
        get: function () {
            return getUint64LE(this.view, 80);
        },
        set: function (val) {
            setUint64LE(this.view, 80, val);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageOptionalHeader64.prototype, "sizeOfStackCommitBigInt", {
        get: function () {
            return getUint64LEBigInt(this.view, 80);
        },
        set: function (val) {
            setUint64LEBigInt(this.view, 80, val);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageOptionalHeader64.prototype, "sizeOfHeapReserve", {
        get: function () {
            return getUint64LE(this.view, 88);
        },
        set: function (val) {
            setUint64LE(this.view, 88, val);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageOptionalHeader64.prototype, "sizeOfHeapReserveBigInt", {
        get: function () {
            return getUint64LEBigInt(this.view, 88);
        },
        set: function (val) {
            setUint64LEBigInt(this.view, 88, val);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageOptionalHeader64.prototype, "sizeOfHeapCommit", {
        get: function () {
            return getUint64LE(this.view, 96);
        },
        set: function (val) {
            setUint64LE(this.view, 96, val);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageOptionalHeader64.prototype, "sizeOfHeapCommitBigInt", {
        get: function () {
            return getUint64LEBigInt(this.view, 96);
        },
        set: function (val) {
            setUint64LEBigInt(this.view, 96, val);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageOptionalHeader64.prototype, "loaderFlags", {
        get: function () {
            return this.view.getUint32(104, true);
        },
        set: function (val) {
            this.view.setUint32(104, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageOptionalHeader64.prototype, "numberOfRvaAndSizes", {
        get: function () {
            return this.view.getUint32(108, true);
        },
        set: function (val) {
            this.view.setUint32(108, val, true);
        },
        enumerable: false,
        configurable: true
    });
    ImageOptionalHeader64.size = 112;
    ImageOptionalHeader64.DEFAULT_MAGIC = 0x20b;
    return ImageOptionalHeader64;
}(FormatBase_js_1.default));
exports.default = ImageOptionalHeader64;
