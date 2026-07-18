const { app, BrowserWindow, session } = require("electron");
const path = require("path");
const { spawn } = require("child_process");
const http = require("http");
const fs = require("fs");

const BACKEND_DIR = path.join(__dirname, "..", "backend");
const BACKEND_HEALTH_URL = "http://127.0.0.1:8000/";
let backendProcess = null;
let mainWindow = null;

function startBackend() {
  return new Promise((resolve) => {
    // Loga a saída do backend num arquivo, pra poder debugar se precisar
    // (fica em backend/backend.log)
    const logPath = path.join(BACKEND_DIR, "backend.log");
    const logStream = fs.createWriteStream(logPath, { flags: "a" });

    backendProcess = spawn("python", ["app.py"], {
      cwd: BACKEND_DIR,
      windowsHide: true, // não abre uma janela de terminal separada
    });

    backendProcess.stdout.on("data", (data) => logStream.write(data));
    backendProcess.stderr.on("data", (data) => logStream.write(data));

    backendProcess.on("error", (err) => {
      console.error("Erro ao iniciar o backend:", err.message);
      resolve(false);
    });

    // Espera o backend responder no /, tentando por até ~30 segundos
    // (a primeira vez pode demorar mais, se o Whisper estiver baixando o
    // modelo de voz)
    let tries = 0;
    const maxTries = 60;
    const check = () => {
      http.get(BACKEND_HEALTH_URL, (res) => {
        resolve(true);
      }).on("error", () => {
        tries += 1;
        if (tries >= maxTries) {
          console.error("Backend não respondeu a tempo.");
          resolve(false);
        } else {
          setTimeout(check, 500);
        }
      });
    };
    setTimeout(check, 800);
  });
}

function stopBackend() {
  if (backendProcess) {
    backendProcess.kill();
    backendProcess = null;
  }
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    backgroundColor: "#080b14",
    autoHideMenuBar: true,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
    },
  });

  mainWindow.loadFile(path.join(__dirname, "index.html"));
}

app.whenReady().then(async () => {
  session.defaultSession.setPermissionRequestHandler((webContents, permission, callback) => {
    if (permission === "media") {
      callback(true);
    } else {
      callback(false);
    }
  });

  const ok = await startBackend();
  if (!ok) {
    console.error("Não consegui iniciar o backend automaticamente. Verifique backend/backend.log");
  }

  createWindow();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  stopBackend();
  if (process.platform !== "darwin") app.quit();
});

app.on("before-quit", () => {
  stopBackend();
});
