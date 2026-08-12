import { CancellationToken } from "./CancellationToken";
export declare function retry<T>(task: () => Promise<T>, options: {
    retries: number;
    interval: number;
    backoff?: number;
    attempt?: number;
    cancellationToken?: CancellationToken;
    shouldRetry?: (e: any) => boolean | Promise<boolean>;
}): Promise<T>;
