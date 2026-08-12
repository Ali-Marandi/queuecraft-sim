var FormatBase = /** @class */ (function () {
    function FormatBase(view) {
        this.view = view;
    }
    FormatBase.prototype.copyTo = function (bin, offset) {
        new Uint8Array(bin, offset, this.view.byteLength).set(new Uint8Array(this.view.buffer, this.view.byteOffset, this.view.byteLength));
    };
    Object.defineProperty(FormatBase.prototype, "byteLength", {
        get: function () {
            return this.view.byteLength;
        },
        enumerable: false,
        configurable: true
    });
    return FormatBase;
}());
export default FormatBase;
