const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("odfOcr", {
  openFile: () => ipcRenderer.invoke("dialog:openFile"),
  readFileBase64: (path) => ipcRenderer.invoke("file:readBase64", path),
  processOcr: (imageBase64, filename) =>
    ipcRenderer.invoke("ocr:process", { imageBase64, filename }),
  saveResult: (jsonString) => ipcRenderer.invoke("dialog:saveResult", jsonString),
});
