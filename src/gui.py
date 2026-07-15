import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess
import webbrowser
import json
import os
import sys
import ctypes

# 高DPI适配
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    pass

# 隐藏子进程 cmd 黑窗
CREATE_NO_WINDOW = 0x08000000

# ========== 路径工具 ==========

def get_app_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_config_path():
    app_path = get_app_path()
    for p in [os.path.join(app_path, "config.json"),
              os.path.join(app_path, "resources", "config.json")]:
        if os.path.exists(p):
            return p
    return os.path.join(app_path, "config.json")





# ========== 主题色 ==========

C_PRIMARY   = "#1a73e8"
C_SUCCESS   = "#34a853"
C_WARNING   = "#fbbc04"
C_DANGER    = "#ea4335"
C_BG        = "#ffffff"
C_CARD_BG   = "#ffffff"
C_TEXT      = "#202124"
C_MUTED     = "#5f6368"
C_BORDER    = "#ffffff"

FONT_TITLE  = ("Microsoft YaHei", 14, "bold")
FONT_HEAD   = ("Microsoft YaHei", 11, "bold")
FONT_BODY   = ("Microsoft YaHei", 10)
FONT_SMALL  = ("Microsoft YaHei", 9)
FONT_MONO   = ("Consolas", 9)


# ========== 任务栏固定 ==========

def ensure_taskbar_pinned():
    """首次运行时将程序固定到任务栏"""
    config_path = get_config_path()
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except:
        config = {}

    if config.get('taskbar_pinned'):
        return

    try:
        app_path = get_app_path()
        shortcut_name = 'BJTUAutoLogin.lnk'
        shortcut_path = os.path.join(app_path, shortcut_name)

        if getattr(sys, 'frozen', False):
            target = sys.executable
            working_dir = os.path.dirname(sys.executable)
        else:
            target = os.path.join(app_path, 'run_gui.bat')
            working_dir = app_path

        icon_path = os.path.join(app_path, 'resources', 'icon.ico')
        if not os.path.exists(icon_path):
            icon_path = os.path.join(app_path, 'icon.ico')

        ps = f'''
$ws = New-Object -ComObject WScript.Shell
$s = $ws.CreateShortcut("{shortcut_path}")
$s.TargetPath = "{target}"
$s.WorkingDirectory = "{working_dir}"
$s.Description = "BJTU校园网自动登录"
$s.IconLocation = "{icon_path}"
$s.Save()

$shell = New-Object -ComObject Shell.Application
$folder = $shell.Namespace("{working_dir}")
$item = $folder.ParseName("{shortcut_name}")
if ($item) {{
    try {{ $item.InvokeVerb("taskbarpin") }} catch {{}}
}}
'''
        subprocess.run(
            ['powershell', '-NoProfile', '-Command', ps],
            capture_output=True,
            creationflags=CREATE_NO_WINDOW,
            timeout=10
        )

        config['taskbar_pinned'] = True
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except:
        pass  # 静默失败，不影响核心功能


# ========== 自定义组件 ==========

class StatusDot(ttk.Frame):
    """带状态点的标签"""
    def __init__(self, parent, text="", **kw):
        super().__init__(parent, **kw)
        self.dot = tk.Canvas(self, width=14, height=14, bg=C_BG,
                             highlightthickness=0)
        self.dot.pack(side=tk.LEFT, padx=(0, 6))
        self.dot_id = self.dot.create_oval(2, 2, 12, 12, fill=C_MUTED, outline="")
        self.label = ttk.Label(self, text=text, font=FONT_BODY)
        self.label.pack(side=tk.LEFT)
        self._status = "unknown"

    def set_status(self, status):
        if status == self._status:
            return
        self._status = status
        color = {"connected": C_SUCCESS, "disconnected": C_DANGER,
                 "online": C_SUCCESS, "offline": C_DANGER,
                 "unknown": C_MUTED, "checking": C_WARNING}.get(status, C_MUTED)
        self.dot.itemconfig(self.dot_id, fill=color)


# ========== 主窗口 ==========

