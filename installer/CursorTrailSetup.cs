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
            try
            {
                Application.Run(new SetupForm());
            }
            catch (Exception ex)
            {
                var logPath = Path.Combine(Path.GetTempPath(), "CursorTrailSetup.log");
                File.WriteAllText(logPath, ex.ToString());
                MessageBox.Show("Не удалось открыть установщик.\r\n\r\nЛог: " + logPath, "CursorTrail Setup", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }
    }

    internal sealed class SetupForm : InstallerShellForm
    {
        private const string AppName = "CursorTrail";
        private const string DisplayName = "Cursor Trail";
        private const string Version = "1.1";

        private readonly string defaultInstallDir = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
            "Programs",
            AppName);

        private TextBox pathBox;
        private ProgressView progressBar;
        private Label statusLabel;
        private AccentButton installButton;
        private AccentButton browseButton;
        private AccentButton cancelButton;
        private AccentButton launchButton;
        private string installedExePath;

        public SetupForm()
        {
            Text = "CursorTrail Setup";
            ClientSize = new Size(840, 560);
            BuildChrome("CursorTrail Setup");
            BuildUi();
        }

        private void BuildUi()
        {
            var header = new HeaderPanel
            {
                Location = new Point(1, 43),
                Size = new Size(ClientSize.Width - 2, 154),
                Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right
            };
            Controls.Add(header);

            var logo = new LogoView
            {
                Image = UiKit.LoadLogoImage(),
                Location = new Point(40, 28),
                Size = new Size(96, 96)
            };
            header.Controls.Add(logo);

            header.Controls.Add(UiKit.MakeLabel("Cursor Trail", 26F, FontStyle.Bold, UiKit.Text, new Point(154, 35), new Size(360, 42)));
            header.Controls.Add(UiKit.MakeLabel("Красивый след курсора. Быстрая установка для Windows.", 10.5F, FontStyle.Regular, UiKit.MutedText, new Point(158, 82), new Size(460, 24)));

            var versionBadge = new RoundedPanel
            {
                Location = new Point(158, 112),
                Size = new Size(116, 28),
                Radius = 14,
                BackColor = Color.FromArgb(36, 36, 43),
                BorderColor = Color.FromArgb(65, 65, 76)
            };
            var versionLabel = UiKit.MakeLabel("версия " + Version, 9F, FontStyle.Bold, UiKit.Text, new Point(0, 0), new Size(116, 28));
            versionLabel.TextAlign = ContentAlignment.MiddleCenter;
            versionBadge.Controls.Add(versionLabel);
            header.Controls.Add(versionBadge);

            var bodyTitle = UiKit.MakeLabel("Установка приложения", 19F, FontStyle.Bold, UiKit.Text, new Point(44, 222), new Size(420, 34));
            Controls.Add(bodyTitle);

            var bodyText = UiKit.MakeLabel(
                "Выберите папку, а установщик аккуратно распакует файлы, создаст ярлыки и добавит удаление через настройки Windows.",
                10.2F,
                FontStyle.Regular,
                UiKit.MutedText,
                new Point(46, 260),
                new Size(700, 44));
            Controls.Add(bodyText);

            AddFeatureChip("Профили", new Point(46, 308));
            AddFeatureChip("RGB Trail", new Point(142, 308));
            AddFeatureChip("Sakura", new Point(248, 308));
            AddFeatureChip("Pixel", new Point(340, 308));

            Controls.Add(UiKit.MakeLabel("Папка установки", 9.5F, FontStyle.Bold, UiKit.MutedText, new Point(46, 356), new Size(180, 22)));

            var inputPanel = new RoundedPanel
            {
                Location = new Point(46, 381),
                Size = new Size(590, 42),
                Radius = 12,
                BackColor = UiKit.Surface2,
                BorderColor = Color.FromArgb(66, 66, 76)
            };
            pathBox = new TextBox
            {
                BorderStyle = BorderStyle.None,
                BackColor = UiKit.Surface2,
                ForeColor = UiKit.Text,
                Font = UiKit.Segoe(10.2F, FontStyle.Regular),
                Location = new Point(14, 11),
                Size = new Size(560, 20),
                Text = defaultInstallDir
            };
            inputPanel.Controls.Add(pathBox);
            Controls.Add(inputPanel);

            browseButton = new AccentButton
            {
                Text = "Обзор",
                Location = new Point(654, 381),
                Size = new Size(130, 42)
            };
            browseButton.Click += BrowseButton_Click;
            Controls.Add(browseButton);

            progressBar = new ProgressView
            {
                Location = new Point(46, 451),
                Size = new Size(738, 16)
            };
            Controls.Add(progressBar);

            statusLabel = UiKit.MakeLabel("Готов к установке.", 9.5F, FontStyle.Regular, UiKit.MutedText, new Point(46, 477), new Size(480, 24));
            Controls.Add(statusLabel);

            installButton = new AccentButton
            {
                Text = "Установить",
                Primary = true,
                Location = new Point(516, 504),
                Size = new Size(130, 40)
            };
            installButton.Click += InstallButton_Click;
            Controls.Add(installButton);

            launchButton = new AccentButton
            {
                Text = "Запустить",
                Primary = true,
                Location = new Point(516, 504),
                Size = new Size(130, 40),
                Visible = false
            };
            launchButton.Click += LaunchButton_Click;
            Controls.Add(launchButton);

            cancelButton = new AccentButton
            {
                Text = "Отмена",
                Location = new Point(662, 504),
                Size = new Size(122, 40)
            };
            cancelButton.Click += delegate { Close(); };
            Controls.Add(cancelButton);
        }

        private void AddFeatureChip(string text, Point location)
        {
            var chip = new RoundedPanel
            {
                Location = location,
                Size = new Size(Math.Max(78, text.Length * 9 + 28), 30),
                Radius = 15,
                BackColor = Color.FromArgb(31, 31, 37),
                BorderColor = Color.FromArgb(56, 56, 66)
            };
            var label = UiKit.MakeLabel(text, 8.5F, FontStyle.Bold, UiKit.Text, new Point(0, 0), new Size(chip.Width, chip.Height));
            label.TextAlign = ContentAlignment.MiddleCenter;
            chip.Controls.Add(label);
            Controls.Add(chip);
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
                if (IsDisposed || !IsHandleCreated)
                {
                    return;
                }

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

            installDir = Path.GetFullPath(installDir);
            installedExePath = Path.Combine(installDir, "Cursor Trail.exe");

            Report("Остановка запущенной копии приложения...", 5);
            CloseRunningApplication();

            Report("Подготовка папки установки...", 10);
            PrepareInstallDirectory(installDir);

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

        private static void PrepareInstallDirectory(string installDir)
        {
            if (IsUnsafeInstallPath(installDir))
            {
                throw new InvalidOperationException("Выберите отдельную папку для Cursor Trail, а не системную или корневую папку.");
            }

            if (!Directory.Exists(installDir))
            {
                Directory.CreateDirectory(installDir);
                return;
            }

            var hasCursorTrailFiles =
                File.Exists(Path.Combine(installDir, "Cursor Trail.exe")) ||
                File.Exists(Path.Combine(installDir, "CursorTrailUninstall.exe")) ||
                Directory.Exists(Path.Combine(installDir, "_internal"));
            var isEmpty = !Directory.EnumerateFileSystemEntries(installDir).Any();

            if (!hasCursorTrailFiles && !isEmpty)
            {
                throw new InvalidOperationException("Выбранная папка не пустая и не похожа на папку Cursor Trail. Выберите отдельную папку установки.");
            }

            Directory.Delete(installDir, true);
            Directory.CreateDirectory(installDir);
        }

        private static bool IsUnsafeInstallPath(string installDir)
        {
            var fullPath = Path.GetFullPath(installDir).TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);
            var root = Path.GetPathRoot(fullPath).TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);
            if (string.Equals(fullPath, root, StringComparison.OrdinalIgnoreCase))
            {
                return true;
            }

            var unsafePaths = new[]
            {
                Environment.GetFolderPath(Environment.SpecialFolder.UserProfile),
                Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory),
                Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments),
                Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles),
                Environment.GetFolderPath(Environment.SpecialFolder.ProgramFilesX86),
                Environment.GetFolderPath(Environment.SpecialFolder.Windows)
            };

            return unsafePaths
                .Where(path => !string.IsNullOrWhiteSpace(path))
                .Select(path => Path.GetFullPath(path).TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar))
                .Any(path => string.Equals(path, fullPath, StringComparison.OrdinalIgnoreCase));
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
                var installRoot = Path.GetFullPath(installDir + Path.DirectorySeparatorChar);
                for (var i = 0; i < entries.Count; i++)
                {
                    var entry = entries[i];
                    var destinationPath = Path.GetFullPath(Path.Combine(installDir, entry.FullName));
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

            var iconPath = Path.Combine(installDir, "icon.ico");
            if (!File.Exists(iconPath))
            {
                iconPath = exePath;
            }

            CreateShortcut(
                Path.Combine(startMenuDir, DisplayName + ".lnk"),
                exePath,
                installDir,
                iconPath);

            CreateShortcut(
                Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory), DisplayName + ".lnk"),
                exePath,
                installDir,
                iconPath);

            var uninstallPath = Path.Combine(installDir, "CursorTrailUninstall.exe");
            if (File.Exists(uninstallPath))
            {
                CreateShortcut(
                    Path.Combine(startMenuDir, "Удалить " + DisplayName + ".lnk"),
                    uninstallPath,
                    installDir,
                    iconPath);
            }
        }

        private static void CreateShortcut(string shortcutPath, string targetPath, string workingDirectory, string iconPath)
        {
            var shellType = Type.GetTypeFromProgID("WScript.Shell");
            if (shellType == null)
            {
                return;
            }

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
            var iconPath = Path.Combine(installDir, "icon.ico");
            if (!File.Exists(iconPath))
            {
                iconPath = exePath;
            }

            using (var key = Registry.CurrentUser.CreateSubKey(@"Software\Microsoft\Windows\CurrentVersion\Uninstall\" + AppName))
            {
                key.SetValue("DisplayName", DisplayName);
                key.SetValue("DisplayVersion", Version);
                key.SetValue("Publisher", "zxckurayami");
                key.SetValue("InstallLocation", installDir);
                key.SetValue("DisplayIcon", iconPath);
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
            if (IsDisposed || !IsHandleCreated)
            {
                return;
            }

            BeginInvoke(new Action(delegate
            {
                statusLabel.Text = message;
                progressBar.Value = progress;
            }));
        }
    }
}
