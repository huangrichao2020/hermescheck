const vscode = require("vscode");
const cp = require("child_process");
const fs = require("fs");
const os = require("os");
const path = require("path");

function runCommand(executable, args, cwd, channel) {
  return new Promise((resolve, reject) => {
    channel.appendLine(`$ ${[executable, ...args].join(" ")}`);
    const child = cp.execFile(executable, args, { cwd, maxBuffer: 1024 * 1024 * 20 }, (error, stdout, stderr) => {
      if (stdout) {
        channel.append(stdout);
      }
      if (stderr) {
        channel.append(stderr);
      }
      if (error) {
        reject(error);
        return;
      }
      resolve();
    });
    child.on("error", reject);
  });
}

async function pickWorkspaceFolder() {
  const folders = vscode.workspace.workspaceFolders || [];
  if (folders.length === 0) {
    throw new Error("Open a workspace folder before running HermesCheck.");
  }
  if (folders.length === 1) {
    return folders[0];
  }
  const picked = await vscode.window.showWorkspaceFolderPick({
    placeHolder: "Choose the workspace folder to audit",
  });
  if (!picked) {
    throw new Error("No workspace folder selected.");
  }
  return picked;
}

async function auditWorkspace() {
  const folder = await pickWorkspaceFolder();
  const config = vscode.workspace.getConfiguration("hermescheck");
  const executable = config.get("executable", "hermescheck");
  const profile = config.get("profile", "personal");
  const outDir = fs.mkdtempSync(path.join(os.tmpdir(), "hermescheck-vscode-"));
  const jsonPath = path.join(outDir, "audit_results.json");
  const reportPath = path.join(outDir, "audit_report.md");
  const channel = vscode.window.createOutputChannel("HermesCheck");
  channel.show(true);

  const args = [folder.uri.fsPath, "--profile", profile, "-o", jsonPath, "-r", reportPath];

  await vscode.window.withProgress(
    {
      location: vscode.ProgressLocation.Notification,
      title: "Running HermesCheck",
      cancellable: false,
    },
    async () => {
      await runCommand(executable, args, folder.uri.fsPath, channel);
    },
  );

  const doc = await vscode.workspace.openTextDocument(reportPath);
  await vscode.window.showTextDocument(doc, { preview: false });
  vscode.window.showInformationMessage("HermesCheck audit complete.");
}

function activate(context) {
  context.subscriptions.push(
    vscode.commands.registerCommand("hermescheck.auditWorkspace", async () => {
      try {
        await auditWorkspace();
      } catch (error) {
        vscode.window.showErrorMessage(`HermesCheck failed: ${error.message || error}`);
      }
    }),
  );
}

function deactivate() {}

module.exports = {
  activate,
  deactivate,
};
