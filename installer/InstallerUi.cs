using System;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Windows.Forms;

namespace CursorTrailInstaller
{
    internal static class UiKit
    {
        public static readonly Color Background = Color.FromArgb(16, 16, 18);
        public static readonly Color Surface = Color.FromArgb(23, 23, 27);
        public static readonly Color Surface2 = Color.FromArgb(31, 31, 35);
        public static readonly Color Border = Color.FromArgb(31, 31, 35);
        public static readonly Color Text = Color.FromArgb(245, 247, 251);
        public static readonly Color MutedText = Color.FromArgb(176, 176, 184);
        public static readonly Color AccentBlue = Color.FromArgb(245, 245, 245);
        public static readonly Color AccentPink = Color.FromArgb(245, 245, 245);
        public static readonly Color AccentOrange = Color.FromArgb(245, 245, 245);

        public static Font Segoe(float size, FontStyle style)
        {
            return new Font("Segoe UI", size, style);
        }

        public static Label MakeLabel(string text, float size, FontStyle style, Color color, Point location, Size sizeValue)
        {
            return new Label
            {
                Text = text,
                Font = Segoe(size, style),
                ForeColor = color,
                BackColor = Color.Transparent,
                Location = location,
                Size = sizeValue
            };
        }

        public static Icon LoadWindowIcon()
        {
            try
            {
                return Icon.ExtractAssociatedIcon(Assembly.GetExecutingAssembly().Location);
            }
            catch
            {
                return SystemIcons.Application;
            }
        }

        public static Image LoadLogoImage()
        {
            var assembly = Assembly.GetExecutingAssembly();
            var resourceName = assembly.GetManifestResourceNames()
                .FirstOrDefault(name => name.EndsWith("Logo.png", StringComparison.OrdinalIgnoreCase));
            if (resourceName == null)
            {
                return LoadWindowIcon().ToBitmap();
            }

            using (var stream = assembly.GetManifestResourceStream(resourceName))
            {
                return new Bitmap(stream);
            }
        }

        public static GraphicsPath RoundRect(Rectangle bounds, int radius)
        {
            var path = new GraphicsPath();
            radius = Math.Max(0, Math.Min(radius, Math.Min(bounds.Width, bounds.Height) / 2));
            if (radius == 0)
            {
                path.AddRectangle(bounds);
                return path;
            }

            var diameter = radius * 2;
            var arc = new Rectangle(bounds.Location, new Size(diameter, diameter));

            path.AddArc(arc, 180, 90);
            arc.X = bounds.Right - diameter;
            path.AddArc(arc, 270, 90);
            arc.Y = bounds.Bottom - diameter;
            path.AddArc(arc, 0, 90);
            arc.X = bounds.Left;
            path.AddArc(arc, 90, 90);
            path.CloseFigure();
            return path;
        }

        public static void ApplyRoundedRegion(Form form, int radius)
        {
            if (form.Width <= 0 || form.Height <= 0)
            {
                return;
            }

            using (var path = RoundRect(new Rectangle(0, 0, form.Width, form.Height), radius))
            {
                form.Region = new Region(path);
            }
        }

        public static void AttachDrag(Control control, Form form)
        {
            var isDragging = false;
            var dragStart = Point.Empty;

            control.MouseDown += delegate(object sender, MouseEventArgs e)
            {
                if (e.Button != MouseButtons.Left)
                {
                    return;
                }

                isDragging = true;
                dragStart = e.Location;
            };

            control.MouseMove += delegate(object sender, MouseEventArgs e)
            {
                if (!isDragging)
                {
                    return;
                }

                var screenPoint = control.PointToScreen(e.Location);
                form.Location = new Point(screenPoint.X - dragStart.X, screenPoint.Y - dragStart.Y);
            };

            control.MouseUp += delegate
            {
                isDragging = false;
            };
        }

        public static void DrawTrail(Graphics graphics, Rectangle bounds)
        {
        }
    }

