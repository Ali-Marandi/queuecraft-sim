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
var ImageFileHeader = /** @class */ (function (_super) {
    __extends(ImageFileHeader, _super);
    function ImageFileHeader(view) {
        return _super.call(this, view) || this;
    }
    ImageFileHeader.from = function (bin, offset) {
        if (offset === void 0) { offset = 0; }
        return new ImageFileHeader(new DataView(bin, offset, 20));
    };
    Object.defineProperty(ImageFileHeader.prototype, "machine", {
        get: function () {
            return this.view.getUint16(0, true);
        },
        set: function (val) {
            this.view.setUint16(0, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageFileHeader.prototype, "numberOfSections", {
        get: function () {
            return this.view.getUint16(2, true);
        },
        set: function (val) {
            this.view.setUint16(2, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageFileHeader.prototype, "timeDateStamp", {
        get: function () {
            return this.view.getUint32(4, true);
        },
        set: function (val) {
            this.view.setUint32(4, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageFileHeader.prototype, "pointerToSymbolTable", {
        get: function () {
            return this.view.getUint32(8, true);
        },
        set: function (val) {
            this.view.setUint32(8, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageFileHeader.prototype, "numberOfSymbols", {
        get: function () {
            return this.view.getUint32(12, true);
        },
        set: function (val) {
            this.view.setUint32(12, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageFileHeader.prototype, "sizeOfOptionalHeader", {
        get: function () {
            return this.view.getUint16(16, true);
        },
        set: function (val) {
            this.view.setUint16(16, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageFileHeader.prototype, "characteristics", {
        get: function () {
            return this.view.getUint16(18, true);
        },
        set: function (val) {
            this.view.setUint16(18, val, true);
        },
        enumerable: false,
        configurable: true
    });
    ImageFileHeader.size = 20;
    return ImageFileHeader;
}(FormatBase));
export default ImageFileHeader;
