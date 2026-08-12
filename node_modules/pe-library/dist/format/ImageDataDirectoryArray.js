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
var ArrayFormatBase_js_1 = require("./ArrayFormatBase.js");
var ImageDataDirectoryArray = /** @class */ (function (_super) {
    __extends(ImageDataDirectoryArray, _super);
    function ImageDataDirectoryArray(view) {
        var _this = _super.call(this, view) || this;
        _this.length = 16;
        return _this;
    }
    /** @note This does not clone binary data; the changes to the array will modify the specified buffer `bin` */
    ImageDataDirectoryArray.from = function (bin, offset) {
        if (offset === void 0) { offset = 0; }
        return new ImageDataDirectoryArray(new DataView(bin, offset, 128));
    };
    ImageDataDirectoryArray.prototype.get = function (index) {
        return {
            virtualAddress: this.view.getUint32(index * 8, true),
            size: this.view.getUint32(4 + index * 8, true),
        };
    };
    ImageDataDirectoryArray.prototype.set = function (index, data) {
        this.view.setUint32(index * 8, data.virtualAddress, true);
        this.view.setUint32(4 + index * 8, data.size, true);
    };
    ImageDataDirectoryArray.prototype.findIndexByVirtualAddress = function (virtualAddress) {
        for (var i = 0; i < 16; ++i) {
            var va = this.view.getUint32(i * 8, true);
            var vs = this.view.getUint32(4 + i * 8, true);
            if (virtualAddress >= va && virtualAddress < va + vs) {
                return i;
            }
        }
        return null;
    };
    ImageDataDirectoryArray.size = 128; // 16 * 8
    ImageDataDirectoryArray.itemSize = 8;
    return ImageDataDirectoryArray;
}(ArrayFormatBase_js_1.default));
exports.default = ImageDataDirectoryArray;