class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("BJTU 校园网自动登录")
        self.root.geometry("550x780")
        self.root.resizable(False, False)
        self.root.configure(bg=C_BG)

        # 图标 — 同时设置窗口角标和任务栏图标
        try:
            paths = [os.path.join(get_app_path(), f)
                     for f in ("icon.ico", "resources/icon.ico")]
            ico_path = None
            for p in paths:
                if os.path.exists(p):
                    ico_path = p
                    break

            if ico_path:
                # 设置任务栏图标
                self.root.iconbitmap(ico_path)

                # 设置窗口左上角图标 (iconphoto 需要 PhotoImage)
                try:
                    from PIL import Image, ImageTk
                    img = Image.open(ico_path)
                    photo = ImageTk.PhotoImage(img)
                    self.root.iconphoto(True, photo)
                    self._icon_photo = photo  # 保持引用防止 GC
                except ImportError:
                    pass  # 无 PIL 时仅靠 iconbitmap
        except:
            pass

        # 数据
        self.config = self.load_config()

        # 绑定样式
        self._setup_style()

        # 构建界面
        self._build()

        self.update_timer = None
        self.start_updates()

    # ---------- 样式 ----------

    def _setup_style(self):
        style = ttk.Style()
        style.theme_use("clam")

        # 所有 ttk 组件统一白色背景
        style.configure(".", background="#ffffff", fieldbackground="#ffffff")
        style.configure("TFrame", background="#ffffff")
        style.configure("TLabel", background="#ffffff")
        style.configure("TButton", background="#ffffff")
        style.configure("TCheckbutton", background="#ffffff")

        style.configure("Primary.TButton", font=FONT_BODY,
                        background=C_PRIMARY, foreground="white",
                        borderwidth=0, padding=(16, 7))
        style.map("Primary.TButton",
                  background=[("active", "#1557b0")])
        style.configure("Outline.TButton", font=FONT_BODY,
                        background=C_CARD_BG, foreground=C_PRIMARY,
                        bordercolor=C_PRIMARY, borderwidth=1,
                        padding=(14, 6))
        style.map("Outline.TButton",
                  background=[("active", "#e8f0fe")])

    # ---------- 配置 ----------

    def load_config(self):
        try:
            with open(get_config_path(), "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {"username": "", "password": "",
                    "check_interval": 60, "retry_interval": 10,
                    "test_url": "https://www.baidu.com",
                    "close_action": "ask", "close_remember": False,
                    "taskbar_pinned": False}

    def save_config(self):
        try:
            with open(get_config_path(), "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            messagebox.showerror("错误", f"保存配置失败：{e}")
            return False

    # ---------- 界面构建 ----------

    def _build(self):
        main = ttk.Frame(self.root, padding="20 20 20 10")
        main.pack(fill=tk.BOTH, expand=True)

        # ---------- 顶部标题 ----------
        header = tk.Frame(main, bg=C_BG)
        header.pack(pady=(0, 16), fill=tk.X)

        tk.Label(header, text="BJTU", font=("Microsoft YaHei", 22, "bold"),
                 fg=C_PRIMARY, bg=C_BG).pack(side=tk.LEFT)
        tk.Label(header, text="校园网自动登录", font=FONT_TITLE,
                 fg=C_TEXT, bg=C_BG).pack(side=tk.LEFT, padx=(6, 0))

        # ---------- 卡片 1: 账号配置 ----------
        self._build_account_card(main)

        # ---------- 卡片 2: 连接状态 ----------
        self._build_status_card(main)

        # ---------- 卡片 3: 设置 ----------
        self._build_settings_card(main)

        # ---------- 按钮行 ----------
        self._build_buttons(main)

        # ---------- 日志 ----------
        self._build_log(main)

    def _build_account_card(self, parent):
        frame = tk.Frame(parent, bg=C_CARD_BG)
        frame.pack(fill=tk.X, pady=(0, 10))

        # 学号
        row1 = ttk.Frame(frame)
        row1.pack(fill=tk.X, pady=3)
        ttk.Label(row1, text="学号", font=FONT_BODY,
                  foreground=C_MUTED, width=6).pack(side=tk.LEFT)
        self.username_var = tk.StringVar(value=self.config.get("username", ""))
        tk.Entry(row1, textvariable=self.username_var, font=FONT_BODY, width=18,
                 relief="solid", bd=1, highlightthickness=0,
                 highlightbackground=C_BORDER, highlightcolor=C_PRIMARY
                 ).pack(side=tk.LEFT, padx=(6, 0), ipady=2)
        # 补位空白
        ttk.Label(row1, text="", width=22).pack(side=tk.LEFT)

        # 密码（带显示切换）
        row2 = ttk.Frame(frame)
        row2.pack(fill=tk.X, pady=3)
        ttk.Label(row2, text="密码", font=FONT_BODY,
                  foreground=C_MUTED, width=6).pack(side=tk.LEFT)
        self.password_var = tk.StringVar(value=self.config.get("password", ""))
        self.password_entry = tk.Entry(row2, textvariable=self.password_var, show="●",
                                       font=FONT_BODY, width=18, relief="solid", bd=1,
                                       highlightthickness=0, highlightbackground=C_BORDER,
                                       highlightcolor=C_PRIMARY)
        self.password_entry.pack(side=tk.LEFT, padx=(6, 0), ipady=2)
        self.show_pwd_var = tk.BooleanVar(value=False)
        tk.Checkbutton(row2, text="显示密码", variable=self.show_pwd_var,
                        command=self._toggle_password_show,
                        bg=C_CARD_BG, relief="flat",
                        highlightthickness=0).pack(side=tk.LEFT, padx=(6, 0))

    def _build_status_card(self, parent):
        frame = tk.Frame(parent, bg=C_CARD_BG)
        frame.pack(fill=tk.X, pady=(0, 10))

        # 两列布局：左 WiFi / 右 网络
        cols = tk.Frame(frame, bg=C_CARD_BG)
        cols.pack(fill=tk.X)

        left = tk.Frame(cols, bg=C_CARD_BG)
        left.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.wifi_dot = StatusDot(left, "WiFi 状态")
        self.wifi_dot.pack(pady=2)

        right = tk.Frame(cols, bg=C_CARD_BG)
        right.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        self.net_dot = StatusDot(right, "网络状态")
        self.net_dot.pack(pady=2)

    def _build_settings_card(self, parent):
        frame = tk.Frame(parent, bg=C_CARD_BG)
        frame.pack(fill=tk.X, pady=(0, 10))

        self.autostart_var = tk.BooleanVar(value=self.check_autostart())
        cb = tk.Checkbutton(frame, text="开机自动启动",
                             variable=self.autostart_var,
                             command=self.toggle_autostart,
                             bg=C_CARD_BG, relief="flat",
                             highlightthickness=0)
        cb.pack(anchor=tk.W)

    def _build_buttons(self, parent):
        row = ttk.Frame(parent)
        row.pack(fill=tk.X, pady=(4, 10))

        ttk.Button(row, text="  立即登录  ", style="Outline.TButton",
                   command=self.manual_login).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(row, text="查看日志", style="Outline.TButton",
                   command=self.view_log).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(row, text="保存配置", style="Outline.TButton",
                   command=self.on_save_config).pack(side=tk.LEFT)

    def _build_log(self, parent):
        frame = tk.Frame(parent, bg=C_CARD_BG)
        frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        label_frame = tk.Frame(frame, bg=C_CARD_BG)
        label_frame.pack(fill=tk.X, pady=(0, 6))
        tk.Label(label_frame, text="运行日志", font=FONT_BODY,
                 fg=C_MUTED, bg=C_CARD_BG, anchor=tk.W).pack(side=tk.LEFT)

        self.log_text = tk.Text(frame, height=6, wrap=tk.WORD,
                                state=tk.DISABLED, font=FONT_MONO,
                                bg="#ffffff", fg=C_TEXT,
                                relief="flat", padx=8, pady=6,
                                highlightthickness=0)
        self.log_text.pack(fill=tk.BOTH, expand=True)

    # ---------- 业务逻辑 ----------

    def on_save_config(self):
        self.config["username"] = self.username_var.get()
        self.config["password"] = self.password_var.get()
        if self.save_config():
            messagebox.showinfo("成功", "配置保存成功！")
            if hasattr(self, 'on_config_changed') and callable(self.on_config_changed):
                self.on_config_changed(self.config)

    def _toggle_password_show(self):
        """切换密码显示/隐藏"""
        if self.show_pwd_var.get():
            self.password_entry.config(show="")
        else:
            self.password_entry.config(show="●")

    def check_autostart(self):
        try:
            r = subprocess.run(['schtasks', '/query', '/tn', 'BJTUAutoLogin'],
                               capture_output=True, text=True, errors='replace',
                               creationflags=CREATE_NO_WINDOW)
            return r.returncode == 0
        except:
            return False

    def toggle_autostart(self):
        if self.autostart_var.get():
            self.enable_autostart()
        else:
            self.disable_autostart()

    def enable_autostart(self):
        try:
            task = 'BJTUAutoLogin'
            # 先删除旧的（避免残留）
            subprocess.run(['schtasks', '/delete', '/tn', task, '/f'],
                           capture_output=True, creationflags=CREATE_NO_WINDOW)

            if getattr(sys, 'frozen', False):
                exe = sys.executable
                cmd = ['schtasks', '/create', '/tn', task,
                       '/tr', f'"{exe}"',
                       '/sc', 'onlogon', '/f']
            else:
                pythonw = sys.executable.replace("python.exe", "pythonw.exe")
                script = os.path.join(get_app_path(), "src", "main.pyw")
                cmd = ['schtasks', '/create', '/tn', task,
                       '/tr', f'"{pythonw}" "{script}"',
                       '/sc', 'onlogon', '/f']

            r = subprocess.run(cmd, capture_output=True, text=True, errors='replace',
                               creationflags=CREATE_NO_WINDOW)
            if r.returncode != 0:
                raise RuntimeError(r.stderr.strip())
            messagebox.showinfo("成功", "开机自启已开启")
        except Exception as e:
            self.autostart_var.set(False)
            messagebox.showerror("失败", f"开启开机自启失败：{e}\n\n请以管理员身份运行此程序")

    def disable_autostart(self):
        try:
            r = subprocess.run(['schtasks', '/delete', '/tn', 'BJTUAutoLogin', '/f'],
                               capture_output=True, text=True, errors='replace',
                               creationflags=CREATE_NO_WINDOW)
            if r.returncode != 0:
                raise RuntimeError(r.stderr.strip())
            messagebox.showinfo("成功", "开机自启已关闭")
        except Exception as e:
            self.autostart_var.set(not self.autostart_var.get())
            messagebox.showerror("失败", f"关闭开机自启失败：{e}")

    def manual_login(self):
        """立即登录 - 由主程序通过 _on_manual_login 注入"""
        if hasattr(self, '_on_manual_login') and callable(self._on_manual_login):
            self._on_manual_login()

    def view_log(self):
        p = os.path.join(get_app_path(), "login.log")
        if os.path.exists(p):
            webbrowser.open(p)

    def minimize_to_tray(self):
        self.root.withdraw()

    def update_status(self, wifi_connected, net_connected):
        if wifi_connected:
            self.wifi_dot.set_status("connected")
        else:
            self.wifi_dot.set_status("disconnected")

        if net_connected:
            self.net_dot.set_status("online")
        else:
            self.net_dot.set_status("offline")

    def start_updates(self):
        self.update_log_preview()
        self.update_timer = self.root.after(1000, self.start_updates)

    def update_log_preview(self):
        p = os.path.join(get_app_path(), "login.log")
        if not os.path.exists(p):
            return
        try:
            with open(p, "r", encoding="utf-8") as f:
                lines = f.readlines()
            recent = lines[-15:]
            self.log_text.config(state=tk.NORMAL)
            self.log_text.delete("1.0", tk.END)
            for line in recent:
                self.log_text.insert(tk.END, line)
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
        except:
            pass

    def on_closing(self):
        """关闭窗口时的处理 - 返回 'exit'/'tray'/'cancel'"""
        action = self.config.get('close_action', 'ask')
        remember = self.config.get('close_remember', False)

        if remember and action != 'ask':
            if action == 'tray':
                self.root.withdraw()
                return 'tray'
            else:
                if self.update_timer:
                    self.root.after_cancel(self.update_timer)
                self.root.destroy()
                return 'exit'
        else:
            return self._show_close_dialog()

    def _show_close_dialog(self):
        """显示关闭方式选择对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("BJTU校园网自动登录")
        dialog.geometry("400x210")
        dialog.resizable(False, False)
        dialog.configure(bg=C_BG)
        dialog.transient(self.root)
        dialog.grab_set()

        # 居中于主窗口
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - 400) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 210) // 2
        dialog.geometry(f"+{x}+{y}")

        # 图标
        try:
            icon_path = os.path.join(get_app_path(), 'resources', 'icon.ico')
            if not os.path.exists(icon_path):
                icon_path = os.path.join(get_app_path(), 'icon.ico')
            if os.path.exists(icon_path):
                dialog.iconbitmap(icon_path)
                try:
                    from PIL import Image, ImageTk
                    img = Image.open(icon_path)
                    photo = ImageTk.PhotoImage(img)
                    dialog.iconphoto(True, photo)
                    dialog._icon_photo = photo  # 保持引用
                except ImportError:
                    pass
        except:
            pass

        result = {'action': None}

        content = tk.Frame(dialog, bg=C_BG, padx=28, pady=24)
        content.pack(fill=tk.BOTH, expand=True)

        tk.Label(content, text="请选择关闭方式", font=FONT_HEAD,
                 fg=C_TEXT, bg=C_BG).pack(anchor=tk.W, pady=(0, 18))

        # 按钮行
        btn_frame = tk.Frame(content, bg=C_BG)
        btn_frame.pack(fill=tk.X, pady=(0, 14))

        def do_exit():
            result['action'] = 'exit'
            if self._close_remember_var.get():
                self.config['close_remember'] = True
                self.config['close_action'] = 'exit'
                self.save_config()
            dialog.destroy()
            if self.update_timer:
                self.root.after_cancel(self.update_timer)
            self.root.destroy()

        def do_tray():
            result['action'] = 'tray'
            if self._close_remember_var.get():
                self.config['close_remember'] = True
                self.config['close_action'] = 'tray'
                self.save_config()
            dialog.destroy()
            self.root.withdraw()

        exit_btn = tk.Button(
            btn_frame, text="直接退出", font=FONT_BODY,
            bg=C_BG, fg=C_DANGER,
            activebackground="#fce8e6", activeforeground=C_DANGER,
            relief="solid", bd=1,
            padx=22, pady=7,
            cursor="hand2",
            command=do_exit
        )
        exit_btn.pack(side=tk.LEFT, padx=(0, 14))

        tray_btn = tk.Button(
            btn_frame, text="最小化到托盘", font=FONT_BODY,
            bg=C_BG, fg=C_PRIMARY,
            activebackground="#e8f0fe", activeforeground=C_PRIMARY,
            relief="solid", bd=1,
            padx=22, pady=7,
            cursor="hand2",
            command=do_tray
        )
        tray_btn.pack(side=tk.LEFT)

        # "不再提醒" 复选框
        self._close_remember_var = tk.BooleanVar(value=False)
        cb = tk.Checkbutton(
            content, text="不再提醒，记住我的选择",
            variable=self._close_remember_var,
            bg=C_BG, fg=C_MUTED, font=FONT_SMALL,
            activebackground=C_BG, activeforeground=C_MUTED,
            relief="flat", highlightthickness=0,
            selectcolor=C_BG,
            cursor="hand2"
        )
        cb.pack(anchor=tk.W)

        def on_dialog_close():
            result['action'] = 'cancel'
            dialog.destroy()

        dialog.protocol("WM_DELETE_WINDOW", on_dialog_close)
        self.root.wait_window(dialog)
        return result['action']


# ========== 入口 ==========

def run_gui():
    root = tk.Tk()
    app = MainWindow(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    run_gui()
