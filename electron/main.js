/**
 * main.js – Electron Hauptprozess
 */

const { app, BrowserWindow, ipcMain, dialog } = require("electron");
const { spawn } = require("child_process");
const path = require("path");
const fs = require("fs");

let mainWindow = null;
let pythonProcess = null;

const SERVER_PORT = 5000;
const SERVER_URL = `http://127.0.0.1:${SERVER_PORT}`;

function startPythonServer() {
  const scriptPath = path.join(__dirname, "..", "scripts", "start_server.py");
  pythonProcess = spawn("python", [scriptPath, "--port", SERVER_PORT], {
    stdio: ["ignore", "pipe", "pipe"],
  });
  pythonProcess.stdout.on("data", (d) => console.log(`[Python] ${d.toString().trim()}`));
  pythonProcess.stderr.on("data", (d) => console.error(`[Python ERR] ${d.toString().trim()}`));

  return new Promise((resolve) => {
    const check = setInterval(async () => {
      try {
        const res = await fetch(`${SERVER_URL}/health`);
        if (res.ok) { clearInterval(check); resolve(); }
      } catch (_) {}
    }, 500);
    setTimeout(() => { clearInterval(check); resolve(); }, 15000);
  });
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200, height: 800, minWidth: 900, minHeight: 600,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
    },
    titleBarStyle: "hiddenInset",
    title: "odf-ocr",
  });
  mainWindow.loadFile(path.join(__dirname, "renderer", "index.html"));
  mainWindow.on("closed", () => { mainWindow = null; });
}

ipcMain.handle("dialog:openFile", async () => {
  const { canceled, filePaths } = await dialog.showOpenDialog(mainWindow, {
    properties: ["openFile"],
    filters: [{ name: "Bilder", extensions: ["jpg","jpeg","png","tiff","tif","bmp"] }],
  });
  return canceled ? null : filePaths[0];
});

ipcMain.handle("file:readBase64", async (_, filePath) => {
  return fs.readFileSync(filePath).toString("base64");
});

ipcMain.handle("ocr:process", async (_, { imageBase64, filename }) => {
  const res = await fetch(`${SERVER_URL}/ocr`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ image: imageBase64, filename }),
  });
  return res.json();
});

ipcMain.handle("dialog:saveResult", async (_, jsonString) => {
  const { canceled, filePath } = await dialog.showSaveDialog(mainWindow, {
    defaultPath: "stundennachweis_ergebnis.json",
    filters: [{ name: "JSON", extensions: ["json"] }],
  });
  if (canceled || !filePath) return false;
  fs.writeFileSync(filePath, jsonString, "utf-8");
  return true;
});

app.whenReady().then(async () => {
  await startPythonServer();
  createWindow();
  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  if (pythonProcess) pythonProcess.kill();
  if (process.platform !== "darwin") app.quit();
});
