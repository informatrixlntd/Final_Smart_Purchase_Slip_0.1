const { exec } = require('child_process');
const fs = require('fs');
const path = require('path');
const http = require('http');
const { google } = require('googleapis');
const { shell } = require('electron');

// ----------------------------
// CONFIG
// ----------------------------
const BACKUP_DIR = path.join(
    process.env.USERPROFILE || process.env.HOME,
    'Documents',
    'smart_purchase_slip_backup'
);

const TOKEN_PATH = path.join(__dirname, "tokens.json"); // token storage

const CLIENT_ID = "432729181710-4jnntjamivku6a3in4k0vo4ft4ag8vg6.apps.googleusercontent.com";
const CLIENT_SECRET = "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";
const REDIRECT_URI = "http://localhost:5000";

// Ensure backup folder exists
if (!fs.existsSync(BACKUP_DIR)) {
    fs.mkdirSync(BACKUP_DIR, { recursive: true });
}

// ---------------------------------------------------------
// CREATE MYSQL BACKUP
// ---------------------------------------------------------
function createMySQLBackup(dbConfig) {
    return new Promise((resolve, reject) => {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const backupFileName = `purchase_slips_backup_${timestamp}.sql`;
        const backupFilePath = path.join(BACKUP_DIR, backupFileName);

        const command = `mysqldump -h ${dbConfig.host} -P ${dbConfig.port} -u ${dbConfig.user} -p${dbConfig.password} ${dbConfig.database} > "${backupFilePath}"`;

        exec(command, (error) => {
            if (error) return reject(error);
            resolve(backupFilePath);
        });
    });
}

// ---------------------------------------------------------
// LOAD SAVED TOKENS (if available)
// ---------------------------------------------------------
function loadSavedTokens() {
    try {
        if (fs.existsSync(TOKEN_PATH)) {
            const tokens = JSON.parse(fs.readFileSync(TOKEN_PATH, "utf8"));
            return tokens;
        }
    } catch (e) {
        console.error("Failed to load saved tokens", e);
    }
    return null;
}

// ---------------------------------------------------------
// SAVE TOKENS TO FILE
// ---------------------------------------------------------
function saveTokens(tokens) {
    try {
        fs.writeFileSync(TOKEN_PATH, JSON.stringify(tokens, null, 2), "utf8");
        console.log("Tokens saved.");
    } catch (err) {
        console.error("Failed to save tokens:", err);
    }
}

// ---------------------------------------------------------
// CREATE GOOGLE OAUTH CLIENT
// ---------------------------------------------------------
function createOAuthClient() {
    const oauth2Client = new google.auth.OAuth2(
        CLIENT_ID,
        CLIENT_SECRET,
        REDIRECT_URI
    );

    const saved = loadSavedTokens();
    if (saved) {
        console.log("Using saved tokens.");
        oauth2Client.setCredentials(saved);
    }

    // Auto-save refresh tokens whenever Google refreshes them
    oauth2Client.on("tokens", (tokens) => {
        const current = oauth2Client.credentials;
        const merged = { ...current, ...tokens };
        saveTokens(merged);
    });

    return oauth2Client;
}

// ---------------------------------------------------------
// FULL AUTOMATIC GOOGLE LOGIN (No copy–paste)
// ---------------------------------------------------------
async function authenticateGoogleDrive(mainWindow) {
    return new Promise((resolve, reject) => {
        const oauth2Client = createOAuthClient();

        // If we already have valid tokens → skip login
        if (oauth2Client.credentials && oauth2Client.credentials.access_token) {
            console.log("Already authenticated with Google.");
            return resolve(oauth2Client);
        }

        console.log("No valid tokens found -> Starting authentication flow...");

        const authUrl = oauth2Client.generateAuthUrl({
            access_type: "offline",
            scope: ["https://www.googleapis.com/auth/drive.file"],
            prompt: "consent"
        });

        // Open Google login
        shell.openExternal(authUrl);

        // Start local server to capture redirect
        const server = http.createServer(async (req, res) => {
            try {
                const urlObj = new URL(req.url, REDIRECT_URI);
                const code = urlObj.searchParams.get("code");

                if (!code) {
                    res.end("Invalid request");
                    return;
                }

                res.end("<h2>Authentication successful! You can close this window.</h2>");
                server.close();

                const { tokens } = await oauth2Client.getToken(code);
                oauth2Client.setCredentials(tokens);
                saveTokens(tokens);

                resolve(oauth2Client);
            } catch (err) {
                res.end("<h2>Authentication failed</h2>");
                server.close();
                reject(err);
            }
        });

        server.listen(5000, () => {
            console.log("OAuth redirect listener running on http://localhost:5000");
        });
    });
}

// ---------------------------------------------------------
// UPLOAD TO GOOGLE DRIVE
// ---------------------------------------------------------
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

    const result = await drive.files.create({
        requestBody: fileMetadata,
        media,
        fields: "id,name"
    });

    return result.data;
}

// ---------------------------------------------------------
// FULL WORKFLOW
// ---------------------------------------------------------
async function performBackupAndUpload(dbConfig, mainWindow) {
    try {
        mainWindow.webContents.send("backup-status", "Creating MySQL backup...");
        const backupFilePath = await createMySQLBackup(dbConfig);

        mainWindow.webContents.send("backup-status", "Authenticating with Google...");
        const auth = await authenticateGoogleDrive(mainWindow);

        mainWindow.webContents.send("backup-status", "Uploading backup to Google Drive...");
        await uploadToGoogleDrive(backupFilePath, auth);

        mainWindow.webContents.send("backup-success", "Backup successfully uploaded to Google Drive!");
        return true;
    } catch (error) {
        console.error(error);
        mainWindow.webContents.send("backup-error", error.message || "Backup failed.");
        return false;
    }
}

module.exports = {
    performBackupAndUpload,
    BACKUP_DIR
};