    internal class InstallerShellForm : Form
    {
        private const int CornerRadius = 18;
        private Panel titleBar;

        protected InstallerShellForm()
        {
            AutoScaleDimensions = new SizeF(96F, 96F);
            AutoScaleMode = AutoScaleMode.Dpi;
            BackColor = UiKit.Background;
            Font = UiKit.Segoe(10F, FontStyle.Regular);
            FormBorderStyle = FormBorderStyle.None;
            StartPosition = FormStartPosition.CenterScreen;
            DoubleBuffered = true;
            Icon = UiKit.LoadWindowIcon();
        }

        protected void BuildChrome(string title)
        {
            titleBar = new Panel
            {
                Location = new Point(1, 1),
                Size = new Size(ClientSize.Width - 2, 42),
                BackColor = Color.FromArgb(12, 12, 14),
                Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right
            };
            Controls.Add(titleBar);
            UiKit.AttachDrag(titleBar, this);

            var titleLogo = new LogoView
            {
                Image = UiKit.LoadLogoImage(),
                Location = new Point(14, 10),
                Size = new Size(22, 22),
                Glow = false
            };
            titleBar.Controls.Add(titleLogo);

            var titleLabel = UiKit.MakeLabel(title, 9.5F, FontStyle.Regular, UiKit.Text, new Point(42, 11), new Size(360, 20));
            titleBar.Controls.Add(titleLabel);
            UiKit.AttachDrag(titleLabel, this);

            var close = new WindowButton("x")
            {
                Location = new Point(titleBar.Width - 42, 5),
                Anchor = AnchorStyles.Top | AnchorStyles.Right
            };
            close.Click += delegate { Close(); };
            titleBar.Controls.Add(close);

            var minimize = new WindowButton("-")
            {
                Location = new Point(titleBar.Width - 78, 5),
                Anchor = AnchorStyles.Top | AnchorStyles.Right
            };
            minimize.Click += delegate { WindowState = FormWindowState.Minimized; };
            titleBar.Controls.Add(minimize);
        }

        protected override void OnShown(EventArgs e)
        {
            base.OnShown(e);
            UiKit.ApplyRoundedRegion(this, CornerRadius);
        }

        protected override void OnResize(EventArgs e)
        {
            base.OnResize(e);
            UiKit.ApplyRoundedRegion(this, CornerRadius);
        }

        protected override void OnPaint(PaintEventArgs e)
        {
            base.OnPaint(e);
            e.Graphics.SmoothingMode = SmoothingMode.AntiAlias;
            var rect = new Rectangle(0, 0, Width - 1, Height - 1);
            using (var path = UiKit.RoundRect(rect, CornerRadius))
            using (var fill = new SolidBrush(UiKit.Background))
            using (var border = new Pen(UiKit.Border))
            {
                e.Graphics.FillPath(fill, path);
                e.Graphics.DrawPath(border, path);
            }
        }
    }

    internal sealed class HeaderPanel : Panel
    {
        public HeaderPanel()
        {
            DoubleBuffered = true;
            BackColor = Color.Transparent;
        }

        protected override void OnPaint(PaintEventArgs e)
        {
            base.OnPaint(e);
            var rect = ClientRectangle;
            using (var brush = new SolidBrush(Color.FromArgb(20, 20, 23)))
            {
                e.Graphics.FillRectangle(brush, rect);
            }

            using (var soft = new LinearGradientBrush(rect, Color.FromArgb(16, 255, 255, 255), Color.FromArgb(0, 255, 255, 255), 90F))
            {
                e.Graphics.FillRectangle(soft, rect);
            }

            using (var pen = new Pen(Color.FromArgb(30, 255, 255, 255)))
            {
                e.Graphics.DrawLine(pen, rect.Left, rect.Bottom - 1, rect.Right, rect.Bottom - 1);
            }
        }
    }

