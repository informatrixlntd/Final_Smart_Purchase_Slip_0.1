const { exec } = require('child_process');
const fs = require('fs');
const path = require('path');
const { google } = require('googleapis');
const { BrowserWindow, shell, ipcMain } = require('electron');

const BACKUP_DIR = path.join(process.env.USERPROFILE || process.env.HOME, 'PurchaseSlipBackups');

// Ensure backup directory exists
if (!fs.existsSync(BACKUP_DIR)) {
    fs.mkdirSync(BACKUP_DIR, { recursive: true });
}

// ----------------------
// CREATE MYSQL BACKUP
// ----------------------
function createMySQLBackup(dbConfig) {
    return new Promise((resolve, reject) => {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const backupFileName = `purchase_slips_backup_${timestamp}.sql`;
        const backupFilePath = path.join(BACKUP_DIR, backupFileName);

        const command = `mysqldump -h ${dbConfig.host} -P ${dbConfig.port} -u ${dbConfig.user} -p${dbConfig.password} ${dbConfig.database} > "${backupFilePath}"`;

        exec(command, (error, stdout, stderr) => {
            if (error) {
                console.error("Backup error:", error);
                reject(error);
                return;
            }

            if (stderr) {
                console.warn("Backup stderr:", stderr);
            }

            console.log("Backup created:", backupFilePath);
            resolve(backupFilePath);
        });
    });
}

// ----------------------
// GOOGLE AUTH (OOB)
// ----------------------
async function authenticateGoogleDrive() {
    return new Promise(async (resolve, reject) => {
        try {
            const oauth2Client = new google.auth.OAuth2(
                "432729181710-4jnntjamivku6a3in4k0vo4ft4ag8vg6.apps.googleusercontent.com",
                "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",
                "http://localhost:5000/" // Desktop approved redirect
            );

            const authUrl = oauth2Client.generateAuthUrl({
                access_type: "offline",
                scope: ["https://www.googleapis.com/auth/drive.file"],
                prompt: "consent"
            });

            // Open Google login flow in default browser
            shell.openExternal(authUrl);

            // ----------------------
            // Prompt window for code input
            // ----------------------
            const promptWindow = new BrowserWindow({
                width: 450,
                height: 220,
                resizable: false,
                title: "Google Authentication",
                webPreferences: {
                    nodeIntegration: true,
                    contextIsolation: false // IMPORTANT - FIXES IPC
                }
            });

            promptWindow.loadURL(`data:text/html,
                <h3>Enter Google Authentication Code</h3>
                <input id="code" style="width:90%;height:35px;font-size:16px;margin-bottom:10px;" />
                <button onclick="submit()" style="width:120px;height:35px;">Submit</button>

                <script>
                    const { ipcRenderer } = require('electron');
                    function submit() {
                        const code = document.getElementById('code').value.trim();
                        ipcRenderer.send('oauth-code', code);
                    }
                </script>
            `);

            // Wait for IPC code from promptWindow
            ipcMain.once("oauth-code", async (event, code) => {
                try {
                    const { tokens } = await oauth2Client.getToken(code);
                    oauth2Client.setCredentials(tokens);
                    promptWindow.close();
                    resolve(oauth2Client);
                } catch (err) {
                    promptWindow.close();
                    reject(err);
                }
            });

        } catch (err) {
            reject(err);
        }
    });
}

// ----------------------
// UPLOAD TO GOOGLE DRIVE
// ----------------------
async function uploadToGoogleDrive(filePath, auth) {
    const drive = google.drive({ version: "v3", auth });

    const fileMetadata = {
        name: path.basename(filePath),
        mimeType: "application/sql"
    };

    const media = {
        mimeType: "application/sql",
        body: fs.createReadStream(filePath)
    };

    try {
        const response = await drive.files.create({
            requestBody: fileMetadata,
            media: media,
            fields: "id,name"
        });

        console.log("File uploaded to Google Drive:", response.data);
        return response.data;
    } catch (error) {
        console.error("Error uploading to Google Drive:", error);
        throw error;
    }
}

// ----------------------
// FULL BACKUP + UPLOAD WORKFLOW
// ----------------------
async function performBackupAndUpload(dbConfig, mainWindow) {
    try {
        mainWindow.webContents.send("backup-status", "Creating database backup...");
        const backupFilePath = await createMySQLBackup(dbConfig);

        mainWindow.webContents.send("backup-status", "Opening Google authentication...");
        const auth = await authenticateGoogleDrive();

        mainWindow.webContents.send("backup-status", "Uploading backup to Google Drive...");
        await uploadToGoogleDrive(backupFilePath, auth);

        mainWindow.webContents.send("backup-success", "Backup completed successfully!");
        return true;

    } catch (error) {
        console.error("Backup failed:", error);
        mainWindow.webContents.send("backup-error", error.message || "Backup failed.");
        return false;
    }
}

module.exports = {
    performBackupAndUpload,
    BACKUP_DIR
};
