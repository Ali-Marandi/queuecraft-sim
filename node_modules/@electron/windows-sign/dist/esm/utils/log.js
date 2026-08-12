import { debug as debugModule } from 'debug';
export function enableDebugging() {
    debugModule.enable('electron-windows-sign');
}
export const log = debugModule('electron-windows-sign');
