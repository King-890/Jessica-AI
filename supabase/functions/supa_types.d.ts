// Type definitions for Deno to fix IDE errors when Deno extension is missing
declare namespace Deno {
    export var env: {
        get(key: string): string | undefined;
        set(key: string, value: string): void;
        toObject(): { [key: string]: string };
    };
}
