"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
var ImageDirectoryEntry;
(function (ImageDirectoryEntry) {
    ImageDirectoryEntry[ImageDirectoryEntry["Export"] = 0] = "Export";
    ImageDirectoryEntry[ImageDirectoryEntry["Import"] = 1] = "Import";
    ImageDirectoryEntry[ImageDirectoryEntry["Resource"] = 2] = "Resource";
    ImageDirectoryEntry[ImageDirectoryEntry["Exception"] = 3] = "Exception";
    ImageDirectoryEntry[ImageDirectoryEntry["Certificate"] = 4] = "Certificate";
    // alias
    ImageDirectoryEntry[ImageDirectoryEntry["Security"] = 4] = "Security";
    ImageDirectoryEntry[ImageDirectoryEntry["BaseRelocation"] = 5] = "BaseRelocation";
    ImageDirectoryEntry[ImageDirectoryEntry["Debug"] = 6] = "Debug";
    ImageDirectoryEntry[ImageDirectoryEntry["Architecture"] = 7] = "Architecture";
    ImageDirectoryEntry[ImageDirectoryEntry["GlobalPointer"] = 8] = "GlobalPointer";
    ImageDirectoryEntry[ImageDirectoryEntry["Tls"] = 9] = "Tls";
    ImageDirectoryEntry[ImageDirectoryEntry["TLS"] = 9] = "TLS";
    ImageDirectoryEntry[ImageDirectoryEntry["LoadConfig"] = 10] = "LoadConfig";
    ImageDirectoryEntry[ImageDirectoryEntry["BoundImport"] = 11] = "BoundImport";
    ImageDirectoryEntry[ImageDirectoryEntry["Iat"] = 12] = "Iat";
    ImageDirectoryEntry[ImageDirectoryEntry["IAT"] = 12] = "IAT";
    ImageDirectoryEntry[ImageDirectoryEntry["DelayImport"] = 13] = "DelayImport";
    ImageDirectoryEntry[ImageDirectoryEntry["ComDescriptor"] = 14] = "ComDescriptor";
    ImageDirectoryEntry[ImageDirectoryEntry["COMDescriptor"] = 14] = "COMDescriptor";
})(ImageDirectoryEntry || (ImageDirectoryEntry = {}));
exports.default = ImageDirectoryEntry;
