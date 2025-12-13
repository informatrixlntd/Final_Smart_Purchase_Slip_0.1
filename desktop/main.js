t the HTML directly using webContents.print()
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
