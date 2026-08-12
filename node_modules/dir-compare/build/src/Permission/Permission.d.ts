import { Entry, PermissionDeniedState } from "../types";
export declare const Permission: {
    getPermissionDeniedState(entry1: Entry, entry2: Entry): PermissionDeniedState;
    getPermissionDeniedStateWhenLeftMissing(entry2: Entry): PermissionDeniedState;
    getPermissionDeniedStateWhenRightMissing(entry1: Entry): PermissionDeniedState;
};
//# sourceMappingURL=Permission.d.ts.map