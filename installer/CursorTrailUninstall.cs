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
            Application.Run(new UninstallForm());
        }
    }

    internal sealed class UninstallForm : Form
    {
        private const string AppName = "CursorTrail";
        private const string DisplayName = "Cursor Trail";

        private ProgressBar progressBar;
        private Label statusLabel;
        private Button removeButton;
        private Button cancelButton;
        private readonly string installDir;

        public UninstallForm()
        {
            installDir = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
            BuildUi();
        }

        private void BuildUi()
        {
            Text = "Удаление Cursor Trail";
            Icon = Icon.ExtractAssociatedIcon(Assembly.GetExecutingAssembly().Location);
            StartPosition = FormStartPosition.CenterScreen;
            FormBorderStyle = FormBorderStyle.FixedSingle;
            MaximizeBox = false;
            ClientSize = new Size(620, 350);
            BackColor = Color.FromArgb(248, 250, 252);
            Font = new Font("Segoe UI", 10F);

            var header = new Panel
            {
                Dock = DockStyle.Top,
                Height = 105,
                BackColor = Color.FromArgb(20, 24, 35)
            };
            Controls.Add(header);

            var iconBox = new PictureBox
            {
                Size = new Size(58, 58),
                Location = new Point(28, 24),
                SizeMode = PictureBoxSizeMode.StretchImage,
                Image = Icon.ToBitmap()
            };
            header.Controls.Add(iconBox);

            var title = new Label
            {
                AutoSize = true,
                Text = "Удаление Cursor Trail",
                ForeColor = Color.White,
                Font = new Font("Segoe UI Semibold", 19F, FontStyle.Bold),
                Location = new Point(105, 25)
            };
            header.Controls.Add(title);

            var subtitle = new Label
            {
                AutoSize = true,
                Text = "Приложение, ярлыки и запись установки будут удалены.",
                ForeColor = Color.FromArgb(190, 205, 230),
                Font = new Font("Segoe UI", 10.5F),
                Location = new Point(108, 66)
            };
            header.Controls.Add(subtitle);

            var bodyText = new Label
            {
                Text = "Cursor Trail установлен в папку:\r\n" + installDir,
                ForeColor = Color.FromArgb(55, 65, 81),
                Location = new Point(34, 135),
                Size = new Size(545, 60)
            };
            Controls.Add(bodyText);

            progressBar = new ProgressBar
            {
                Location = new Point(37, 218),
                Size = new Size(540, 18)
            };
            Controls.Add(progressBar);

            statusLabel = new Label
            {
                Text = "Готов к удалению.",
                ForeColor = Color.FromArgb(75, 85, 99),
                Location = new Point(34, 248),
                Size = new Size(545, 28)
            };
            Controls.Add(statusLabel);

            removeButton = Button("Удалить", new Point(351, 292), true);
            removeButton.Click += RemoveButton_Click;
            Controls.Add(removeButton);

            cancelButton = Button("Отмена", new Point(474, 292), false);
            cancelButton.Click += delegate { Close(); };
            Controls.Add(cancelButton);
        }

        private Button Button(string text, Point location, bool primary)
        {
            var button = new Button
            {
                Text = text,
                Location = location,
                Size = new Size(103, 36),
                FlatStyle = FlatStyle.Flat,
                BackColor = primary ? Color.FromArgb(220, 38, 38) : Color.White,
                ForeColor = primary ? Color.White : Color.FromArgb(31, 41, 55),
                Font = new Font("Segoe UI Semibold", 10F, FontStyle.Bold)
            };
            button.FlatAppearance.BorderColor = Color.FromArgb(209, 213, 219);
            if (primary)
            {
                button.FlatAppearance.BorderSize = 0;
            }
            return button;
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
            progressBar.Value = Math.Max(0, Math.Min(100, progress));
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
