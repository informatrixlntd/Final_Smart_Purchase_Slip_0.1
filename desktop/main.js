const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const { spawn, exec } = require('child_process');
const fs = require('fs');

let mainWindow;
let pythonProcess;
let isBackupInProgress = false;
let canCloseApp = false;

// Load configuration from config.json
function loadConfig() {
    try {
        let configPath;
        if (app.isPackaged) {
            configPath = path.join(process.resourcesPath, 'config.json');
        } else {
            configPath = path.join(__dirname, '..', 'config.json');
        }

        if (fs.existsSync(configPath)) {
            const configData = fs.readFileSync(configPath, 'utf8');
            return JSON.parse(configData);
        }
    } catch (error) {
        console.error('Error loading config:', error);
    }

    // Default config if file not found
    return {
        database: {
            host: 'localhost',
            port: 3306,
            user: 'root',
            password: 'root',
            database: 'purchase_slips_db'
        }
    };
}

const config = loadConfig();

function createWindow() {
    // Create splash screen first
    let splashWindow = new BrowserWindow({
        width: 500,
        height: 500,
        transparent: true,
        frame: false,
        alwaysOnTop: true,
        icon: path.join(__dirname, 'assets', 'spslogo.png'),
        webPreferences: {
            nodeIntegration: false
        }
    });

    splashWindow.loadFile(path.join(__dirname, 'splash.html'));

    mainWindow = new BrowserWindow({
        width: 1400,
        height: 900,
        icon: path.join(__dirname, 'assets', 'spslogo.png'),
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false,
            enableRemoteModule: true
        },
        autoHideMenuBar: true,
        resizable: true,
        show: false
    });

    mainWindow.loadFile(path.join(__dirname, 'login.html'));

    mainWindow.once('ready-to-show', () => {
        setTimeout(() => {
            splashWindow.close();
            mainWindow.show();
        }, 2000);
    });

    mainWindow.on('close', async (event) => {
        if (!canCloseApp && !isBackupInProgress) {
            event.preventDefault();
            await showBackupDialog();
        }
    });

    mainWindow.on('closed', function() {
        mainWindow = null;
    });
}

async function showBackupDialog() {
    if (isBackupInProgress) return;

    const result = await dialog.showMessageBox(mainWindow, {
        type: 'warning',
        title: 'Backup Required Before Exit',
        message: 'Database backup is required before closing the application.',
        detail: 'Click "Start Backup" to create a backup and upload it to Google Drive.',
        buttons: ['Start Backup', 'Cancel'],
        defaultId: 0,
        cancelId: 1
    });

    if (result.response === 0) {
        await performBackup();
    }
}

async function performBackup() {
    isBackupInProgress = true;

    try {
        const progressDialog = dialog.showMessageBox(mainWindow, {
            type: 'info',
            title: 'Backup in Progress',
            message: 'Creating database backup...',
            detail: 'Please wait. This may take a few moments.',
            buttons: []
        });

        const dbConfig = config.database || {
            host: 'localhost',
            port: 3306,
            user: 'root',
            password: 'root',
            database: 'purchase_slips_db'
        };


        // Try to use backup module if available
        let backupSuccess = false;
        try {
            const backup = require('./backup');
            backupSuccess = await backup.performBackupAndUpload(dbConfig, mainWindow);
        } catch (error) {
            console.error('Backup module error:', error);
            // Fallback: just create local backup without Google Drive
            backupSuccess = await createLocalBackupOnly(dbConfig);
        }

        isBackupInProgress = false;

        if (backupSuccess) {
            await dialog.showMessageBox(mainWindow, {
                type: 'info',
                title: 'Backup Completed',
                message: 'Database backup completed successfully!',
                detail: 'The application will now close.',
                buttons: ['OK']
            });

            canCloseApp = true;
            mainWindow.close();
        } else {
            await dialog.showMessageBox(mainWindow, {
                type: 'error',
                title: 'Backup Failed',
                message: 'Database backup failed.',
                detail: 'Please try again or contact support.',
                buttons: ['OK']
            });
        }
    } catch (error) {
        isBackupInProgress = false;
        console.error('Backup error:', error);
        await dialog.showMessageBox(mainWindow, {
            type: 'error',
            title: 'Backup Error',
            message: 'An error occurred during backup.',
            detail: error.message,
            buttons: ['OK']
        });
    }
}

