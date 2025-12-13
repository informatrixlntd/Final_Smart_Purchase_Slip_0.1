const { app, BrowserWindow, ipcMain, dialog, shell } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');

let mainWindow = null;
let loginWindow = null;
let splashWindow = null;
let backendProcess = null;
let printWindow = null;  

const isDev = !app.isPackaged;
const BACKEND_EXE = isDev
    ? path.join(__dirname, '..', 'dist-backend', 'purchase_slips_backend.exe')
    : path.join(process.resourcesPath, 'backend', 'purchase_slips_backend.exe');

const BACKEND_URL = 'http://127.0.0.1:5000';

function startBackend() {
    return new Promise((resolve, reject) => {
        console.log('[BACKEND] Starting backend server...');
        console.log('[BACKEND] Executable path:', BACKEND_EXE);

        if (!fs.existsSync(BACKEND_EXE)) {
            console.error('[BACKEND] Backend executable not found at:', BACKEND_EXE);
            reject(new Error(`Backend executable not found: ${BACKEND_EXE}`));
            return;
        }

        backendProcess = spawn(BACKEND_EXE, [], {
            cwd: path.dirname(BACKEND_EXE),
            detached: false,
            windowsHide: true
        });

        backendProcess.stdout.on('data', (data) => {
            console.log('[BACKEND]', data.toString().trim());
        });

        backendProcess.stderr.on('data', (data) => {
            console.error('[BACKEND ERROR]', data.toString().trim());
        });

        backendProcess.on('error', (err) => {
            console.error('[BACKEND] Failed to start:', err);
            reject(err);
        });

        backendProcess.on('exit', (code) => {
            console.log(`[BACKEND] Process exited with code ${code}`);
            if (code !== 0 && code !== null) {
                backendProcess = null;
            }
        });

        let attempts = 0;
        const maxAttempts = 30;
        const checkInterval = setInterval(() => {
            http.get(BACKEND_URL, (res) => {
                if (res.statusCode === 200 || res.statusCode === 404) {
                    console.log('[BACKEND] Backend is ready!');
                    clearInterval(checkInterval);
                    resolve();
                }
            }).on('error', () => {
                attempts++;
                if (attempts >= maxAttempts) {
                    clearInterval(checkInterval);
                    reject(new Error('Backend failed to start within timeout'));
                }
            });
        }, 500);
    });
}

function stopBackend() {
    if (backendProcess) {
        console.log('[BACKEND] Stopping backend server...');
        try {
            if (process.platform === 'win32') {
                spawn('taskkill', ['/pid', backendProcess.pid, '/f', '/t']);
            } else {
                backendProcess.kill('SIGTERM');
            }
        } catch (error) {
            console.error('[BACKEND] Error stopping backend:', error);
        }
        backendProcess = null;
    }
}

function createSplashWindow() {
    splashWindow = new BrowserWindow({
        width: 500,
        height: 300,
        transparent: true,
        frame: false,
        alwaysOnTop: true,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true
        }
    });

    splashWindow.loadFile(path.join(__dirname, 'splash.html'));
    splashWindow.center();
}

function createLoginWindow() {
    if (splashWindow && !splashWindow.isDestroyed()) {
        splashWindow.close();
        splashWindow = null;
    }

    loginWindow = new BrowserWindow({
        width: 450,
        height: 600,
        resizable: false,
        frame: true,
        icon: path.join(__dirname, 'assets', 'spslogo.png'),
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false
        },
        title: 'Smart Purchase Slip Manager - Login'
    });

    loginWindow.loadFile(path.join(__dirname, 'login.html'));
    loginWindow.center();

    loginWindow.on('closed', () => {
        loginWindow = null;
        if (!mainWindow) {
            app.quit();
        }
    });
}

function createMainWindow() {
    if (loginWindow && !loginWindow.isDestroyed()) {
        loginWindow.close();
        loginWindow = null;
    }

    mainWindow = new BrowserWindow({
        width: 1400,
        height: 900,
        minWidth: 1000,
        minHeight: 700,
        icon: path.join(__dirname, 'assets', 'spslogo.png'),
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false,
            enableRemoteModule: true
        },
        title: 'Smart Purchase Slip Manager'
    });

    mainWindow.loadFile(path.join(__dirname, 'app.html'));
    mainWindow.maximize();

    if (isDev) {
        mainWindow.webContents.openDevTools();
    }

    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

ipcMain.on('login-success', (event, userData) => {
    console.log('[AUTH] Login successful, opening main window');
    createMainWindow();
});

ipcMain.on('logout', () => {
    console.log('[AUTH] Logout requested');
    if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.close();
        mainWindow = null;
    }
    createLoginWindow();
});

