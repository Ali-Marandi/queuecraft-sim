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
/** abstract class that support array-like methods and 'for...of' operation */
var ArrayFormatBase = /** @class */ (function (_super) {
    __extends(ArrayFormatBase, _super);
    function ArrayFormatBase(view) {
        return _super.call(this, view) || this;
    }
    ArrayFormatBase.prototype.forEach = function (callback) {
        var len = this.length;
        var a = [];
        a.length = len;
        for (var i = 0; i < len; ++i) {
            a[i] = this.get(i);
        }
        for (var i = 0; i < len; ++i) {
            callback(a[i], i, this);
        }
    };
    ArrayFormatBase.prototype._iterator = function () {
        return new (/** @class */ (function () {
            function class_1(base) {
                this.base = base;
                this.i = 0;
            }
            class_1.prototype.next = function () {
                if (this.i === this.base.length) {
                    return {
                        value: undefined,
                        done: true,
                    };
                }
                else {
                    return {
                        value: this.base.get(this.i++),
                        done: false,
                    };
                }
            };
            return class_1;
        }()))(this);
    };
    return ArrayFormatBase;
}(FormatBase));
/* istanbul ignore else */
if (typeof Symbol !== 'undefined') {
    ArrayFormatBase.prototype[Symbol.iterator] =
        ArrayFormatBase.prototype._iterator;
}
export default ArrayFormatBase;