function createLocalBackupOnly(dbConfig) {
    return new Promise((resolve) => {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const backupDir = path.join(process.env.USERPROFILE || process.env.HOME, 'Documents', 'smart_purchase_slip_backup');

        if (!fs.existsSync(backupDir)) {
            fs.mkdirSync(backupDir, { recursive: true });
        }

        const backupFileName = `purchase_slips_backup_${timestamp}.sql`;
        const backupFilePath = path.join(backupDir, backupFileName);

        const command = `mysqldump -h ${dbConfig.host} -P ${dbConfig.port} -u ${dbConfig.user} -p${dbConfig.password} ${dbConfig.database} > "${backupFilePath}"`;

        exec(command, (error, stdout, stderr) => {
            if (error) {
                console.error('Local backup error:', error);
                resolve(false);
                return;
            }
            console.log('Local backup created:', backupFilePath);
            resolve(true);
        });
    });
}

function startPythonBackend() {
    // Check if packaged backend executable exists
    const isPackaged = app.isPackaged;
    let backendPath;

    if (isPackaged) {
        // In production, look for the packaged executable
        if (process.platform === 'win32') {
            backendPath = path.join(process.resourcesPath, 'backend', 'purchase_slips_backend.exe');
        } else {
            backendPath = path.join(process.resourcesPath, 'backend', 'purchase_slips_backend');
        }

        // Check if backend executable exists
        if (fs.existsSync(backendPath)) {
            console.log('Starting packaged backend:', backendPath);
            pythonProcess = spawn(backendPath, [], {
                cwd: path.join(process.resourcesPath, 'backend')
            });
        } else {
            console.error('Backend executable not found:', backendPath);
            dialog.showErrorBox('Backend Error', 'Backend executable not found. Please reinstall the application.');
            return;
        }
    } else {
        // In development, use Python script
        const pythonScript = path.join(__dirname, '..', 'backend', 'app.py');
        console.log('Starting development backend:', pythonScript);
        pythonProcess = spawn('python', [pythonScript], {
            cwd: path.join(__dirname, '..')
        });
    }

    pythonProcess.stdout.on('data', (data) => {
        console.log(`Backend: ${data}`);
    });

    pythonProcess.stderr.on('data', (data) => {
        console.error(`Backend Error: ${data}`);
    });

    pythonProcess.on('error', (error) => {
        console.error('Backend process error:', error);
        dialog.showErrorBox('Backend Error', `Failed to start backend: ${error.message}`);
    });

    setTimeout(() => {
        console.log('Backend started successfully');
    }, 3000);
}

app.on('ready', () => {
    startPythonBackend();
    createWindow();
});

app.on('window-all-closed', function() {
    if (pythonProcess) {
        pythonProcess.kill();
    }
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', function() {
    if (mainWindow === null) {
        createWindow();
    }
});

ipcMain.on('login-success', () => {
    mainWindow.loadFile(path.join(__dirname, 'app.html'));
});

ipcMain.on('logout', () => {
    mainWindow.loadFile(path.join(__dirname, 'login.html'));
});

/**
 * WhatsApp sharing handler with automated file attachment
 * Opens WhatsApp Desktop with specific contact and automates file attachment
 */