ipcMain.on('print-slip-html', async (event, slipId) => {
    console.log('[PRINT] Direct HTML print requested for slip:', slipId);

    try {
        if (!printWindow || printWindow.isDestroyed()) {
            printWindow = new BrowserWindow({
                width: 800,
                height: 1100,
                show: false,
                webPreferences: {
                    nodeIntegration: false,
                    contextIsolation: true
                }
            });
        }

        await printWindow.loadURL(`http://localhost:5000/print/${slipId}`);
        await new Promise(resolve => setTimeout(resolve, 1500));

        printWindow.webContents.print({
            silent: false,
            printBackground: true,
            color: true,
            margins: {
                marginType: 'none'
            },
            landscape: false,
            pagesPerSheet: 1,
            collate: false,
            copies: 1
        }, (success, failureReason) => {
            if (success) {
                console.log('[PRINT] Print job sent successfully');
            } else {
                console.error('[PRINT] Print failed:', failureReason);
            }

            if (printWindow && !printWindow.isDestroyed()) {
                printWindow.close();
                printWindow = null;
                console.log('[PRINT] Print window closed');
            }
        });

    } catch (error) {
        console.error('[PRINT] Error during HTML print:', error);

        if (printWindow && !printWindow.isDestroyed()) {
            printWindow.close();
        }

        dialog.showErrorBox(
            'Print Error',
            `Failed to print slip:\n\n${error.message}\n\nPlease ensure the Flask server is running.`
        );
    }
});

ipcMain.on('print-slip', async (event, data) => {
    let printWindow = null;

    const slipId = typeof data === 'object' ? data.slipId : data;
    const mobileNumber = typeof data === 'object' ? data.mobileNumber : null;
    const billNo = typeof data === 'object' ? data.billNo : null;

    try {
        printWindow = new BrowserWindow({
            width: 800,
            height: 1100,
            show: false,
            webPreferences: {
                nodeIntegration: false,
                contextIsolation: true
            }
        });

        await printWindow.loadURL(`http://localhost:5000/print/${slipId}`);
        await new Promise(resolve => setTimeout(resolve, 1500));

        const pdfData = await printWindow.webContents.printToPDF({
            marginsType: 0,
            pageSize: 'A4',
            printBackground: true,
            printSelectionOnly: false,
            landscape: false
        });

        printWindow.close();
        printWindow = null;

        const pdfBase64 = pdfData.toString('base64');

        const viewerWindow = new BrowserWindow({
            width: 900,
            height: 1200,
            icon: path.join(__dirname, 'assets', 'spslogo.png'),
            webPreferences: {
                nodeIntegration: true,
                contextIsolation: false
            },
            title: `Purchase Slip ${slipId}`
        });

        const viewerHTML = `
<!DOCTYPE html>
<html>
<head>
    <title>Purchase Slip ${slipId}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: #525252;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            overflow: hidden;
        }
        #toolbar {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background: #323639;
            padding: 12px 20px;
            display: flex;
            gap: 12px;
            justify-content: center;
            align-items: center;
            z-index: 1000;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        }
        button {
            background: #4a90e2;
            color: white;
            border: none;
            padding: 10px 24px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        button:hover {
            background: #357abd;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }
        button:active {
            transform: translateY(0);
        }
        button.download {
            background: #4caf50;
        }
        button.download:hover {
            background: #45a049;
        }
        button.whatsapp {
            background: #25d366;
        }
        button.whatsapp:hover {
            background: #20ba5a;
        }
        #pdf-container {
            width: 100%;
            height: calc(100vh - 50px);
            border: none;
            margin-top: 50px;
            background: #525252;
        }
    </style>
</head>
<body>
    <div id="toolbar">
        <button onclick="printPDF()">
            <span>🖨️</span>
            <span>Print</span>
        </button>
        <button class="download" onclick="downloadPDF()">
            <span>⬇️</span>
            <span>Download PDF</span>
        </button>
        <button class="whatsapp" onclick="shareWhatsApp()">
            <span>📱</span>
            <span>Share on WhatsApp</span>
        </button>
    </div>
    <iframe id="pdf-container" src="data:application/pdf;base64,${pdfBase64}"></iframe>

    <script>
        const { shell, ipcRenderer } = require('electron');
        const fs = require('fs');
        const path = require('path');
        const os = require('os');

        const pdfBase64 = '${pdfBase64}';
        const slipId = ${slipId};
        const mobileNumber = ${mobileNumber ? `'${mobileNumber}'` : 'null'};
        const billNo = ${billNo ? `'${billNo}'` : 'null'};

        function printPDF() {
            console.log('[PRINT] Print button clicked - sending IPC to print HTML');
            ipcRenderer.send('print-slip-html', slipId);
        }

        function downloadPDF() {
            const link = document.createElement('a');
            link.href = 'data:application/pdf;base64,' + pdfBase64;
            link.download = 'purchase_slip_' + slipId + '.pdf';
            link.click();
        }

        function shareWhatsApp() {
            if (!mobileNumber || mobileNumber === 'null' || mobileNumber.trim() === '') {
                alert('No mobile number found for this slip.\\n\\nPlease add a mobile number in the slip details and try again.');
                return;
            }

            try {
                const documentsPath = path.join(os.homedir(), 'Documents', 'PurchaseSlipWhatsApp');
                if (!fs.existsSync(documentsPath)) {
                    fs.mkdirSync(documentsPath, { recursive: true });
                }

                const timestamp = new Date().toISOString().replace(/[:.]/g, '-').split('T')[0];
                const fileName = 'Purchase_Slip_' + (billNo || slipId) + '_' + timestamp + '.pdf';
                const filePath = path.join(documentsPath, fileName);

                const pdfBuffer = Buffer.from(pdfBase64, 'base64');
                fs.writeFileSync(filePath, pdfBuffer);

                const cleanMobile = mobileNumber.replace(/[^0-9]/g, '');
                const whatsappNumber = cleanMobile.startsWith('91') ? cleanMobile : '91' + cleanMobile;

                ipcRenderer.send('share-whatsapp', {
                    filePath: filePath,
                    phoneNumber: whatsappNumber,
                    billNo: billNo || slipId
                });

            } catch (error) {
                alert('Error preparing WhatsApp share:\\n\\n' + error.message + '\\n\\nPlease try again or contact support.');
                console.error('WhatsApp share error:', error);
            }
        }

        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'p') {
                e.preventDefault();
                console.log('[PRINT] Ctrl+P pressed - triggering print');
                printPDF();
            }
        });
    </script>
</body>
</html>
        `;

        viewerWindow.loadURL('data:text/html;charset=utf-8,' + encodeURIComponent(viewerHTML));

    } catch (error) {
        console.error('[PRINT] Error generating PDF:', error);

        if (printWindow && !printWindow.isDestroyed()) {
            printWindow.close();
        }

        dialog.showErrorBox(
            'Print Error',
            `Failed to generate PDF:\n\n${error.message}\n\nPlease ensure the Flask server is running.`
        );
    }
});

