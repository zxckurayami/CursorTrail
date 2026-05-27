using System;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Threading.Tasks;
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
            Application.Run(new SetupForm());
        }
    }

    internal sealed class SetupForm : Form
    {
        private const string AppName = "CursorTrail";
        private const string DisplayName = "Cursor Trail";
        private readonly string defaultInstallDir = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
            "Programs",
            AppName);

        private TextBox pathBox;
        private ProgressBar progressBar;
        private Label statusLabel;
        private Button installButton;
        private Button browseButton;
        private Button cancelButton;
        private Button launchButton;
        private string installedExePath;

        public SetupForm()
        {
            BuildUi();
        }

        private void BuildUi()
        {
            Text = "CursorTrail Setup";
            Icon = Icon.ExtractAssociatedIcon(Assembly.GetExecutingAssembly().Location);
            StartPosition = FormStartPosition.CenterScreen;
            FormBorderStyle = FormBorderStyle.FixedSingle;
            MaximizeBox = false;
            MinimizeBox = true;
            ClientSize = new Size(760, 500);
            BackColor = Color.FromArgb(248, 250, 252);
            Font = new Font("Segoe UI", 10F);

            var header = new Panel
            {
                Dock = DockStyle.Top,
                Height = 128,
                BackColor = Color.FromArgb(20, 24, 35)
            };
            Controls.Add(header);

            var iconBox = new PictureBox
            {
                Size = new Size(72, 72),
                Location = new Point(30, 28),
                SizeMode = PictureBoxSizeMode.StretchImage,
                Image = Icon.ToBitmap()
            };
            header.Controls.Add(iconBox);

            var title = new Label
            {
                AutoSize = true,
                Text = "Cursor Trail",
                ForeColor = Color.White,
                Font = new Font("Segoe UI Semibold", 24F, FontStyle.Bold),
                Location = new Point(122, 30)
            };
            header.Controls.Add(title);

            var subtitle = new Label
            {
                AutoSize = true,
                Text = "Установка версии 1.1 для Windows",
                ForeColor = Color.FromArgb(190, 205, 230),
                Font = new Font("Segoe UI", 11F),
                Location = new Point(126, 78)
            };
            header.Controls.Add(subtitle);

            var bodyTitle = new Label
            {
                AutoSize = true,
                Text = "Настраиваемый след курсора",
                ForeColor = Color.FromArgb(24, 29, 39),
                Font = new Font("Segoe UI Semibold", 15F, FontStyle.Bold),
                Location = new Point(34, 158)
            };
            Controls.Add(bodyTitle);

            var bodyText = new Label
            {
                Text = "Установщик добавит приложение в профиль пользователя, создаст ярлыки в меню Пуск и на рабочем столе, а также зарегистрирует удаление через настройки Windows.",
                ForeColor = Color.FromArgb(75, 85, 99),
                Font = new Font("Segoe UI", 10.5F),
                Location = new Point(36, 195),
                Size = new Size(685, 52)
            };
            Controls.Add(bodyText);

            var pathLabel = new Label
            {
                AutoSize = true,
                Text = "Папка установки",
                ForeColor = Color.FromArgb(55, 65, 81),
                Font = new Font("Segoe UI Semibold", 10F, FontStyle.Bold),
                Location = new Point(36, 265)
            };
            Controls.Add(pathLabel);

            pathBox = new TextBox
            {
                Location = new Point(39, 292),
                Size = new Size(560, 30),
                Text = defaultInstallDir
            };
            Controls.Add(pathBox);

            browseButton = SecondaryButton("Обзор", new Point(613, 290), new Size(108, 34));
            browseButton.Click += BrowseButton_Click;
            Controls.Add(browseButton);

            progressBar = new ProgressBar
            {
                Location = new Point(39, 355),
                Size = new Size(682, 18),
                Style = ProgressBarStyle.Continuous
            };
            Controls.Add(progressBar);

            statusLabel = new Label
            {
                Text = "Готов к установке.",
                ForeColor = Color.FromArgb(75, 85, 99),
                Location = new Point(36, 383),
                Size = new Size(685, 28)
            };
            Controls.Add(statusLabel);

            installButton = PrimaryButton("Установить", new Point(473, 435), new Size(120, 38));
            installButton.Click += InstallButton_Click;
            Controls.Add(installButton);

            launchButton = PrimaryButton("Запустить", new Point(473, 435), new Size(120, 38));
            launchButton.Visible = false;
            launchButton.Click += LaunchButton_Click;
            Controls.Add(launchButton);

            cancelButton = SecondaryButton("Отмена", new Point(607, 435), new Size(114, 38));
            cancelButton.Click += delegate { Close(); };
            Controls.Add(cancelButton);
        }

        private Button PrimaryButton(string text, Point location, Size size)
        {
            var button = new Button
            {
                Text = text,
                Location = location,
                Size = size,
                FlatStyle = FlatStyle.Flat,
                BackColor = Color.FromArgb(36, 99, 235),
                ForeColor = Color.White,
                Font = new Font("Segoe UI Semibold", 10F, FontStyle.Bold)
            };
            button.FlatAppearance.BorderSize = 0;
            return button;
        }

        private Button SecondaryButton(string text, Point location, Size size)
        {
            var button = new Button
            {
                Text = text,
                Location = location,
                Size = size,
                FlatStyle = FlatStyle.Flat,
                BackColor = Color.White,
                ForeColor = Color.FromArgb(31, 41, 55),
                Font = new Font("Segoe UI", 10F)
            };
            button.FlatAppearance.BorderColor = Color.FromArgb(209, 213, 219);
            return button;
        }

        private void BrowseButton_Click(object sender, EventArgs e)
        {
            using (var dialog = new FolderBrowserDialog())
            {
                dialog.Description = "Выберите папку установки Cursor Trail";
                dialog.SelectedPath = pathBox.Text;
                if (dialog.ShowDialog(this) == DialogResult.OK)
                {
                    pathBox.Text = dialog.SelectedPath;
                }
            }
        }

        private void InstallButton_Click(object sender, EventArgs e)
        {
            SetControlsEnabled(false);
            progressBar.Value = 0;
            statusLabel.Text = "Подготовка установки...";

            var installDir = pathBox.Text.Trim();
            Task.Factory.StartNew(delegate
            {
                Install(installDir);
            }).ContinueWith(task =>
            {
                BeginInvoke(new Action(delegate
                {
                    if (task.Exception != null)
                    {
                        SetControlsEnabled(true);
                        progressBar.Value = 0;
                        statusLabel.Text = "Ошибка установки.";
                        MessageBox.Show(this, task.Exception.GetBaseException().Message, "CursorTrail Setup", MessageBoxButtons.OK, MessageBoxIcon.Error);
                        return;
                    }

                    progressBar.Value = 100;
                    statusLabel.Text = "Установка завершена.";
                    launchButton.Visible = true;
                    installButton.Visible = false;
                    cancelButton.Text = "Готово";
                    cancelButton.Enabled = true;
                }));
            });
        }

        private void SetControlsEnabled(bool enabled)
        {
            installButton.Enabled = enabled;
            browseButton.Enabled = enabled;
            pathBox.Enabled = enabled;
            cancelButton.Enabled = enabled;
        }

        private void Install(string installDir)
        {
            if (string.IsNullOrWhiteSpace(installDir))
            {
                throw new InvalidOperationException("Папка установки не указана.");
            }

            installedExePath = Path.Combine(installDir, "Cursor Trail.exe");
            Report("Остановка запущенной копии приложения...", 5);
            CloseRunningApplication();

            Report("Подготовка папки установки...", 10);
            if (Directory.Exists(installDir))
            {
                Directory.Delete(installDir, true);
            }
            Directory.CreateDirectory(installDir);

            Report("Распаковка файлов приложения...", 15);
            ExtractPayload(installDir);

            if (!File.Exists(installedExePath))
            {
                throw new FileNotFoundException("Cursor Trail.exe не найден после распаковки.", installedExePath);
            }

            Report("Создание ярлыков...", 88);
            CreateShortcuts(installDir, installedExePath);

            Report("Регистрация приложения в Windows...", 94);
            RegisterUninstall(installDir, installedExePath);

            Report("Готово.", 100);
        }

        private void ExtractPayload(string installDir)
        {
            var assembly = Assembly.GetExecutingAssembly();
            var resourceName = assembly.GetManifestResourceNames().FirstOrDefault(name => name.EndsWith("Payload.zip", StringComparison.OrdinalIgnoreCase));
            if (resourceName == null)
            {
                throw new InvalidOperationException("Встроенный payload не найден.");
            }

            using (var stream = assembly.GetManifestResourceStream(resourceName))
            using (var archive = new ZipArchive(stream, ZipArchiveMode.Read))
            {
                var entries = archive.Entries.Where(entry => !string.IsNullOrEmpty(entry.Name)).ToList();
                for (var i = 0; i < entries.Count; i++)
                {
                    var entry = entries[i];
                    var destinationPath = Path.GetFullPath(Path.Combine(installDir, entry.FullName));
                    var installRoot = Path.GetFullPath(installDir + Path.DirectorySeparatorChar);
                    if (!destinationPath.StartsWith(installRoot, StringComparison.OrdinalIgnoreCase))
                    {
                        throw new InvalidOperationException("Недопустимый путь внутри payload.");
                    }

                    Directory.CreateDirectory(Path.GetDirectoryName(destinationPath));
                    entry.ExtractToFile(destinationPath, true);

                    var progress = 15 + (int)((i + 1) * 68.0 / Math.Max(1, entries.Count));
                    Report("Распаковка файлов приложения... " + (i + 1) + " / " + entries.Count, progress);
                }
            }
        }

        private void CreateShortcuts(string installDir, string exePath)
        {
            var startMenuDir = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.Programs), DisplayName);
            Directory.CreateDirectory(startMenuDir);

            CreateShortcut(
                Path.Combine(startMenuDir, DisplayName + ".lnk"),
                exePath,
                installDir,
                exePath);

            CreateShortcut(
                Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory), DisplayName + ".lnk"),
                exePath,
                installDir,
                exePath);

            var uninstallPath = Path.Combine(installDir, "CursorTrailUninstall.exe");
            if (File.Exists(uninstallPath))
            {
                CreateShortcut(
                    Path.Combine(startMenuDir, "Удалить " + DisplayName + ".lnk"),
                    uninstallPath,
                    installDir,
                    uninstallPath);
            }
        }

        private static void CreateShortcut(string shortcutPath, string targetPath, string workingDirectory, string iconPath)
        {
            var shellType = Type.GetTypeFromProgID("WScript.Shell");
            var shell = Activator.CreateInstance(shellType);
            var shortcut = shellType.InvokeMember("CreateShortcut", BindingFlags.InvokeMethod, null, shell, new object[] { shortcutPath });
            var shortcutType = shortcut.GetType();
            shortcutType.InvokeMember("TargetPath", BindingFlags.SetProperty, null, shortcut, new object[] { targetPath });
            shortcutType.InvokeMember("WorkingDirectory", BindingFlags.SetProperty, null, shortcut, new object[] { workingDirectory });
            shortcutType.InvokeMember("IconLocation", BindingFlags.SetProperty, null, shortcut, new object[] { iconPath });
            shortcutType.InvokeMember("Save", BindingFlags.InvokeMethod, null, shortcut, null);
            Marshal.FinalReleaseComObject(shortcut);
            Marshal.FinalReleaseComObject(shell);
        }

        private static void RegisterUninstall(string installDir, string exePath)
        {
            var uninstallPath = Path.Combine(installDir, "CursorTrailUninstall.exe");
            using (var key = Registry.CurrentUser.CreateSubKey(@"Software\Microsoft\Windows\CurrentVersion\Uninstall\" + AppName))
            {
                key.SetValue("DisplayName", DisplayName);
                key.SetValue("DisplayVersion", "1.1");
                key.SetValue("Publisher", "zxckurayami");
                key.SetValue("InstallLocation", installDir);
                key.SetValue("DisplayIcon", exePath);
                key.SetValue("UninstallString", "\"" + uninstallPath + "\"");
                key.SetValue("NoModify", 1, RegistryValueKind.DWord);
                key.SetValue("NoRepair", 1, RegistryValueKind.DWord);
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

        private void LaunchButton_Click(object sender, EventArgs e)
        {
            if (!string.IsNullOrEmpty(installedExePath) && File.Exists(installedExePath))
            {
                Process.Start(new ProcessStartInfo
                {
                    FileName = installedExePath,
                    WorkingDirectory = Path.GetDirectoryName(installedExePath)
                });
            }
            Close();
        }

        private void Report(string message, int progress)
        {
            BeginInvoke(new Action(delegate
            {
                statusLabel.Text = message;
                progressBar.Value = Math.Max(0, Math.Min(100, progress));
            }));
        }
    }
}
