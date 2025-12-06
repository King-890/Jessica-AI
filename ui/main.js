/* eslint-env node */
import { app, BrowserWindow, Tray, Menu, globalShortcut, ipcMain } from "electron";
import path from "path";
import fs from "fs";
import { fileURLToPath } from "url";
import process from "node:process";
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

let win

function createWindow() {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: { nodeIntegration: true },
  });
  win.loadURL("http://localhost:5175/");
  win.on('close', (e) => { e.preventDefault(); win.hide(); })
  return win
}

let tray
function setupTray() {
  const iconPath = path.join(__dirname, "icon.png");
  if (!fs.existsSync(iconPath)) {
    console.warn("Tray icon not found at ui/icon.png; skipping tray setup.");
    return;
  }
  tray = new Tray(iconPath);
  const contextMenu = Menu.buildFromTemplate([
    { label: "Open Jessica", click: () => { if (!win) win = createWindow(); win.show(); win.focus(); } },
    { label: "Open Settings", click: () => { if (!win) win = createWindow(); win.show(); win.focus(); } },
    { type: 'separator' },
    { label: "Start on Login", type: 'checkbox', checked: false, click: (item) => app.setLoginItemSettings({ openAtLogin: item.checked }) },
    { type: 'separator' },
    { label: "Exit", click: () => app.quit() },
  ]);
  tray.setToolTip("Jessica AI Assistant");
  tray.setContextMenu(contextMenu);
}

function setupHotkeys() {
  try {
    globalShortcut.register('Control+Space', () => {
      if (!win) win = createWindow();
      if (win.isVisible()) { win.hide(); } else { win.show(); win.focus(); }
    })
  } catch (e) {
    console.warn('Failed to register hotkey', e)
  }
}

function setupIPC() {
  ipcMain.handle('backend:fetch', async (event, payload) => {
    try {
      const { url, method = 'GET', headers = {}, body } = payload || {}
      const res = await fetch(url, { method, headers, body })
      const text = await res.text()
      return { ok: res.ok, status: res.status, headers: Object.fromEntries(res.headers), body: text }
    } catch (e) {
      return { ok: false, status: 0, error: String(e) }
    }
  })
}

app.whenReady().then(() => {
  win = createWindow();
  setupTray();
  setupHotkeys();
  setupIPC();
  const gotLock = app.requestSingleInstanceLock();
  if (!gotLock) {
    app.quit();
  } else {
    app.on('second-instance', () => {
      if (!win) win = createWindow();
      win.show(); win.focus();
    })
  }
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});

app.on('will-quit', () => {
  try { globalShortcut.unregisterAll() } catch {}
})