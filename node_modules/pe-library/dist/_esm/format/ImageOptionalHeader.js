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
import FormatBase from './FormatBase.js';
var ImageOptionalHeader = /** @class */ (function (_super) {
    __extends(ImageOptionalHeader, _super);
    function ImageOptionalHeader(view) {
        return _super.call(this, view) || this;
    }
    ImageOptionalHeader.from = function (bin, offset) {
        if (offset === void 0) { offset = 0; }
        return new ImageOptionalHeader(new DataView(bin, offset, 96));
    };
    Object.defineProperty(ImageOptionalHeader.prototype, "magic", {
        get: function () {
            return this.view.getUint16(0, true);
        },
        set: function (val) {
            this.view.setUint16(0, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageOptionalHeader.prototype, "majorLinkerVersion", {
        get: function () {
            return this.view.getUint8(2);
        },
        set: function (val) {
            this.view.setUint8(2, val);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageOptionalHeader.prototype, "minorLinkerVersion", {
        get: function () {
            return this.view.getUint8(3);
        },
        set: function (val) {
            this.view.setUint8(3, val);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageOptionalHeader.prototype, "sizeOfCode", {
        get: function () {
            return this.view.getUint32(4, true);
        },
        set: function (val) {
            this.view.setUint32(4, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageOptionalHeader.prototype, "sizeOfInitializedData", {
        get: function () {
            return this.view.getUint32(8, true);
        },
        set: function (val) {
            this.view.setUint32(8, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageOptionalHeader.prototype, "sizeOfUninitializedData", {
        get: function () {
            return this.view.getUint32(12, true);
        },
        set: function (val) {
            this.view.setUint32(12, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageOptionalHeader.prototype, "addressOfEntryPoint", {
        get: function () {
            return this.view.getUint32(16, true);
        },
        set: function (val) {
            this.view.setUint32(16, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageOptionalHeader.prototype, "baseOfCode", {
        get: function () {
            return this.view.getUint32(20, true);
        },
        set: function (val) {
            this.view.setUint32(20, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageOptionalHeader.prototype, "baseOfData", {
        get: function () {
            return this.view.getUint32(24, true);
        },
        set: function (val) {
            this.view.setUint32(24, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageOptionalHeader.prototype, "imageBase", {
        get: function () {
            return this.view.getUint32(28, true);
        },
        set: function (val) {
            this.view.setUint32(28, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageOptionalHeader.prototype, "sectionAlignment", {
        get: function () {
            return this.view.getUint32(32, true);
        },
        set: function (val) {
            this.view.setUint32(32, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageOptionalHeader.prototype, "fileAlignment", {
        get: function () {
            return this.view.getUint32(36, true);
        },
        set: function (val) {
            this.view.setUint32(36, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageOptionalHeader.prototype, "majorOperatingSystemVersion", {
        get: function () {
            return this.view.getUint16(40, true);
        },
        set: function (val) {
            this.view.setUint16(40, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageOptionalHeader.prototype, "minorOperatingSystemVersion", {
        get: function () {
            return this.view.getUint16(42, true);
        },
        set: function (val) {
            this.view.setUint16(42, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageOptionalHeader.prototype, "majorImageVersion", {
        get: function () {
            return this.view.getUint16(44, true);
        },
        set: function (val) {
            this.view.setUint16(44, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageOptionalHeader.prototype, "minorImageVersion", {
        get: function () {
            return this.view.getUint16(46, true);
        },
        set: function (val) {
            this.view.setUint16(46, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageOptionalHeader.prototype, "majorSubsystemVersion", {
        get: function () {
            return this.view.getUint16(48, true);
        },
        set: function (val) {
            this.view.setUint16(48, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageOptionalHeader.prototype, "minorSubsystemVersion", {
        get: function () {
            return this.view.getUint16(50, true);
        },
        set: function (val) {
            this.view.setUint16(50, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageOptionalHeader.prototype, "win32VersionValue", {
        get: function () {
            return this.view.getUint32(52, true);
        },
        set: function (val) {
            this.view.setUint32(52, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageOptionalHeader.prototype, "sizeOfImage", {
        get: function () {
            return this.view.getUint32(56, true);
        },
        set: function (val) {
            this.view.setUint32(56, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageOptionalHeader.prototype, "sizeOfHeaders", {
        get: function () {
            return this.view.getUint32(60, true);
        },
        set: function (val) {
            this.view.setUint32(60, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageOptionalHeader.prototype, "checkSum", {
        get: function () {
            return this.view.getUint32(64, true);
        },
        set: function (val) {
            this.view.setUint32(64, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageOptionalHeader.prototype, "subsystem", {
        get: function () {
            return this.view.getUint16(68, true);
        },
        set: function (val) {
            this.view.setUint16(68, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageOptionalHeader.prototype, "dllCharacteristics", {
        get: function () {
            return this.view.getUint16(70, true);
        },
        set: function (val) {
            this.view.setUint16(70, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageOptionalHeader.prototype, "sizeOfStackReserve", {
        get: function () {
            return this.view.getUint32(72, true);
        },
        set: function (val) {
            this.view.setUint32(72, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageOptionalHeader.prototype, "sizeOfStackCommit", {
        get: function () {
            return this.view.getUint32(76, true);
        },
        set: function (val) {
            this.view.setUint32(76, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageOptionalHeader.prototype, "sizeOfHeapReserve", {
        get: function () {
            return this.view.getUint32(80, true);
        },
        set: function (val) {
            this.view.setUint32(80, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageOptionalHeader.prototype, "sizeOfHeapCommit", {
        get: function () {
            return this.view.getUint32(84, true);
        },
        set: function (val) {
            this.view.setUint32(84, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageOptionalHeader.prototype, "loaderFlags", {
        get: function () {
            return this.view.getUint32(88, true);
        },
        set: function (val) {
            this.view.setUint32(88, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageOptionalHeader.prototype, "numberOfRvaAndSizes", {
        get: function () {
            return this.view.getUint32(92, true);
        },
        set: function (val) {
            this.view.setUint32(92, val, true);
        },
        enumerable: false,
        configurable: true
    });
    ImageOptionalHeader.size = 96;
    ImageOptionalHeader.DEFAULT_MAGIC = 0x10b;
    return ImageOptionalHeader;
}(FormatBase));
export default ImageOptionalHeader;
