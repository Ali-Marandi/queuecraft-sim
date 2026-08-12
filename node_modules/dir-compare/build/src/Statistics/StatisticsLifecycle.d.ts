import { InitialStatistics, Statistics } from "..";
import { ExtOptions } from "../ExtOptions";
/**
 * Controls creation/completion of global statistics object.
 */
export declare const StatisticsLifecycle: {
    initStats(options: ExtOptions): InitialStatistics;
    completeStatistics(initialStatistics: InitialStatistics, options: ExtOptions): Statistics;
};
//# sourceMappingURL=StatisticsLifecycle.d.ts.map