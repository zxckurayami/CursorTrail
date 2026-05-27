using System;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Reflection;
using System.Text;
using System.Windows.Forms;
using Microsoft.Win32;

namespace CursorTrailInstaller
{
    internal static class Program
    {
        [STAThread]
        private static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            try
            {
                Application.Run(new UninstallForm());
            }
            catch (Exception ex)
            {
                var logPath = Path.Combine(Path.GetTempPath(), "CursorTrailUninstall.log");
                File.WriteAllText(logPath, ex.ToString());
                MessageBox.Show("Не удалось открыть удаление Cursor Trail.\r\n\r\nЛог: " + logPath, "Cursor Trail", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }
    }

    internal sealed class UninstallForm : InstallerShellForm
    {
        private const string AppName = "CursorTrail";
        private const string DisplayName = "Cursor Trail";

        private readonly string installDir;
        private ProgressView progressBar;
        private Label statusLabel;
        private AccentButton removeButton;
        private AccentButton cancelButton;

        public UninstallForm()
        {
            installDir = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
            Text = "Удаление Cursor Trail";
            ClientSize = new Size(720, 430);
            BuildChrome("Cursor Trail Uninstall");
            BuildUi();
        }

        private void BuildUi()
        {
            var header = new HeaderPanel
            {
                Location = new Point(1, 43),
                Size = new Size(ClientSize.Width - 2, 132),
                Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right
            };
            Controls.Add(header);

            var logo = new LogoView
            {
                Image = UiKit.LoadLogoImage(),
                Location = new Point(38, 24),
                Size = new Size(72, 72),
                Glow = false
            };
            header.Controls.Add(logo);

            header.Controls.Add(UiKit.MakeLabel("Удаление Cursor Trail", 22F, FontStyle.Bold, UiKit.Text, new Point(138, 34), new Size(430, 34)));
            header.Controls.Add(UiKit.MakeLabel("Удалим ярлыки, файлы приложения и запись установки Windows.", 10F, FontStyle.Regular, UiKit.MutedText, new Point(141, 76), new Size(500, 24)));

            Controls.Add(UiKit.MakeLabel("Папка приложения", 9.5F, FontStyle.Bold, UiKit.MutedText, new Point(44, 210), new Size(180, 22)));

            var pathPanel = new RoundedPanel
            {
                Location = new Point(44, 238),
                Size = new Size(632, 54),
                Radius = 12,
                BackColor = Color.FromArgb(32, 32, 36),
                BorderColor = Color.FromArgb(32, 32, 36)
            };
            pathPanel.Controls.Add(UiKit.MakeLabel(installDir, 9.5F, FontStyle.Regular, UiKit.Text, new Point(14, 17), new Size(604, 22)));
            Controls.Add(pathPanel);

            progressBar = new ProgressView
            {
                Location = new Point(44, 322),
                Size = new Size(632, 16)
            };
            Controls.Add(progressBar);

            statusLabel = UiKit.MakeLabel("Готов к удалению.", 9.5F, FontStyle.Regular, UiKit.MutedText, new Point(44, 350), new Size(420, 24));
            Controls.Add(statusLabel);

            removeButton = new AccentButton
            {
                Text = "Удалить",
                Danger = true,
                Location = new Point(430, 374),
                Size = new Size(116, 40)
            };
            removeButton.Click += RemoveButton_Click;
            Controls.Add(removeButton);

            cancelButton = new AccentButton
            {
                Text = "Отмена",
                Location = new Point(560, 374),
                Size = new Size(116, 40)
            };
            cancelButton.Click += delegate { Close(); };
            Controls.Add(cancelButton);
        }

        private void RemoveButton_Click(object sender, EventArgs e)
        {
            var answer = MessageBox.Show(this, "Удалить Cursor Trail с этого компьютера?", "Cursor Trail", MessageBoxButtons.YesNo, MessageBoxIcon.Question);
            if (answer != DialogResult.Yes)
            {
                return;
            }

            removeButton.Enabled = false;
            cancelButton.Enabled = false;

            try
            {
                CloseRunningApplication();
                Report("Удаление ярлыков...", 25);
                DeleteShortcuts();

                Report("Удаление записи установки...", 50);
                Registry.CurrentUser.DeleteSubKeyTree(@"Software\Microsoft\Windows\CurrentVersion\Uninstall\" + AppName, false);

                Report("Удаление файлов приложения...", 75);
                ScheduleSelfDelete();

                Report("Удаление завершено.", 100);
                cancelButton.Text = "Готово";
                cancelButton.Enabled = true;
            }
            catch (Exception ex)
            {
                cancelButton.Enabled = true;
                removeButton.Enabled = true;
                statusLabel.Text = "Ошибка удаления.";
                MessageBox.Show(this, ex.Message, "Cursor Trail", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        private void Report(string text, int progress)
        {
            statusLabel.Text = text;
            progressBar.Value = progress;
            Application.DoEvents();
        }

        private static void DeleteShortcuts()
        {
            var desktopShortcut = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory), DisplayName + ".lnk");
            if (File.Exists(desktopShortcut))
            {
                File.Delete(desktopShortcut);
            }

            var startMenuDir = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.Programs), DisplayName);
            if (Directory.Exists(startMenuDir))
            {
                Directory.Delete(startMenuDir, true);
            }
        }

        private static void CloseRunningApplication()
        {
            foreach (var process in Process.GetProcessesByName("Cursor Trail"))
            {
                try
                {
                    process.CloseMainWindow();
                    if (!process.WaitForExit(2500))
                    {
                        process.Kill();
                    }
                }
                catch
                {
                }
            }
        }

        private void ScheduleSelfDelete()
        {
            var escapedInstallDir = installDir.Replace("'", "''");
            var currentProcessId = Process.GetCurrentProcess().Id;
            var command = "$ErrorActionPreference='SilentlyContinue'; Wait-Process -Id " + currentProcessId + " -Timeout 60; Remove-Item -LiteralPath '" + escapedInstallDir + "' -Recurse -Force";
            var encodedCommand = Convert.ToBase64String(Encoding.Unicode.GetBytes(command));
            Process.Start(new ProcessStartInfo
            {
                FileName = "powershell.exe",
                Arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -EncodedCommand " + encodedCommand,
                CreateNoWindow = true,
                WindowStyle = ProcessWindowStyle.Hidden,
                UseShellExecute = false
            });
        }
    }
}
