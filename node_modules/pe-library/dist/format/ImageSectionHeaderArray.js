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
var functions_js_1 = require("../util/functions.js");
var ImageSectionHeaderArray = /** @class */ (function (_super) {
    __extends(ImageSectionHeaderArray, _super);
    function ImageSectionHeaderArray(view, length) {
        var _this = _super.call(this, view) || this;
        _this.length = length;
        return _this;
    }
    ImageSectionHeaderArray.from = function (bin, length, offset) {
        if (offset === void 0) { offset = 0; }
        var size = length * 40;
        return new ImageSectionHeaderArray(new DataView(bin, offset, size), length);
    };
    ImageSectionHeaderArray.prototype.get = function (index) {
        return {
            name: functions_js_1.getFixedString(this.view, index * 40, 8),
            virtualSize: this.view.getUint32(8 + index * 40, true),
            virtualAddress: this.view.getUint32(12 + index * 40, true),
            sizeOfRawData: this.view.getUint32(16 + index * 40, true),
            pointerToRawData: this.view.getUint32(20 + index * 40, true),
            pointerToRelocations: this.view.getUint32(24 + index * 40, true),
            pointerToLineNumbers: this.view.getUint32(28 + index * 40, true),
            numberOfRelocations: this.view.getUint16(32 + index * 40, true),
            numberOfLineNumbers: this.view.getUint16(34 + index * 40, true),
            characteristics: this.view.getUint32(36 + index * 40, true),
        };
    };
    ImageSectionHeaderArray.prototype.set = function (index, data) {
        functions_js_1.setFixedString(this.view, index * 40, 8, data.name);
        this.view.setUint32(8 + index * 40, data.virtualSize, true);
        this.view.setUint32(12 + index * 40, data.virtualAddress, true);
        this.view.setUint32(16 + index * 40, data.sizeOfRawData, true);
        this.view.setUint32(20 + index * 40, data.pointerToRawData, true);
        this.view.setUint32(24 + index * 40, data.pointerToRelocations, true);
        this.view.setUint32(28 + index * 40, data.pointerToLineNumbers, true);
        this.view.setUint16(32 + index * 40, data.numberOfRelocations, true);
        this.view.setUint16(34 + index * 40, data.numberOfLineNumbers, true);
        this.view.setUint32(36 + index * 40, data.characteristics, true);
    };
    ImageSectionHeaderArray.itemSize = 40;
    return ImageSectionHeaderArray;
}(ArrayFormatBase_js_1.default));
exports.default = ImageSectionHeaderArray;
