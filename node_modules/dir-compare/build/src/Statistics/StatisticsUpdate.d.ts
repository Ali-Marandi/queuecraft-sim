import { DifferenceType, Entry, InitialStatistics, Options, PermissionDeniedState, Reason } from "..";
import { ExtOptions } from "../ExtOptions";
/**
 * Calculates comparison statistics.
 */
export declare const StatisticsUpdate: {
    updateStatisticsBoth(entry1: Entry, entry2: Entry, same: boolean, reason: Reason, type: DifferenceType, permissionDeniedState: PermissionDeniedState, statistics: InitialStatistics, options: ExtOptions): void;
    updateStatisticsLeft(entry1: Entry, type: DifferenceType, permissionDeniedState: PermissionDeniedState, statistics: InitialStatistics, options: ExtOptions): void;
    updateStatisticsRight(entry2: Entry, type: DifferenceType, permissionDeniedState: PermissionDeniedState, statistics: InitialStatistics, options: Options): void;
};
//# sourceMappingURL=StatisticsUpdate.d.ts.map