ipcMain.on('share-whatsapp', async (event, data) => {
    const { filePath, phoneNumber, billNo } = data;

    try {
        const whatsappUrl = `https://web.whatsapp.com/send?phone=${phoneNumber}`;
        await shell.openExternal(whatsappUrl);

        await new Promise(resolve => setTimeout(resolve, 3000));

        await shell.openPath(filePath);

        console.log('[WHATSAPP] Opened WhatsApp and PDF file for manual attachment');

    } catch (error) {
        console.error('[WHATSAPP] Error:', error);
        dialog.showErrorBox(
            'WhatsApp Share Error',
            `Failed to open WhatsApp:\n\n${error.message}\n\nThe PDF was saved to:\n${filePath}\n\nYou can manually share it.`
        );
    }
});

app.whenReady().then(async () => {
    console.log('[APP] Application starting...');
    console.log('[APP] isPackaged:', app.isPackaged);
    console.log('[APP] resourcesPath:', process.resourcesPath);

    createSplashWindow();

    try {
        await startBackend();
        console.log('[APP] Backend started successfully');

        setTimeout(() => {
            createLoginWindow();
        }, 1500);

    } catch (error) {
        console.error('[APP] Failed to start backend:', error);

        if (splashWindow && !splashWindow.isDestroyed()) {
            splashWindow.close();
        }

        const response = dialog.showMessageBoxSync({
            type: 'error',
            title: 'Backend Start Failed',
            message: 'Failed to start the backend server',
            detail: `Error: ${error.message}\n\nBackend path: ${BACKEND_EXE}\n\nThe application cannot continue.`,
            buttons: ['Exit', 'Show Logs'],
            defaultId: 0
        });

        if (response === 1) {
            const logsPath = path.join(app.getPath('userData'), 'logs');
            shell.openPath(logsPath);
        }

        app.quit();
    }
});

app.on('window-all-closed', () => {
    console.log('[APP] All windows closed');
    stopBackend();
    app.quit();
});

app.on('before-quit', () => {
    console.log('[APP] Application quitting...');
    stopBackend();
});

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createLoginWindow();
    }
});

process.on('exit', () => {
    stopBackend();
});

process.on('SIGINT', () => {
    stopBackend();
    process.exit();
});

process.on('SIGTERM', () => {
    stopBackend();
    process.exit();
});