    internal sealed class LogoView : Control
    {
        public Image Image { get; set; }
        public bool Glow { get; set; }

        public LogoView()
        {
            DoubleBuffered = true;
            Glow = false;
            SetStyle(ControlStyles.SupportsTransparentBackColor, true);
            BackColor = Color.Transparent;
        }

        protected override void OnPaint(PaintEventArgs e)
        {
            base.OnPaint(e);
            e.Graphics.SmoothingMode = SmoothingMode.AntiAlias;
            e.Graphics.InterpolationMode = InterpolationMode.HighQualityBicubic;
            e.Graphics.PixelOffsetMode = PixelOffsetMode.HighQuality;

            var rect = ClientRectangle;
            if (Glow)
            {
                using (var blue = new SolidBrush(Color.FromArgb(18, 255, 255, 255)))
                using (var pink = new SolidBrush(Color.FromArgb(12, 255, 255, 255)))
                {
                    e.Graphics.FillEllipse(blue, new Rectangle(rect.Left + 3, rect.Top + 8, rect.Width - 6, rect.Height - 10));
                    e.Graphics.FillEllipse(pink, new Rectangle(rect.Left + 13, rect.Top + 3, rect.Width - 20, rect.Height - 18));
                }
            }

            if (Image == null)
            {
                return;
            }

            var target = Fit(Image.Size, rect, 0);
            e.Graphics.DrawImage(Image, target);
        }

        private static Rectangle Fit(Size source, Rectangle bounds, int padding)
        {
            var available = new Rectangle(bounds.X + padding, bounds.Y + padding, bounds.Width - padding * 2, bounds.Height - padding * 2);
            var scale = Math.Min((float)available.Width / source.Width, (float)available.Height / source.Height);
            var width = (int)Math.Round(source.Width * scale);
            var height = (int)Math.Round(source.Height * scale);
            return new Rectangle(available.X + (available.Width - width) / 2, available.Y + (available.Height - height) / 2, width, height);
        }
    }

    internal sealed class ProgressView : Control
    {
        private int value;

        public int Value
        {
            get { return value; }
            set
            {
                this.value = Math.Max(0, Math.Min(100, value));
                Invalidate();
            }
        }

        public ProgressView()
        {
            DoubleBuffered = true;
            SetStyle(ControlStyles.SupportsTransparentBackColor, true);
            BackColor = Color.Transparent;
            Height = 16;
        }

        protected override void OnPaint(PaintEventArgs e)
        {
            base.OnPaint(e);
            e.Graphics.SmoothingMode = SmoothingMode.AntiAlias;
            var track = new Rectangle(0, 0, Width - 1, Height - 1);
            using (var path = UiKit.RoundRect(track, Height / 2))
            using (var background = new SolidBrush(Color.FromArgb(42, 42, 48)))
            {
                e.Graphics.FillPath(background, path);
            }

            var fillWidth = (int)Math.Round((Width - 1) * (Value / 100.0));
            if (fillWidth <= 0)
            {
                return;
            }

            var fill = new Rectangle(0, 0, fillWidth, Height - 1);
            using (var path = UiKit.RoundRect(fill, Height / 2))
            using (var brush = new SolidBrush(Color.FromArgb(236, 236, 240)))
            {
                e.Graphics.FillPath(brush, path);
            }
        }
    }

    internal sealed class PathField : Control
    {
        private bool hovered;
        private string pathText;

        public string PathText
        {
            get { return pathText; }
            set
            {
                pathText = value ?? string.Empty;
                Invalidate();
            }
        }

        public PathField()
        {
            SetStyle(ControlStyles.SupportsTransparentBackColor, true);
            SetStyle(ControlStyles.UserPaint | ControlStyles.AllPaintingInWmPaint | ControlStyles.OptimizedDoubleBuffer, true);
            BackColor = Color.Transparent;
            Cursor = Cursors.Hand;
            Font = UiKit.Segoe(10.2F, FontStyle.Regular);
            Size = new Size(590, 42);
        }

