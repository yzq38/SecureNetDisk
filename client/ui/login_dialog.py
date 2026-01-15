from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QPainter, QLinearGradient, QPainterPath, QFont
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTabWidget, QWidget, QMessageBox, QStackedWidget,
    QGroupBox, QFormLayout, QComboBox, QDialogButtonBox
)
from PyQt6.QtGui import QIcon, QPixmap
from pathlib import Path
from .styles import StyleSheet
from client.config import config as app_config

class GradientWaveWidget(QWidget):
    """动态波浪渐变背景部件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.colors = [
            QColor("#132843"),  # Color 01
            QColor("#3966A2"),  # Color 02
            QColor("#6191D3"),  # Color 03
            QColor("#D6DEEB"),  # Color 04
            QColor("#F8F6F6")  # Color 05
        ]
        self.offset = 0
        self.wave_speed = 0.5
        self.wave_height = 20

        # 启动动画定时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_wave)
        self.timer.start(50)  # 20 FPS

    def update_wave(self):
        """更新波浪偏移量"""
        self.offset += self.wave_speed
        if self.offset > 100:  # 重置偏移量保持平滑循环
            self.offset = 0
        self.update()

    def paintEvent(self, event):
        """绘制波浪渐变背景"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()

        # 创建主渐变（从上到下）
        main_gradient = QLinearGradient(0, 0, width, height)

        # 计算颜色停止点，制造波浪效果
        num_colors = len(self.colors)
        for i in range(num_colors):
            # 计算波浪偏移位置
            wave_pos = (i / (num_colors - 1) * 100 + self.offset) % 100 / 100
            main_gradient.setColorAt(wave_pos, self.colors[i])

            # 添加一些中间渐变点使过渡更平滑
            if i < num_colors - 1:
                mid_pos = ((i + 0.5) / (num_colors - 1) * 100 + self.offset) % 100 / 100
                # 创建中间颜色（混合两个相邻颜色）
                mid_color = QColor(
                    (self.colors[i].red() + self.colors[i + 1].red()) // 2,
                    (self.colors[i].green() + self.colors[i + 1].green()) // 2,
                    (self.colors[i].blue() + self.colors[i + 1].blue()) // 2
                )
                main_gradient.setColorAt(mid_pos, mid_color)

        # 填充渐变
        painter.fillRect(0, 0, width, height, main_gradient)

        # 添加一些波浪曲线
        painter.setPen(Qt.PenStyle.NoPen)
        wave_color = QColor(255, 255, 255, 30)  # 半透明白色

        for i in range(3):  # 画3层波浪
            path_height = self.wave_height * (i + 1)
            wave_color.setAlpha(40 - i * 10)
            painter.setBrush(wave_color)

            # 创建波浪路径
            painter.save()
            painter.translate(-self.offset * 2 * (i + 1), height - path_height)

            wave_width = width * 2
            wave_path = QPainterPath()
            wave_path.moveTo(0, 0)

            for x in range(0, wave_width + 1, 20):
                y = path_height * 0.5 * (1 + 0.5 * (i + 1) *
                                         (0.5 * (x / 50 + self.offset / 10) % 6.28))
                wave_path.lineTo(x, y)

            wave_path.lineTo(wave_width, 0)
            wave_path.lineTo(0, 0)
            painter.drawPath(wave_path)
            painter.restore()

        painter.end()



