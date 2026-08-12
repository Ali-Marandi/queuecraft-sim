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
import { createDataView } from '../util/functions.js';
var ImageDosHeader = /** @class */ (function (_super) {
    __extends(ImageDosHeader, _super);
    function ImageDosHeader(view) {
        return _super.call(this, view) || this;
    }
    ImageDosHeader.from = function (bin, offset) {
        if (offset === void 0) { offset = 0; }
        return new ImageDosHeader(createDataView(bin, offset, 64));
    };
    ImageDosHeader.prototype.isValid = function () {
        return this.magic === ImageDosHeader.DEFAULT_MAGIC;
    };
    Object.defineProperty(ImageDosHeader.prototype, "magic", {
        get: function () {
            return this.view.getUint16(0, true);
        },
        set: function (val) {
            this.view.setUint16(0, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageDosHeader.prototype, "lastPageSize", {
        get: function () {
            return this.view.getUint16(2, true);
        },
        set: function (val) {
            this.view.setUint16(2, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageDosHeader.prototype, "pages", {
        get: function () {
            return this.view.getUint16(4, true);
        },
        set: function (val) {
            this.view.setUint16(4, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageDosHeader.prototype, "relocations", {
        get: function () {
            return this.view.getUint16(6, true);
        },
        set: function (val) {
            this.view.setUint16(6, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageDosHeader.prototype, "headerSizeInParagraph", {
        get: function () {
            return this.view.getUint16(8, true);
        },
        set: function (val) {
            this.view.setUint16(8, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageDosHeader.prototype, "minAllocParagraphs", {
        get: function () {
            return this.view.getUint16(10, true);
        },
        set: function (val) {
            this.view.setUint16(10, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageDosHeader.prototype, "maxAllocParagraphs", {
        get: function () {
            return this.view.getUint16(12, true);
        },
        set: function (val) {
            this.view.setUint16(12, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageDosHeader.prototype, "initialSS", {
        get: function () {
            return this.view.getUint16(14, true);
        },
        set: function (val) {
            this.view.setUint16(14, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageDosHeader.prototype, "initialSP", {
        get: function () {
            return this.view.getUint16(16, true);
        },
        set: function (val) {
            this.view.setUint16(16, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageDosHeader.prototype, "checkSum", {
        get: function () {
            return this.view.getUint16(18, true);
        },
        set: function (val) {
            this.view.setUint16(18, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageDosHeader.prototype, "initialIP", {
        get: function () {
            return this.view.getUint16(20, true);
        },
        set: function (val) {
            this.view.setUint16(20, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageDosHeader.prototype, "initialCS", {
        get: function () {
            return this.view.getUint16(22, true);
        },
        set: function (val) {
            this.view.setUint16(22, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageDosHeader.prototype, "relocationTableAddress", {
        get: function () {
            return this.view.getUint16(24, true);
        },
        set: function (val) {
            this.view.setUint16(24, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageDosHeader.prototype, "overlayNum", {
        get: function () {
            return this.view.getUint16(26, true);
        },
        set: function (val) {
            this.view.setUint16(26, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageDosHeader.prototype, "oemId", {
        // WORD e_res[4] (28,30,32,34)
        get: function () {
            return this.view.getUint16(36, true);
        },
        set: function (val) {
            this.view.setUint16(36, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageDosHeader.prototype, "oemInfo", {
        get: function () {
            return this.view.getUint16(38, true);
        },
        set: function (val) {
            this.view.setUint16(38, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageDosHeader.prototype, "newHeaderAddress", {
        // WORD e_res2[10] (40,42,44,46,48,50,52,54,56,58)
        get: function () {
            return this.view.getUint32(60, true);
        },
        set: function (val) {
            this.view.setUint32(60, val, true);
        },
        enumerable: false,
        configurable: true
    });
    ImageDosHeader.size = 64;
    ImageDosHeader.DEFAULT_MAGIC = 0x5a4d; // 'MZ'
    return ImageDosHeader;
}(FormatBase));
export default ImageDosHeader;