        protected override void OnMouseEnter(EventArgs e)
        {
            hovered = true;
            Invalidate();
            base.OnMouseEnter(e);
        }

        protected override void OnMouseLeave(EventArgs e)
        {
            hovered = false;
            Invalidate();
            base.OnMouseLeave(e);
        }

        protected override void OnPaint(PaintEventArgs e)
        {
            e.Graphics.SmoothingMode = SmoothingMode.AntiAlias;
            var rect = new Rectangle(0, 0, Width - 1, Height - 1);
            var fillColor = Enabled
                ? (hovered ? Color.FromArgb(38, 38, 42) : Color.FromArgb(32, 32, 36))
                : Color.FromArgb(27, 27, 31);

            using (var path = UiKit.RoundRect(rect, 12))
            using (var fill = new SolidBrush(fillColor))
            {
                e.Graphics.FillPath(fill, path);
            }

            var textRect = new Rectangle(14, 0, Width - 28, Height);
            TextRenderer.DrawText(
                e.Graphics,
                PathText,
                Font,
                textRect,
                Enabled ? UiKit.Text : Color.FromArgb(120, 120, 128),
                TextFormatFlags.Left | TextFormatFlags.VerticalCenter | TextFormatFlags.EndEllipsis | TextFormatFlags.NoPrefix);
        }

        protected override void OnPaintBackground(PaintEventArgs pevent)
        {
        }
    }

    internal sealed class RoundedPanel : Panel
    {
        public int Radius { get; set; }
        public Color BorderColor { get; set; }

        public RoundedPanel()
        {
            Radius = 12;
            BorderColor = UiKit.Border;
            BackColor = UiKit.Surface2;
            DoubleBuffered = true;
            SetStyle(ControlStyles.SupportsTransparentBackColor, true);
        }

        protected override void OnPaint(PaintEventArgs e)
        {
            e.Graphics.SmoothingMode = SmoothingMode.AntiAlias;
            var rect = new Rectangle(0, 0, Width - 1, Height - 1);
            using (var path = UiKit.RoundRect(rect, Radius))
            using (var fill = new SolidBrush(BackColor))
            using (var pen = new Pen(BorderColor))
            {
                e.Graphics.FillPath(fill, path);
                if (BorderColor.A > 0 && BorderColor.ToArgb() != BackColor.ToArgb())
                {
                    e.Graphics.DrawPath(pen, path);
                }
            }
        }

        protected override void OnPaintBackground(PaintEventArgs e)
        {
        }
    }

    internal sealed class AccentButton : Control
    {
        private bool hovered;
        private bool pressed;

        public bool Primary { get; set; }
        public bool Danger { get; set; }

        public AccentButton()
        {
            SetStyle(ControlStyles.SupportsTransparentBackColor, true);
            SetStyle(ControlStyles.UserPaint | ControlStyles.AllPaintingInWmPaint | ControlStyles.OptimizedDoubleBuffer, true);
            BackColor = Color.Transparent;
            ForeColor = UiKit.Text;
            Font = UiKit.Segoe(10F, FontStyle.Bold);
            Cursor = Cursors.Hand;
            Size = new Size(128, 40);
        }

        protected override void OnMouseEnter(EventArgs e)
        {
            hovered = true;
            Invalidate();
            base.OnMouseEnter(e);
        }

        protected override void OnMouseLeave(EventArgs e)
        {
            hovered = false;
            pressed = false;
            Invalidate();
            base.OnMouseLeave(e);
        }

        protected override void OnMouseDown(MouseEventArgs mevent)
        {
            pressed = true;
            Invalidate();
            base.OnMouseDown(mevent);
        }

        protected override void OnMouseUp(MouseEventArgs mevent)
        {
            pressed = false;
            Invalidate();
            base.OnMouseUp(mevent);
        }