class LoginDialog(QDialog):
    """登录对话框"""
    login_success = pyqtSignal(dict)
    
    def __init__(self, network_client, key_manager, device_trust=None, parent=None):
        super().__init__(parent)
        self.network = network_client
        self.key_manager = key_manager
        self.device_trust = device_trust
        self._pending_trust_data = None  # 待确认信任的数据
        self.setWindowTitle("安全网盘 - 登录")
        self.setMinimumSize(400, 600)
        self.resize(900, 835)  # 初始大小
        self.setStyleSheet(StyleSheet.LOGIN)
        self._init_ui()
        
        # 启动后尝试自动连接
        QTimer.singleShot(100, self._try_initial_connect)
    
    def _init_ui(self):
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)  # 去除边距以便渐变区域填充
        main_layout.setSpacing(0)

        # 渐变波浪背景区域
        self.gradient_widget = GradientWaveWidget()
        # 渐变区域的高度约为整个对话框的1/3
        gradient_height = int(self.height() * 0.3)
        self.gradient_widget.setFixedHeight(gradient_height)

        # 渐变区域容器，包含内容
        gradient_container = QWidget()
        gradient_container.setObjectName("gradientContainer")
        gradient_layout = QVBoxLayout(gradient_container)
        gradient_layout.setContentsMargins(0, 0, 0, 0)
        gradient_layout.setSpacing(0)

        # 在渐变区域上方添加顶部间距
        gradient_layout.addSpacing(20)

        # 渐变区域的内容布局
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(40, 0, 40, 20)  # 左右边距40px，底部边距20px
        content_layout.setSpacing(16)

        # Logo 图标 + 文字 (水平居中)
        logo_container = QWidget()
        logo_layout = QHBoxLayout(logo_container)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.setSpacing(12)
        logo_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        icon_path = Path(__file__).parent.parent / "resources" / "icon.png"
        if icon_path.exists():
            # 设置窗口图标
            self.setWindowIcon(QIcon(str(icon_path)))
            # Logo 图片
            logo_pixmap = QPixmap(str(icon_path)).scaled(
                56, 56, 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            logo_icon = QLabel()
            logo_icon.setPixmap(logo_pixmap)
            logo_layout.addWidget(logo_icon)
        
        logo_text = QLabel("安全网盘")
        logo_text.setStyleSheet("""
            QLabel {
                font-size: 32px;
                font-weight: bold;
                color: white;
                background: transparent;
            }
        """)
        logo_layout.addWidget(logo_text)
        
        content_layout.addWidget(logo_container, alignment=Qt.AlignmentFlag.AlignCenter)
        
        
        # 连接状态标签
        self.connection_status = QLabel("⚪ 正在连接服务器...")
        self.connection_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.connection_status.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.9);
                font-size: 14px;
                font-weight: 500;
                text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
            }
        """)
        content_layout.addWidget(self.connection_status)

        content_layout.addSpacing(10)

        gradient_layout.addLayout(content_layout)
        gradient_layout.addStretch()

        # 将渐变部件设置为渐变容器的背景
        gradient_container.background_widget = self.gradient_widget
        main_layout.addWidget(gradient_container)

        # 创建白色内容区域（覆盖剩余部分）
        content_widget = QWidget()
        content_widget.setObjectName("contentWidget")
        content_widget.setStyleSheet("""
            QWidget#contentWidget {
                background: white;
                border-top-left-radius: 20px;
                border-top-right-radius: 20px;
                margin-top: -5px;
            }
        """)

        content_layout_inner = QVBoxLayout(content_widget)
        content_layout_inner.setContentsMargins(40, 30, 40, 40)
        content_layout_inner.setSpacing(16)

        self.stack = QStackedWidget()
        self.stack.addWidget(self._create_login_page())  # 0 - 密码登录
        self.stack.addWidget(self._create_register_page())  # 1 - 注册
        self.stack.addWidget(self._create_recovery_page())  # 2 - 恢复密码
        self.stack.addWidget(self._create_email_login_page())  # 3 - 邮箱验证码登录

        # 页面切换时刷新UI状态
        self.stack.currentChanged.connect(self._on_page_changed)
        content_layout_inner.addWidget(self.stack)

        # 右下角设置按钮
        settings_btn = QPushButton("⚙️")
        settings_btn.setObjectName("settingsButton")
        settings_btn.setFixedSize(40, 40)
        # 创建字体并设置大小
        font = QFont()
        font.setPointSize(20)  # 设置字体大小为20
        settings_btn.setFont(font)
        settings_btn.clicked.connect(self._show_settings_dialog)

        # 将按钮放在布局的右下角
        content_layout_inner.addStretch()
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(settings_btn)
        content_layout_inner.addLayout(button_layout)

        main_layout.addWidget(content_widget)


        # 初始化动画状态
        gradient_container._animation_time = 0.0

        # 初始化颜色数组
        gradient_container._colors = [
            QColor("#132843"),  # 深蓝色
            QColor("#3966A2"),  # 蓝色
            QColor("#6191D3"),  # 浅蓝色
            QColor("#D6DEEB"),  # 淡蓝色
            QColor("#F8F6F6")  # 近白色
        ]

        # 创建动画定时器
        gradient_container._timer = QTimer(gradient_container)
        gradient_container._timer.timeout.connect(lambda: (
            setattr(gradient_container, '_animation_time',
                    (gradient_container._animation_time + 0.005) % 1.0),
            gradient_container.update()
        ))
        gradient_container._timer.start(16)  # 约60fps

        # 重写渐变容器的绘制事件
        def gradient_container_paint_event(event):
            # 直接绘制渐变背景，不通过render
            painter = QPainter(gradient_container)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # 获取容器尺寸
            width = gradient_container.width()
            height = gradient_container.height()

            # 创建主渐变
            main_gradient = QLinearGradient(0, 0, width, height)

            # 动态计算偏移量 - 需要保存偏移状态
            if not hasattr(gradient_container, '_wave_offset'):
                gradient_container._wave_offset = 0
                gradient_container._wave_timer = QTimer(gradient_container)
                gradient_container._wave_timer.timeout.connect(
                    lambda: (
                        setattr(gradient_container, '_wave_offset',
                                (gradient_container._wave_offset + 0.5) % 100),
                        gradient_container.update()
                    )
                )
                gradient_container._wave_timer.start(50)

            offset = gradient_container._wave_offset
            colors = [
                QColor("#132843"),  # Color 01
                QColor("#3966A2"),  # Color 02
                QColor("#6191D3"),  # Color 03
                QColor("#D6DEEB"),  # Color 04
                QColor("#F8F6F6")  # Color 05
            ]

            # 计算颜色停止点，制造波浪效果
            num_colors = len(colors)
            for i in range(num_colors):
                # 计算波浪偏移位置
                wave_pos = (i / (num_colors - 1) * 100 + offset) % 100 / 100
                main_gradient.setColorAt(wave_pos, colors[i])

                # 添加中间渐变点使过渡更平滑
                if i < num_colors - 1:
                    mid_pos = ((i + 0.5) / (num_colors - 1) * 100 + offset) % 100 / 100
                    # 创建中间颜色（混合两个相邻颜色）
                    mid_color = QColor(
                        (colors[i].red() + colors[i + 1].red()) // 2,
                        (colors[i].green() + colors[i + 1].green()) // 2,
                        (colors[i].blue() + colors[i + 1].blue()) // 2
                    )
                    main_gradient.setColorAt(mid_pos, mid_color)

            # 填充渐变
            painter.fillRect(0, 0, width, height, main_gradient)

            # 调用原始的paintEvent绘制内容
            QWidget.paintEvent(gradient_container, event)

        gradient_container.paintEvent = gradient_container_paint_event

    def resizeEvent(self, event):
        """处理窗口大小变化"""
        super().resizeEvent(event)
        # 动态调整渐变区域高度
        gradient_height = int(self.height() * 0.3)
        self.gradient_widget.setFixedHeight(gradient_height)
        self.gradient_widget.update()

    def _show_settings_dialog(self):
        """显示服务器设置对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle("服务器设置")
        dialog.setFixedSize(500, 220)  # 稍微增大对话框宽度

        layout = QVBoxLayout(dialog)
        layout.setSpacing(16)

        # 居中标题
        title_label = QLabel("服务器设置")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: 500;
                color: #202124;
                margin-bottom: 8px;
            }
        """)
        layout.addWidget(title_label)

        # 服务器设置表单
        form_layout = QFormLayout()
        form_layout.setFormAlignment(Qt.AlignmentFlag.AlignCenter)  # 表单居中
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)  # 标签右对齐

        self.host_combo = QComboBox()
        self.host_combo.setEditable(True)
        self.host_combo.setPlaceholderText("服务器地址和端口 (例如: 127.0.0.1:5000)")
        self.host_combo.setMinimumWidth(300)  # 设置最小宽度
        self.host_combo.setMaximumWidth(400)  # 设置最大宽度

        # 填充历史记录
        if app_config.recent_hosts:
            self.host_combo.addItems(app_config.recent_hosts)
            # 显示完整的历史记录，包含端口
            if ':' in app_config.recent_hosts[0]:
                self.host_combo.setCurrentText(app_config.recent_hosts[0])
            else:
                # 如果历史记录没有端口，添加默认端口
                self.host_combo.setCurrentText(f"{app_config.recent_hosts[0]}:{app_config.port}")
        else:
            # 显示默认的地址和端口
            self.host_combo.setCurrentText(f"{app_config.host}:{app_config.port}")

        # 创建容器使输入框居中
        host_container = QWidget()
        host_layout = QHBoxLayout(host_container)
        host_layout.setContentsMargins(0, 0, 0, 0)
        host_layout.addWidget(self.host_combo, alignment=Qt.AlignmentFlag.AlignCenter)

        form_layout.addRow("地址端口:", host_container)
        layout.addLayout(form_layout)

        # 测试连接按钮
        test_conn_btn = QPushButton("测试连接")
        test_conn_btn.setStyleSheet("""
            QPushButton {
                background: #1a73e8;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-weight: 500;
                min-width: 100px;
            }
            QPushButton:hover {
                background: #1557b0;
            }
        """)
        test_conn_btn.clicked.connect(lambda: self._test_connection_in_dialog(dialog))

        # 将按钮放在容器中居中
        btn_container = QWidget()
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.addWidget(test_conn_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(btn_container)

        # 按钮框
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(lambda: self._apply_settings(dialog))
        button_box.rejected.connect(dialog.reject)

        # 将按钮框居中
        button_container = QWidget()
        button_container_layout = QHBoxLayout(button_container)
        button_container_layout.setContentsMargins(0, 0, 0, 0)
        button_container_layout.addWidget(button_box, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(button_container)

        dialog.exec()

    def _test_connection_in_dialog(self, dialog):
        """在设置对话框中测试连接"""
        text = self.host_combo.currentText().strip()
        if not text:
            QMessageBox.warning(dialog, "配置错误", "请输入服务器地址和端口")
            return

        # 解析地址和端口
        if ':' in text:
            parts = text.split(':')
            if len(parts) != 2 or not parts[1].isdigit():
                QMessageBox.warning(dialog, "配置错误", "地址格式应为 host:port (例如: 127.0.0.1:5000)")
                return
            host = parts[0].strip()
            port = int(parts[1].strip())
        else:
            QMessageBox.warning(dialog, "配置错误", "请包含端口号 (例如: 127.0.0.1:5000)")
            return

        # 临时更新网络配置
        old_host = self.network.server_info.host
        old_port = self.network.server_info.port

        self.network.server_info.host = host
        self.network.server_info.port = port

        if self.network.is_connected:
            self.network.disconnect()

        if self.network.connect():
            QMessageBox.information(dialog, "连接成功", f"已连接到服务器 {host}:{port}")
            # 保持连接状态
        else:
            QMessageBox.critical(dialog, "连接失败", f"无法连接到服务器 {host}:{port}")
            # 恢复之前的配置
            self.network.server_info.host = old_host
            self.network.server_info.port = old_port

    def _apply_settings(self, dialog):
        """应用设置并保存到配置"""
        text = self.host_combo.currentText().strip()
        if not text:
            QMessageBox.warning(dialog, "配置错误", "请输入服务器地址和端口")
            return

        # 解析地址和端口
        if ':' in text:
            parts = text.split(':')
            if len(parts) != 2 or not parts[1].isdigit():
                QMessageBox.warning(dialog, "配置错误", "地址格式应为 host:port (例如: 127.0.0.1:5000)")
                return
            host = parts[0].strip()
            port = int(parts[1].strip())
        else:
            QMessageBox.warning(dialog, "配置错误", "请包含端口号 (例如: 127.0.0.1:5000)")
            return

        # 更新网络配置
        if self.network.is_connected:
            self.network.disconnect()

        self.network.server_info.host = host
        self.network.server_info.port = port

        # 尝试连接
        if self.network.connect():
            # 保存到配置
            app_config.host = host
            app_config.port = port
            app_config.add_to_history(host, port)  # 保存带端口的完整地址
            app_config.save()

            # 更新状态标签
            self._update_status(True, f"已连接到服务器")
            dialog.accept()
        else:
            QMessageBox.critical(dialog, "连接失败", f"无法连接到服务器 {host}:{port}")
            self._update_status(False, f"连接失败: {host}:{port}")

    def _create_login_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 1, 0, 0)
        layout.setSpacing(12)

        layout.addWidget(QLabel("登录您的账号"))

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("用户名")
        if app_config.last_username:
            self.username_input.setText(app_config.last_username)
        layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("密码")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_input)

        login_btn = QPushButton("登录")
        login_btn.setObjectName("loginButton")
        login_btn.clicked.connect(self._do_login)
        layout.addWidget(login_btn)

        # 邮箱验证码登录按钮
        email_login_btn = QPushButton("📧 使用邮箱验证码登录")
        email_login_btn.setObjectName("linkButton")
        email_login_btn.clicked.connect(lambda: self.stack.setCurrentIndex(3))
        layout.addWidget(email_login_btn)

        # 忘记密码按钮
        forgot_btn = QPushButton("忘记密码")
        forgot_btn.setObjectName("linkButton")
        forgot_btn.clicked.connect(lambda: self.stack.setCurrentIndex(2))
        layout.addWidget(forgot_btn)

        layout.addStretch()

        reg_btn = QPushButton("没有账号？点击注册")
        reg_btn.setObjectName("linkButton")
        reg_btn.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        layout.addWidget(reg_btn)

        return page

    def _on_host_changed(self, text):
        """Handle host text change - no longer needed as port is part of host string"""
        pass  # Port is now included in host:port format

    def _try_initial_connect(self):
        """启动时尝试静默连接"""
        host = app_config.host
        port = app_config.port
        
        # 更新 network client 配置
        self.network.server_info.host = host
        self.network.server_info.port = port
        
        if self.network.connect():
            self._update_status(True, f"已连接到 {host}:{port}")
        else:
            self._update_status(False, f"未能连接到服务器 {host}:{port}")

    def _update_status(self, connected: bool, message: str):
        """更新连接状态标签"""
        if connected:
            self.connection_status.setText(f"🟢 {message}")
            self.connection_status.setStyleSheet("color: #34a853; font-size: 12px; font-weight: bold;") 
        else:
            self.connection_status.setText(f"🔴 {message}")
            self.connection_status.setStyleSheet("color: #ea4335; font-size: 12px; font-weight: bold;")

    def _ensure_connection(self) -> bool:
        """确保已连接到配置的服务器"""
        # 使用当前配置的服务器信息（已通过设置对话框或初始连接设置）
        host = self.network.server_info.host or app_config.host
        port = self.network.server_info.port or app_config.port

        # 如果已连接，直接返回
        if self.network.is_connected:
            if self.network.ping():
                return True
            # ping失败，重新连接
            self.network.disconnect()

        # 更新配置并重连
        self._update_status(False, "正在连接服务器...")

        self.network.server_info.host = host
        self.network.server_info.port = port
        
        if not self.network.connect():
            self._update_status(False, f"连接失败: {host}:{port}")
            QMessageBox.critical(self, "连接失败", f"无法连接到服务器 {host}:{port}\n请检查服务器设置")
            return False
            
        self._update_status(True, f"已连接到 {host}:{port}")
        return True

    def _save_connection_config(self):
        """保存成功的连接配置"""
        app_config.host = self.network.server_info.host
        app_config.port = self.network.server_info.port
        # Add to history
        app_config.add_to_history(app_config.host, app_config.port)
        app_config.save()

    def _do_login(self):
        if not self._ensure_connection():
            return

        username = self.username_input.text().strip()
        password = self.password_input.text()
        if not username or not password:
            QMessageBox.warning(self, "提示", "请输入用户名和密码")
            return
        
        # 保存用户名
        app_config.last_username = username
        self._save_connection_config() # 保存连接配置（因为连接成功了）
        
        # 使用 SHA-256 预哈希密码后再发送（避免明文传输）
        from auth.password import PasswordManager
        password_prehash = PasswordManager.prehash_password(password)
        result = self.network.login_password(username, password_prehash)
        
        if result.get('success'):
            if self.key_manager.unlock_with_password(password, result):
                email = result.get('email', '')
                # 检查是否需要询问信任设备（仅当该邮箱未信任时）
                if self.device_trust and email and not self.device_trust.has_trusted_device(email):
                    self._pending_trust_data = {
                        'result': result,
                        'email': email
                    }
                    self._ask_trust_device()
                else:
                    self.login_success.emit(result)
                    self.accept()
            else:
                QMessageBox.critical(self, "错误", "密钥解锁失败")
        else:
            QMessageBox.critical(self, "错误", result.get('error', '登录失败'))

    def _create_email_login_page(self):
        """创建邮箱验证码登录页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(12)
        
        back_btn = QPushButton("← 返回密码登录")
        back_btn.setObjectName("linkButton")
        back_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        layout.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        
        layout.addWidget(QLabel("📧 邮箱验证码登录"))
        
        # 可更新的已信任用户提示
        self.email_login_trust_hint = QLabel("")
        self.email_login_trust_hint.setStyleSheet("color: #1a73e8; font-size: 12px;")
        self.email_login_trust_hint.setWordWrap(True)
        layout.addWidget(self.email_login_trust_hint)
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("邮箱地址")
        layout.addWidget(self.email_input)
        
        # 验证码输入和获取按钮
        code_layout = QHBoxLayout()
        self.email_code_input = QLineEdit()
        self.email_code_input.setPlaceholderText("验证码")
        self.email_code_input.setMaxLength(6)
        code_layout.addWidget(self.email_code_input, 2)
        
        self.get_code_btn = QPushButton("获取验证码")
        self.get_code_btn.clicked.connect(self._request_email_code)
        code_layout.addWidget(self.get_code_btn, 1)
        layout.addLayout(code_layout)
        
        # 密码输入（非信任设备需要）
        self.email_password_input = QLineEdit()
        self.email_password_input.setPlaceholderText("密码（非信任设备需要）")
        self.email_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.email_password_input)
        
        # 提示：输入邮箱后会动态判断是否需要密码
        self.trust_hint_label = QLabel("")
        self.trust_hint_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(self.trust_hint_label)
        
        # 邮箱输入变化时更新提示
        self.email_input.textChanged.connect(self._update_trust_hint)
        
        # 初始化信任状态
        self._refresh_trust_ui()
        
        email_login_btn = QPushButton("验证码登录")
        email_login_btn.setObjectName("loginButton")
        email_login_btn.clicked.connect(self._do_email_login)
        layout.addWidget(email_login_btn)
        
        layout.addStretch()
        return page
    def _refresh_trust_ui(self):
        """刷新设备信任相关的UI"""
        trusted_emails = []
        if self.device_trust:
            trusted_emails = self.device_trust.get_trusted_emails()
        
        # 更新邮箱登录页的已信任用户提示
        if hasattr(self, 'email_login_trust_hint'):
            if trusted_emails:
                self.email_login_trust_hint.setText(f"已信任用户: {', '.join(trusted_emails)}")
                self.email_login_trust_hint.show()
                # 如果只有一个信任用户且输入框为空，自动填充
                if len(trusted_emails) == 1 and not self.email_input.text().strip():
                    self.email_input.setText(trusted_emails[0])
            else:
                self.email_login_trust_hint.setText("")
                self.email_login_trust_hint.hide()
        
        # 更新密码恢复页的信任提示
        if hasattr(self, 'recovery_email_hint'):
            if trusted_emails:
                self.recovery_email_hint.setText(f"可用邮箱: {', '.join(trusted_emails)}")
            else:
                self.recovery_email_hint.setText("⚠️ 此设备无信任用户，无法使用此方式")
        
        # 更新当前输入框的信任状态
        self._update_trust_hint()
    
    def _on_page_changed(self, index: int):
        """页面切换时刷新UI状态"""
        # 刷新信任状态
        self._refresh_trust_ui()
        
        # 清除所有输入字段（防止信息泄露）
        
        # 密码登录页
        if hasattr(self, 'username_input'):
            self.username_input.clear()
        if hasattr(self, 'password_input'):
            self.password_input.clear()
        
        # 邮箱登录页
        if hasattr(self, 'email_input'):
            self.email_input.clear()
        if hasattr(self, 'email_code_input'):
            self.email_code_input.clear()
        if hasattr(self, 'email_password_input'):
            self.email_password_input.clear()
        
        # 注册页
        if hasattr(self, 'reg_username'):
            self.reg_username.clear()
        if hasattr(self, 'reg_email'):
            self.reg_email.clear()
        if hasattr(self, 'reg_password'):
            self.reg_password.clear()
        
        # 恢复页（恢复密钥方式）
        if hasattr(self, 'recovery_username'):
            self.recovery_username.clear()
        if hasattr(self, 'recovery_key_input'):
            self.recovery_key_input.clear()
        
        # 恢复页（邮箱验证码方式）
        if hasattr(self, 'recovery_email_username'):
            self.recovery_email_username.clear()
        if hasattr(self, 'recovery_email_input'):
            self.recovery_email_input.clear()
        if hasattr(self, 'recovery_code_input'):
            self.recovery_code_input.clear()
        
        # 恢复页（新密码）
        if hasattr(self, 'new_password_input'):
            self.new_password_input.clear()
        if hasattr(self, 'confirm_password_input'):
            self.confirm_password_input.clear()
        
        # 重置验证码按钮状态
        if hasattr(self, 'get_code_btn'):
            self.get_code_btn.setEnabled(True)
            self.get_code_btn.setText("获取验证码")
        if hasattr(self, 'recovery_get_code_btn'):
            self.recovery_get_code_btn.setEnabled(True)
            self.recovery_get_code_btn.setText("获取验证码")
    
    def _update_trust_hint(self):
        """更新信任状态提示"""
        email = self.email_input.text().strip()
        if self.device_trust and email and self.device_trust.has_trusted_device(email):
            self.trust_hint_label.setText("✓ 此邮箱已信任，无需密码")
            self.trust_hint_label.setStyleSheet("color: #1a73e8; font-size: 11px;")
            self.email_password_input.setEnabled(False)
        else:
            self.trust_hint_label.setText("此邮箱未信任此设备，需要输入密码")
            self.trust_hint_label.setStyleSheet("color: #666; font-size: 11px;")
            self.email_password_input.setEnabled(True)
    
    def _create_register_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(12)
        
        back_btn = QPushButton("← 返回")
        back_btn.setObjectName("linkButton")
        back_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        layout.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        
        layout.addWidget(QLabel("创建账号"))
        
        self.reg_username = QLineEdit()
        self.reg_username.setPlaceholderText("用户名")
        layout.addWidget(self.reg_username)
        
        self.reg_email = QLineEdit()
        self.reg_email.setPlaceholderText("邮箱")
        layout.addWidget(self.reg_email)
        
        self.reg_password = QLineEdit()
        self.reg_password.setPlaceholderText("密码")
        self.reg_password.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.reg_password)
        
        reg_btn = QPushButton("注册")
        reg_btn.setObjectName("loginButton")
        reg_btn.clicked.connect(self._do_register)
        layout.addWidget(reg_btn)
        
        layout.addStretch()
        return page
    
    def _create_recovery_page(self):
        """创建密码恢复页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(12)
        
        back_btn = QPushButton("← 返回登录")
        back_btn.setObjectName("linkButton")
        back_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        layout.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        
        layout.addWidget(QLabel("🔑 重置密码"))
        
        # 方式选择
        self.recovery_method_label = QLabel("请选择重置方式：")
        layout.addWidget(self.recovery_method_label)
        
        method_layout = QHBoxLayout()
        self.recovery_key_radio = QPushButton("恢复密钥")
        self.recovery_key_radio.setCheckable(True)
        self.recovery_key_radio.setChecked(True)
        self.recovery_key_radio.clicked.connect(lambda: self._switch_recovery_method('key'))
        method_layout.addWidget(self.recovery_key_radio)
        
        self.email_code_radio = QPushButton("邮箱验证码（信任设备）")
        self.email_code_radio.setCheckable(True)
        self.email_code_radio.clicked.connect(lambda: self._switch_recovery_method('email'))
        method_layout.addWidget(self.email_code_radio)
        layout.addLayout(method_layout)
        
        # 恢复密钥方式的输入框
        self.recovery_key_container = QWidget()
        key_layout = QVBoxLayout(self.recovery_key_container)
        key_layout.setContentsMargins(0, 0, 0, 0)
        
        self.recovery_username = QLineEdit()
        self.recovery_username.setPlaceholderText("用户名")
        key_layout.addWidget(self.recovery_username)
        
        self.recovery_key_input = QLineEdit()
        self.recovery_key_input.setPlaceholderText("恢复密钥")
        key_layout.addWidget(self.recovery_key_input)
        layout.addWidget(self.recovery_key_container)
        
        # 邮箱验证码方式的输入框
        self.recovery_email_container = QWidget()
        email_layout = QVBoxLayout(self.recovery_email_container)
        email_layout.setContentsMargins(0, 0, 0, 0)

        self.recovery_email_username = QLineEdit()
        self.recovery_email_username.setPlaceholderText("用户名")
        self.recovery_email_username.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
            }
        """)
        email_layout.addWidget(self.recovery_email_username)

        self.recovery_email_input = QLineEdit()
        self.recovery_email_input.setPlaceholderText("邮箱地址")
        self.recovery_email_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
            }
        """)
        email_layout.addWidget(self.recovery_email_input)

        code_row = QHBoxLayout()
        self.recovery_code_input = QLineEdit()
        self.recovery_code_input.setPlaceholderText("验证码")
        self.recovery_code_input.setMaxLength(6)
        self.recovery_code_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
            }
        """)
        code_row.addWidget(self.recovery_code_input, 2)
        
        self.recovery_get_code_btn = QPushButton("获取验证码")
        self.recovery_get_code_btn.clicked.connect(self._request_recovery_code)
        code_row.addWidget(self.recovery_get_code_btn, 1)
        email_layout.addLayout(code_row)
        
        self.recovery_email_hint = QLabel("")
        self.recovery_email_hint.setStyleSheet("color: #666; font-size: 11px;")
        email_layout.addWidget(self.recovery_email_hint)
        
        layout.addWidget(self.recovery_email_container)
        self.recovery_email_container.hide()  # 默认隐藏
        
        # 新密码输入
        self.new_password_input = QLineEdit()
        self.new_password_input.setPlaceholderText("新密码")
        self.new_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.new_password_input)
        
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText("确认新密码")
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.confirm_password_input)
        
        reset_btn = QPushButton("重置密码")
        reset_btn.setObjectName("loginButton")
        reset_btn.clicked.connect(self._do_recovery)
        layout.addWidget(reset_btn)
        
        layout.addStretch()
        return page
    
    def _switch_recovery_method(self, method: str):
        """切换恢复方式"""
        if method == 'key':
            self.recovery_key_radio.setChecked(True)
            self.email_code_radio.setChecked(False)
            self.recovery_key_container.show()
            self.recovery_email_container.hide()
        else:
            self.recovery_key_radio.setChecked(False)
            self.email_code_radio.setChecked(True)
            self.recovery_key_container.hide()
            self.recovery_email_container.show()
            # 检查信任设备
            if self.device_trust:
                trusted = self.device_trust.get_trusted_emails()
                if trusted:
                    self.recovery_email_hint.setText(f"可用邮箱: {', '.join(trusted)}")
                else:
                    self.recovery_email_hint.setText("⚠️ 此设备无信任用户，无法使用此方式")
    
    def _request_recovery_code(self):
        """请求密码重置验证码"""
        if not self._ensure_connection():
            return
            
        email = self.recovery_email_input.text().strip()
        if not email:
            QMessageBox.warning(self, "提示", "请输入邮箱")
            return
        
        # 检查是否是信任设备的邮箱
        if not self.device_trust or not self.device_trust.has_trusted_device(email):
            QMessageBox.warning(self, "提示", "此邮箱未信任此设备，无法使用邮箱验证码重置密码")
            return
        
        result = self.network.request_email_code(email, 'reset')
        if result.get('success'):
            QMessageBox.information(self, "提示", "验证码已发送")
            self.recovery_get_code_btn.setEnabled(False)
            self.recovery_get_code_btn.setText("已发送")
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(60000, lambda: (
                self.recovery_get_code_btn.setEnabled(True),
                self.recovery_get_code_btn.setText("获取验证码")
            ))
        else:
            QMessageBox.critical(self, "错误", result.get('error', '发送失败'))
    
    def _request_email_code(self):
        """请求发送验证码"""
        if not self._ensure_connection():
            return
            
        email = self.email_input.text().strip()
        if not email:
            QMessageBox.warning(self, "提示", "请输入邮箱")
            return
        
        result = self.network.request_email_code(email, 'login')
        if result.get('success'):
            QMessageBox.information(self, "提示", "验证码已发送，请查收邮箱")
            self.get_code_btn.setEnabled(False)
            self.get_code_btn.setText("已发送")
            # 60秒后恢复
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(60000, lambda: (
                self.get_code_btn.setEnabled(True),
                self.get_code_btn.setText("获取验证码")
            ))
        else:
            QMessageBox.critical(self, "错误", result.get('error', '发送失败'))
    
    def _do_email_login(self):
        """邮箱验证码登录"""
        if not self._ensure_connection():
            return
            
        email = self.email_input.text().strip()
        code = self.email_code_input.text().strip()
        
        if not email or not code:
            QMessageBox.warning(self, "提示", "请输入邮箱和验证码")
            return
        
        # 检查该邮箱是否信任此设备
        is_trusted = self.device_trust and self.device_trust.has_trusted_device(email)
        
        if is_trusted:
            # 信任设备：先从本地解密
            device_data = self.device_trust.unlock_from_device(email)
            if device_data:
                # 验证邮箱验证码
                result = self.network.login_email(email, code)
                if result.get('success'):
                    # 使用本地存储的密钥
                    self.key_manager.unlock_from_device(device_data)
                    self.login_success.emit(result)
                    self.accept()
                    return
                else:
                    QMessageBox.critical(self, "错误", result.get('error', '验证码错误'))
                    return
        
        # 非信任设备：需要密码
        password = self.email_password_input.text()
        if not password:
            QMessageBox.warning(self, "提示", "请输入密码")
            return
        
        # 验证邮箱验证码
        result = self.network.login_email(email, code)
        if not result.get('success'):
            QMessageBox.critical(self, "错误", result.get('error', '验证码错误'))
            return
        
        # 使用密码解锁密钥
        if self.key_manager.unlock_with_password(password, result):
            # 检查是否需要询问信任设备（仅当该邮箱未信任时）
            if self.device_trust and not self.device_trust.has_trusted_device(email):
                self._pending_trust_data = {
                    'result': result,
                    'email': email
                }
                self._ask_trust_device()
            else:
                self.login_success.emit(result)
                self.accept()
        else:
            QMessageBox.critical(self, "错误", "密码错误，无法解锁密钥")
    
    def _ask_trust_device(self):
        """询问是否信任设备"""
        reply = QMessageBox.question(
            self, 
            "信任此设备", 
            "是否信任此设备？\n\n"
            "信任后，下次可使用邮箱验证码快速登录，无需输入密码。\n"
            "仅在您信任的个人设备上选择此选项。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 保存设备信任
            if self.device_trust and self.key_manager.user_keys:
                self.device_trust.trust_device(
                    username=self.key_manager.user_keys.username,
                    email=self._pending_trust_data.get('email', ''),
                    master_key=self.key_manager.user_keys.master_key,
                    private_key=self.key_manager.user_keys.private_key,
                    public_key=self.key_manager.user_keys.public_key
                )
                QMessageBox.information(self, "成功", "设备已信任，下次可使用验证码登录")
        
        # 完成登录
        self.login_success.emit(self._pending_trust_data['result'])
        self._pending_trust_data = None
        self.accept()
    
    def _do_register(self):
        if not self._ensure_connection():
            return
            
        username = self.reg_username.text().strip()
        email = self.reg_email.text().strip()
        password = self.reg_password.text()
        
        if not username or not email or not password:
            QMessageBox.warning(self, "提示", "请填写所有字段")
            return
        
        # 验证邮箱格式
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            QMessageBox.warning(self, "提示", "邮箱格式不正确")
            return
        
        # 验证密码强度
        from auth.password import PasswordManager
        valid, msg = PasswordManager.validate_password(password)
        if not valid:
            QMessageBox.warning(self, "提示", msg)
            return
        
        reg_data = self.key_manager.prepare_registration(password)
        result = self.network.register(
            username=username, email=email,
            password_hash=reg_data['password_hash'],
            public_key=reg_data['public_key'],
            encrypted_private_key=reg_data['encrypted_private_key'],
            encrypted_master_key=reg_data['encrypted_master_key'],
            master_key_salt=reg_data['master_key_salt'],
            recovery_key_encrypted=reg_data['recovery_key_encrypted'],
            recovery_key_salt=reg_data['recovery_key_salt'],
            recovery_key_hash=reg_data['recovery_key_hash']
        )
        
        if result.get('success'):
            QMessageBox.information(self, "成功", 
                f"注册成功！请保存恢复密钥:\n\n{reg_data['recovery_key']}")
            self.stack.setCurrentIndex(0)
        else:
            QMessageBox.critical(self, "错误", result.get('error', '注册失败'))
    
    def _do_recovery(self):
        """执行密码恢复"""
        if not self._ensure_connection():
            return
            
        new_password = self.new_password_input.text()
        confirm_password = self.confirm_password_input.text()
        
        if not new_password:
            QMessageBox.warning(self, "提示", "请输入新密码")
            return
        
        if new_password != confirm_password:
            QMessageBox.warning(self, "提示", "两次输入的密码不一致")
            return
        
        # 验证密码强度
        from auth.password import PasswordManager
        valid, msg = PasswordManager.validate_password(new_password)
        if not valid:
            QMessageBox.warning(self, "提示", msg)
            return
        
        # 判断使用哪种恢复方式
        use_email = self.email_code_radio.isChecked()
        email_for_trust = None
        
        if use_email:
            # 邮箱验证码方式（需要信任设备）
            username = self.recovery_email_username.text().strip()
            email = self.recovery_email_input.text().strip()
            code = self.recovery_code_input.text().strip()
            
            if not username or not email or not code:
                QMessageBox.warning(self, "提示", "请输入用户名、邮箱和验证码")
                return
            
            # 检查信任设备
            if not self.device_trust or not self.device_trust.has_trusted_device(email):
                QMessageBox.critical(self, "错误", "此邮箱未信任此设备，无法使用此方式")
                return
            
            # 从本地设备解锁密钥
            device_data = self.device_trust.unlock_from_device(email)
            if not device_data:
                QMessageBox.critical(self, "错误", "无法从设备读取密钥")
                return
            
            # 设置密钥管理器
            self.key_manager.unlock_from_device(device_data)
            email_for_trust = email
            
            # 准备新密码数据
            reset_data = self.key_manager.prepare_password_reset(new_password)
            
            # 发送密码重置请求（使用邮箱验证码）
            reset_result = self.network.reset_password(
                email=email,
                code=code,
                new_password_hash=reset_data['new_password_hash'],
                new_encrypted_master_key=reset_data['new_encrypted_master_key'],
                new_master_key_salt=reset_data['new_master_key_salt']
            )
        else:
            # 恢复密钥方式
            username = self.recovery_username.text().strip()
            recovery_key = self.recovery_key_input.text().strip()
            
            if not username or not recovery_key:
                QMessageBox.warning(self, "提示", "请填写用户名和恢复密钥")
                return
            
            # 获取用户数据
            result = self.network.get_user_for_recovery(username)
            if not result.get('success'):
                QMessageBox.critical(self, "错误", result.get('error', '获取用户信息失败'))
                return
            
            # 使用恢复密钥解锁主密钥
            if not self.key_manager.unlock_with_recovery(recovery_key, result):
                QMessageBox.critical(self, "错误", "恢复密钥无效")
                return
            
            email_for_trust = result.get('email')
            
            # 准备新密码数据
            reset_data = self.key_manager.prepare_password_reset(new_password)
            
            # 发送密码重置请求
            reset_result = self.network.reset_password(
                username=username,
                recovery_key=recovery_key,
                new_password_hash=reset_data['new_password_hash'],
                new_encrypted_master_key=reset_data['new_encrypted_master_key'],
                new_master_key_salt=reset_data['new_master_key_salt']
            )
        
        if reset_result.get('success'):
            # 自动解除设备信任（密码已更改，本地密钥加密已失效）
            if self.device_trust and email_for_trust:
                self.device_trust.clear_trust(email_for_trust)
                self._refresh_trust_ui()  # 立即刷新信任状态UI
            
            QMessageBox.information(self, "成功", "密码重置成功，请使用新密码登录")
            self.key_manager.lock()
            self.stack.setCurrentIndex(0)
        else:
            QMessageBox.critical(self, "错误", reset_result.get('error', '密码重置失败'))
