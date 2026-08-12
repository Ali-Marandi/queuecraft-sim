"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Permission = void 0;
exports.Permission = {
    getPermissionDeniedState(entry1, entry2) {
        if (entry1.isPermissionDenied && entry2.isPermissionDenied) {
            return "access-error-both";
        }
        else if (entry1.isPermissionDenied) {
            return "access-error-left";
        }
        else if (entry2.isPermissionDenied) {
            return "access-error-right";
        }
        else {
            return "access-ok";
        }
    },
    getPermissionDeniedStateWhenLeftMissing(entry2) {
        let permissionDeniedState = "access-ok";
        if (entry2.isPermissionDenied) {
            permissionDeniedState = "access-error-right";
        }
        return permissionDeniedState;
    },
    getPermissionDeniedStateWhenRightMissing(entry1) {
        let permissionDeniedState = "access-ok";
        if (entry1.isPermissionDenied) {
            permissionDeniedState = "access-error-left";
        }
        return permissionDeniedState;
    }
};
//# sourceMappingURL=Permission.js.map