        protected override void OnPaint(PaintEventArgs e)
        {
            e.Graphics.SmoothingMode = SmoothingMode.AntiAlias;
            var rect = new Rectangle(0, 0, Width - 1, Height - 1);

            if (Primary || Danger)
            {
                var left = Color.FromArgb(238, 238, 242);
                var right = Color.FromArgb(238, 238, 242);
                if (!Enabled)
                {
                    left = Color.FromArgb(72, 72, 78);
                    right = Color.FromArgb(72, 72, 78);
                }
                else if (pressed)
                {
                    left = Color.FromArgb(210, 210, 216);
                    right = Color.FromArgb(210, 210, 216);
                }
                else if (hovered)
                {
                    left = Color.White;
                    right = Color.White;
                }

                using (var path = UiKit.RoundRect(rect, 11))
                using (var brush = new LinearGradientBrush(rect, left, right, 0F))
                {
                    e.Graphics.FillPath(brush, path);
                }
            }
            else
            {
                var fillColor = hovered ? Color.FromArgb(42, 42, 47) : UiKit.Surface2;
                if (pressed)
                {
                    fillColor = Color.FromArgb(27, 27, 31);
                }

                using (var path = UiKit.RoundRect(rect, 11))
                using (var fill = new SolidBrush(fillColor))
                {
                    e.Graphics.FillPath(fill, path);
                }
            }

            var textColor = Enabled
                ? (Primary || Danger ? Color.FromArgb(18, 18, 20) : UiKit.Text)
                : Color.FromArgb(120, 120, 128);

            TextRenderer.DrawText(
                e.Graphics,
                Text,
                Font,
                rect,
                textColor,
                TextFormatFlags.HorizontalCenter | TextFormatFlags.VerticalCenter | TextFormatFlags.EndEllipsis);
        }

        protected override void OnPaintBackground(PaintEventArgs pevent)
        {
        }
    }

    internal sealed class WindowButton : Control
    {
        private bool hovered;

        public WindowButton(string text)
        {
            SetStyle(ControlStyles.SupportsTransparentBackColor, true);
            SetStyle(ControlStyles.UserPaint | ControlStyles.AllPaintingInWmPaint | ControlStyles.OptimizedDoubleBuffer, true);
            Text = text;
            BackColor = Color.Transparent;
            ForeColor = UiKit.MutedText;
            Font = UiKit.Segoe(11F, FontStyle.Regular);
            Size = new Size(34, 32);
            Cursor = Cursors.Hand;
        }

        protected override void OnMouseEnter(EventArgs e)
        {
            hovered = true;
            Invalidate();
            base.OnMouseEnter(e);
        }

        protected override void OnMouseLeave(EventArgs e)
        {
            hovered = false;
            Invalidate();
            base.OnMouseLeave(e);
        }

        protected override void OnPaint(PaintEventArgs e)
        {
            e.Graphics.SmoothingMode = SmoothingMode.AntiAlias;
            var rect = new Rectangle(0, 0, Width - 1, Height - 1);
            if (hovered)
            {
                using (var path = UiKit.RoundRect(rect, 8))
                using (var fill = new SolidBrush(Color.FromArgb(35, 35, 39)))
                {
                    e.Graphics.FillPath(fill, path);
                }
            }

            using (var pen = new Pen(hovered ? Color.White : UiKit.MutedText, 1.6F))
            {
                pen.StartCap = LineCap.Round;
                pen.EndCap = LineCap.Round;
                if (Text == "-")
                {
                    e.Graphics.DrawLine(pen, 11, 17, 23, 17);
                }
                else
                {
                    e.Graphics.DrawLine(pen, 12, 11, 22, 21);
                    e.Graphics.DrawLine(pen, 22, 11, 12, 21);
                }
            }
        }

        protected override void OnPaintBackground(PaintEventArgs pevent)
        {
        }
    }
}