ipcMain.on('share-whatsapp', async (event, data) => {
    const { shell } = require('electron');
    const { exec } = require('child_process');
    const os = require('os');

    const { filePath, phoneNumber } = data;

    console.log("\n================================================");
    console.log("📱 WHATSAPP SHARE");
    console.log("Phone:", phoneNumber);
    console.log("File:", filePath);
    console.log("================================================");

    try {
        if (process.platform === 'win32') {

            // FIX: correct Windows path
            const fixedPath = filePath.replace(/\//g, '\\');

            // Create PowerShell script
            const psScriptPath = path.join(os.tmpdir(), 'whatsapp-share.ps1');

            const psScript = `
# WhatsApp Auto-Attach Script

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName Microsoft.VisualBasic
Add-Type -AssemblyName UIAutomationClient


Write-Host "Opening WhatsApp..."
Start-Process "whatsapp://send?phone=${phoneNumber}"
Start-Sleep -Seconds 4

# Detect WhatsApp window
$attempts = 0
$proc = $null
while ($attempts -lt 10 -and $proc -eq $null) {
    $proc = Get-Process | Where-Object { $_.MainWindowTitle -like "*WhatsApp*" } | Select-Object -First 1
    if ($proc -eq $null) {
        Start-Sleep -Seconds 1
        $attempts++
    }
}

if ($proc -eq $null) {
    Write-Host "WhatsApp not found"
    exit
}

Write-Host "Activating WhatsApp..."
[Microsoft.VisualBasic.Interaction]::AppActivate($proc.Id)
Start-Sleep -Milliseconds 1000

# Focus the message input field
$automation = New-Object -ComObject UIAutomationClient.CUIAutomation
$root = $automation.GetRootElement()

$waWin = $root.FindFirst(
    0x1,
    $automation.CreatePropertyCondition(30005, "WhatsApp")
)

if ($waWin -ne $null) {
    $edit = $waWin.FindFirst(
        0x4,
        $automation.CreatePropertyCondition(30003, 50004) # Edit box
    )
    if ($edit -ne $null) {
        $edit.SetFocus()
        Send-Keys "{TAB}"
Start-Sleep -Milliseconds 200
        // Start-Sleep -Milliseconds 300
    }
}

Write-Host "Preparing file to clipboard..."
$file = "${fixedPath}"

$data = New-Object System.Windows.Forms.DataObject
$list = New-Object System.Collections.Specialized.StringCollection
$list.Add($file)
$data.SetFileDropList($list)
[System.Windows.Forms.Clipboard]::SetDataObject($data, $true)

Start-Sleep -Milliseconds 500

Write-Host "Pasting file..."
[System.Windows.Forms.SendKeys]::SendWait("^v")

Start-Sleep -Seconds 2
Write-Host "DONE - File attached successfully!"
`;

            // Write script to temp file
            fs.writeFileSync(psScriptPath, psScript);

            console.log("Running PowerShell automation...");

            exec(`powershell.exe -ExecutionPolicy Bypass -File "${psScriptPath}"`, 
                (error, stdout, stderr) => {

                try { fs.unlinkSync(psScriptPath); } catch {}

                if (error) {
                    console.error("PowerShell error:", error);
                    exec(`start "" "whatsapp://send?phone=${phoneNumber}"`);
                    setTimeout(() => shell.showItemInFolder(filePath), 2000);
                } else {
                    console.log(stdout);
                    console.log("WhatsApp automation complete.");
                }
            });

        } else {
            // Mac/Linux fallback
            shell.openExternal(`whatsapp://send?phone=${phoneNumber}`);
            setTimeout(() => shell.showItemInFolder(filePath), 2500);
        }

    } catch (error) {
        console.error("WhatsApp Share Error:", error);
        dialog.showErrorBox("WhatsApp Share Error",
            `Failed to share on WhatsApp:\n${error.message}`);
    }
});


/**
 * Print slip HTML directly (correct method)
 * Loads the actual HTML from Flask and prints it using webContents.print()
 * This is the proper way to print - NOT from PDF viewer
 */
ipcMain.on('print-slip-html', async (event, slipId) => {
    console.log(`\n${'='.repeat(60)}`);
    console.log(`🖨️  PRINTING SLIP HTML - ID: ${slipId}`);
    console.log('='.repeat(60));

    let printWindow = null;

    try {
        // Create hidden window to load the actual HTML slip
        printWindow = new BrowserWindow({
            width: 800,
            height: 1100,
            show: false, // Hidden window for printing
            webPreferences: {
                nodeIntegration: false,
                contextIsolation: true
            }
        });

        console.log(`📄 Loading slip HTML from: http://localhost:5000/print/${slipId}`);

        // Load the actual HTML from Flask server
        await printWindow.loadURL(`http://localhost:5000/print/${slipId}`);

        // Wait for content to fully render
        await new Promise(resolve => setTimeout(resolve, 1500));

        console.log('✅ HTML loaded successfully, initiating print...');

        // Print the HTML directly using webContents.print()
        printWindow.webContents.print({
            silent: false, // Show print dialog
            printBackground: true, // Include background colors/images
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
                console.log('✅ Print job sent successfully');
            } else {
                console.error('❌ Print failed:', failureReason);
            }

            // Clean up the print window
            if (printWindow && !printWindow.isDestroyed()) {
                printWindow.close();
                printWindow = null;
                console.log('🧹 Print window closed');
            }
        });

    } catch (error) {
        console.error('❌ Error during HTML print:', error);

        // Clean up print window if it exists
        if (printWindow && !printWindow.isDestroyed()) {
            printWindow.close();
        }

        // Show error to user
        const { dialog } = require('electron');
        dialog.showErrorBox(
            'Print Error',
            `Failed to print slip:\n\n${error.message}\n\nPlease ensure the Flask server is running.`
        );
    }
});

