const { app, BrowserWindow, Tray, Menu } = require("electron");
const path = require("path");
const fs = require("fs");

function createWindow() {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: { nodeIntegration: true },
  });
  win.loadURL("http://localhost:4173/");
}

function setupTray() {
  const iconPath = path.join(__dirname, "icon.png");
  if (!fs.existsSync(iconPath)) {
    console.warn("Tray icon not found at ui/icon.png; skipping tray setup.");
    return;
  }
  const tray = new Tray(iconPath);
  const contextMenu = Menu.buildFromTemplate([
    { label: "Open Jessica", click: createWindow },
    { label: "Exit", click: () => app.quit() },
  ]);
  tray.setToolTip("Jessica AI Assistant");
  tray.setContextMenu(contextMenu);
}

app.whenReady().then(() => {
  createWindow();
  setupTray();
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});