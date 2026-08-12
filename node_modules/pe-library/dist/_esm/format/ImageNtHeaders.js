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
import ImageFileHeader from './ImageFileHeader.js';
import ImageOptionalHeader from './ImageOptionalHeader.js';
import ImageOptionalHeader64 from './ImageOptionalHeader64.js';
import ImageDataDirectoryArray from './ImageDataDirectoryArray.js';
import { createDataView } from '../util/functions.js';
var ImageNtHeaders = /** @class */ (function (_super) {
    __extends(ImageNtHeaders, _super);
    function ImageNtHeaders(view) {
        return _super.call(this, view) || this;
    }
    ImageNtHeaders.from = function (bin, offset) {
        if (offset === void 0) { offset = 0; }
        var magic = createDataView(bin, offset + ImageFileHeader.size, 6).getUint16(4, true);
        var len = 4 + ImageFileHeader.size + ImageDataDirectoryArray.size;
        if (magic === ImageOptionalHeader64.DEFAULT_MAGIC) {
            len += ImageOptionalHeader64.size;
        }
        else {
            len += ImageOptionalHeader.size;
        }
        return new ImageNtHeaders(createDataView(bin, offset, len));
    };
    ImageNtHeaders.prototype.isValid = function () {
        return this.signature === ImageNtHeaders.DEFAULT_SIGNATURE;
    };
    ImageNtHeaders.prototype.is32bit = function () {
        return (this.view.getUint16(ImageFileHeader.size + 4, true) ===
            ImageOptionalHeader.DEFAULT_MAGIC);
    };
    Object.defineProperty(ImageNtHeaders.prototype, "signature", {
        get: function () {
            return this.view.getUint32(0, true);
        },
        set: function (val) {
            this.view.setUint32(0, val, true);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageNtHeaders.prototype, "fileHeader", {
        get: function () {
            return ImageFileHeader.from(this.view.buffer, this.view.byteOffset + 4);
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageNtHeaders.prototype, "optionalHeader", {
        get: function () {
            var off = ImageFileHeader.size + 4;
            var magic = this.view.getUint16(off, true);
            if (magic === ImageOptionalHeader64.DEFAULT_MAGIC) {
                return ImageOptionalHeader64.from(this.view.buffer, this.view.byteOffset + off);
            }
            else {
                return ImageOptionalHeader.from(this.view.buffer, this.view.byteOffset + off);
            }
        },
        enumerable: false,
        configurable: true
    });
    Object.defineProperty(ImageNtHeaders.prototype, "optionalHeaderDataDirectory", {
        get: function () {
            return ImageDataDirectoryArray.from(this.view.buffer, this.view.byteOffset + this.getDataDirectoryOffset());
        },
        enumerable: false,
        configurable: true
    });
    ImageNtHeaders.prototype.getDataDirectoryOffset = function () {
        var off = ImageFileHeader.size + 4;
        var magic = this.view.getUint16(off, true);
        if (magic === ImageOptionalHeader64.DEFAULT_MAGIC) {
            off += ImageOptionalHeader64.size;
        }
        else {
            off += ImageOptionalHeader.size;
        }
        return off;
    };
    ImageNtHeaders.prototype.getSectionHeaderOffset = function () {
        return this.getDataDirectoryOffset() + ImageDataDirectoryArray.size;
    };
    ImageNtHeaders.DEFAULT_SIGNATURE = 0x4550; // 'PE\x00\x00'
    return ImageNtHeaders;
}(FormatBase));
export default ImageNtHeaders;