/**
 * Print slip handler with PDF preview
 * Generates PDF using printToPDF and displays in custom viewer
 * User can print, download, or share on WhatsApp from the viewer
 */
ipcMain.on('print-slip', async (event, data) => {
    const { dialog, shell } = require('electron');
    let printWindow = null;

    // Handle both old format (just slipId) and new format (object with slipId)
    const slipId = typeof data === 'object' ? data.slipId : data;
    const mobileNumber = typeof data === 'object' ? data.mobileNumber : null;
    const billNo = typeof data === 'object' ? data.billNo : null;

    try {
        // Create hidden window to load slip content
        printWindow = new BrowserWindow({
            width: 800,
            height: 1100,
            show: false,
            webPreferences: {
                nodeIntegration: false,
                contextIsolation: true
            }
        });

        // Load slip HTML from Flask server
        await printWindow.loadURL(`http://localhost:5000/print/${slipId}`);

        // Wait for content to fully render
        await new Promise(resolve => setTimeout(resolve, 1500));

        // Generate PDF using Electron's built-in printToPDF
        const pdfData = await printWindow.webContents.printToPDF({
            marginsType: 0,
            pageSize: 'A4',
            printBackground: true,
            printSelectionOnly: false,
            landscape: false
        });

        // Close the temporary window
        printWindow.close();
        printWindow = null;

        // Convert PDF to base64 for embedding
        const pdfBase64 = pdfData.toString('base64');

        // Create PDF viewer window with toolbar
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

        // Create HTML with embedded PDF viewer and WhatsApp button
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
            // FIXED: Print the actual HTML slip using IPC
            // DO NOT use window.print() - it doesn't work with PDF iframes
            console.log('🖨️  Print button clicked - sending IPC to print HTML');
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
                // Create permanent WhatsApp share folder in user's Documents
                const documentsPath = path.join(os.homedir(), 'Documents', 'PurchaseSlipWhatsApp');
                if (!fs.existsSync(documentsPath)) {
                    fs.mkdirSync(documentsPath, { recursive: true });
                }

                // Save PDF to permanent folder with timestamp
                const timestamp = new Date().toISOString().replace(/[:.]/g, '-').split('T')[0];
                const fileName = 'Purchase_Slip_' + (billNo || slipId) + '_' + timestamp + '.pdf';
                const filePath = path.join(documentsPath, fileName);

                // Convert base64 to buffer and save
                const pdfBuffer = Buffer.from(pdfBase64, 'base64');
                fs.writeFileSync(filePath, pdfBuffer);

                // Clean mobile number and construct WhatsApp URL
                const cleanMobile = mobileNumber.replace(/[^0-9]/g, '');
                const whatsappNumber = cleanMobile.startsWith('91') ? cleanMobile : '91' + cleanMobile;

                // Send IPC to main process to handle WhatsApp sharing with file
                ipcRenderer.send('share-whatsapp', {
                    filePath: filePath,
                    phoneNumber: whatsappNumber,
                    billNo: billNo || slipId
                });

                // Show success message
                // alert('📱 WhatsApp Automation Started\\n\\nOpening WhatsApp Desktop...\\nChat: +' + whatsappNumber + '\\nPDF: ' + fileName + '\\n\\nThe PDF will be automatically attached.\\nJust press Send in WhatsApp! 🚀');

            } catch (error) {
                alert('Error preparing WhatsApp share:\\n\\n' + error.message + '\\n\\nPlease try again or contact support.');
                console.error('WhatsApp share error:', error);
            }
        }

        // Add keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'p') {
                e.preventDefault();
                console.log('⌨️  Ctrl+P pressed - triggering print');
                printPDF(); // This now calls the IPC method, not window.print()
            }
        });
    </script>
</body>
</html>
        `;

        // Load the viewer with embedded PDF
        viewerWindow.loadURL('data:text/html;charset=utf-8,' + encodeURIComponent(viewerHTML));

    } catch (error) {
        console.error('Error generating PDF:', error);

        // Clean up print window if it exists
        if (printWindow && !printWindow.isDestroyed()) {
            printWindow.close();
        }

        // Show error dialog to user
        dialog.showErrorBox(
            'Print Error',
            `Failed to generate PDF:\n\n${error.message}\n\nPlease ensure the Flask server is running.`
        );
    }
});
