# main.py - VERSÃO CORRIGIDA COM HIGH DPI SUPPORT
import sys
import os
import pandas as pd

# **CORREÇÃO CRÍTICA: Configura DPI ANTES de importar PyQt5**
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
os.environ["QT_SCALE_FACTOR"] = "1.0"

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QGridLayout, QLabel, QAction, QFileDialog, 
                             QMessageBox, QGroupBox, QComboBox, QTableView, QHeaderView, QPushButton, QHBoxLayout, 
                             QTabWidget, QFrame, QSplitter, QTextEdit,QDialog,QScrollArea)
from PyQt5.QtGui import QFont, QStandardItemModel, QStandardItem, QIcon
from PyQt5.QtCore import Qt
from database import Database
from settings_dialog import SettingsDialog
from flow_dialog import FlowVisualDialog
from flow_dialog import FlowDialog
import datetime
from version import Version
from update_dialog import UpdateDialog
from tools_dialog import ToolsDialog
from screen_utils import ScreenManager, ResponsiveDialog

class MainWindow(QMainWindow, ResponsiveDialog):
    def __init__(self):
        super().__init__()
        self.db = Database("estoque.db")
        self.setWindowTitle("Sistema de Controle de Caixas v2.2 - Com Suporte para CDs")
        
        # **CORREÇÃO: Janela principal responsiva**
        width, height = ScreenManager.get_responsive_size(0.85, 0.8, 1200, 800, 1600, 1000)
        self.setGeometry(100, 100, width, height)
        
        # **CORREÇÃO: Centraliza janela**
        ScreenManager.center_window(self)
        
        # **CORREÇÃO: Configura font base responsivo**
        screen_geometry = ScreenManager.get_screen_geometry()
        if screen_geometry.width() < 1920:  # Telas menores
            font_size = 9
        else:  # Telas grandes
            font_size = 10
            
        base_font = QFont()
        base_font.setPointSize(font_size)
        self.setFont(base_font)
        
        self.cd_map = {
            'CD RJ': 'CD HORTIFRUTI - Rio de Janeiro (RJ)',
            'CD SP': 'CD HORTIFRUTI - São Paulo (SP)',
            'CD ES': 'CD HORTIFRUTI - Viana (ES)'
        }
        self.asset_types = ['HB 618', 'HB 623']

        self.init_ui()
        self.create_menu()
        self.update_all_views()

    def show_visual_flow_dialog(self):
        """Mostra o diálogo de fluxo visual melhorado - VERSÃO RESPONSIVA"""
        location_text = self.location_combo.currentText()
        if location_text and "Selecione" not in location_text:
            location_name = location_text.replace("🏢 ", "").replace("🏪 ", "")
            
            # Para CDs, usa FlowVisualDialog que tem botão de análise completa
            from flow_dialog import FlowVisualDialog, CDFlowAnalysisDialog
            
            if not location_name.startswith('LOJA'):  # É um CD
                # Pergunta se quer fluxo visual ou análise completa
                from PyQt5.QtWidgets import QMessageBox
                
                # **CORREÇÃO: Dialog responsivo**
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("Tipo de Análise")
                msg_box.setText(f"Qual análise deseja para {location_name}?")
                msg_box.setInformativeText("Escolha o tipo de análise:")
                
                visual_button = msg_box.addButton("📊 Fluxo Visual", QMessageBox.YesRole)
                complete_button = msg_box.addButton("📈 Análise Completa", QMessageBox.NoRole)
                cancel_button = msg_box.addButton("❌ Cancelar", QMessageBox.RejectRole)
                
                # **CORREÇÃO: Tamanho responsivo para message box**
                msg_box.setFont(QFont("Arial", 10))
                
                result = msg_box.exec_()
                
                if msg_box.clickedButton() == complete_button:
                    dialog = CDFlowAnalysisDialog(location_name, self.db, self)
                    dialog.exec_()
                elif msg_box.clickedButton() == visual_button:
                    dialog = FlowVisualDialog(location_name, self.db, self)
                    dialog.exec_()
            else:
                # Para lojas, usa FlowVisualDialog normal
                dialog = FlowVisualDialog(location_name, self.db, self)
                dialog.exec_()

    def create_menu(self):
        menu_bar = self.menuBar()
        
        menu_font = QFont()
        menu_font.setPointSize(10)
        menu_bar.setFont(menu_font)
        
        # Menu Arquivo
        file_menu = menu_bar.addMenu("📁 Arquivo")
        
        upload_action = QAction("📤 Novo Upload de Movimentos (.csv/.xlsx)", self)
        upload_action.triggered.connect(self.handle_upload)
        file_menu.addAction(upload_action)
        
        upload_inventory_action = QAction("📦 Upload de Inventário Inicial", self)
        upload_inventory_action.triggered.connect(self.quick_upload_inventory)
        file_menu.addAction(upload_inventory_action)
        
        file_menu.addSeparator()
        
        export_all_action = QAction("💾 Exportar Relatório Completo", self)
        export_all_action.triggered.connect(self.export_complete_report)
        file_menu.addAction(export_all_action)
        
        file_menu.addSeparator()
        exit_action = QAction("🚪 Sair", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Menu Visualização
        view_menu = menu_bar.addMenu("👁 Visualização")
        
        refresh_action = QAction("🔄 Atualizar Dados", self)
        refresh_action.triggered.connect(self.update_all_views)
        view_menu.addAction(refresh_action)

        # **MUDANÇA: Menu Ferramentas com novo diálogo**
        tools_menu = menu_bar.addMenu("🔧 Ferramentas")
        tools_action = QAction("⚙️ Abrir Ferramentas", self)
        tools_action.triggered.connect(self.open_tools_dialog)
        tools_menu.addAction(tools_action)

        # Menu de Atualizações
        update_menu = menu_bar.addMenu("🔄 Atualizações")
        
        check_updates_action = QAction("🔍 Verificar Atualizações", self)
        check_updates_action.triggered.connect(self.check_updates_manual)
        update_menu.addAction(check_updates_action)
        
        update_menu.addSeparator()
        
        about_action = QAction("ℹ️ Sobre", self)
        about_action.triggered.connect(self.show_about)
        update_menu.addAction(about_action)


    def open_tools_dialog(self):
        """Abre o novo diálogo de ferramentas"""
        dialog = ToolsDialog(self.db, self)
        dialog.database_cleared.connect(self.update_all_views)
        dialog.appearance_changed.connect(self.apply_appearance_settings)
        dialog.exec_()

    def apply_appearance_settings(self, settings):
        """Aplica configurações de aparência em tempo real"""
        try:
            # Aplica fonte global
            font = QFont(settings['font_family'], settings['font_size'])
            self.setFont(font)
            QApplication.instance().setFont(font)
            
            # Aplica cores (stylesheet global)
            if settings['theme'] == 'Escuro':
                dark_style = f"""
                QMainWindow {{
                    background-color: #2b2b2b;
                    color: #ffffff;
                }}
                QTabWidget::pane {{
                    border: 1px solid {settings['primary_color']};
                    background-color: #404040;
                }}
                QTabBar::tab {{
                    background: #505050;
                    color: #ffffff;
                    padding: 10px 20px;
                }}
                QTabBar::tab:selected {{
                    background: {settings['primary_color']};
                }}
                QGroupBox {{
                    color: #ffffff;
                    border: 2px solid {settings['primary_color']};
                }}
                QLabel {{
                    color: #ffffff;
                }}
                """
                self.setStyleSheet(dark_style)
            else:
                # Tema claro
                light_style = f"""
                QMainWindow {{
                    background-color: {settings['background_color']};
                    color: {settings['text_color']};
                }}
                QTabWidget::pane {{
                    border: 1px solid #c0c0c0;
                }}
                QTabBar::tab {{
                    background: #f0f0f0;
                    padding: 10px 20px;
                }}
                QTabBar::tab:selected {{
                    background: {settings['primary_color']};
                    color: white;
                }}
                """
                self.setStyleSheet(light_style)
            
            # Força atualização da interface
            self.update()
            self.repaint()
            
            print(f"✅ Configurações aplicadas: Fonte {settings['font_family']} {settings['font_size']}pt, Tema {settings['theme']}")
            
        except Exception as e:
            print(f"❌ Erro ao aplicar configurações: {e}")

    def open_tools_dialog(self):
        """Abre o novo diálogo de ferramentas"""
        dialog = ToolsDialog(self.db, self)
        dialog.database_cleared.connect(self.update_all_views)
        dialog.appearance_changed.connect(self.apply_appearance_settings)
        dialog.exec_()

    def check_updates_manual(self):
        """Abre diálogo de atualizações manualmente"""
        dialog = UpdateDialog(self, auto_check=False)
        dialog.exec_()

    def show_about(self):
        """Mostra informações sobre a aplicação"""
        app_info = Version.get_app_info()
        
        about_text = f"""
        <div style="text-align: center;">
            <h1>🔧 {app_info['name']}</h1>
            <h3 style="color: #007bff;">Versão {app_info['version']}</h3>
        </div>
        
        <hr>
        
        <h3>📊 Informações da Versão</h3>
        <table border="0" cellpadding="5">
            <tr><td><b>🏷️ Versão:</b></td><td>{app_info['version']}</td></tr>
            <tr><td><b>📅 Data de Build:</b></td><td>{app_info['build_date']}</td></tr>
            <tr><td><b>📝 Descrição:</b></td><td>{app_info['description']}</td></tr>
        </table>
        
        <hr>
        
        <h3>⚡ Funcionalidades Principais</h3>
        <ul>
            <li>📦 <b>Inventário Inicial:</b> Carregamento de estoque base para lojas</li>
            <li>📊 <b>Controle de Movimentos:</b> Remessas, regressos e transferências</li>
            <li>🎯 <b>Fluxo Visual:</b> Acompanhe mudanças dia a dia (Lojas e CDs)</li>
            <li>📈 <b>Relatórios Completos:</b> Exportação em Excel/CSV</li>
            <li>🔄 <b>Atualizações Automáticas:</b> Sistema sempre atualizado</li>
            <li>🏪 <b>Multi-Local:</b> CDs e Lojas integrados</li>
        </ul>
        
        <hr>
        
        <h3>🆕 Novidades desta Versão</h3>
        <ul>
            <li>✅ <b>Suporte para CDs:</b> Fluxo visual agora funciona para CDs</li>
            <li>✅ <b>Fonts Corrigidas:</b> Textos maiores e mais legíveis</li>
            <li>✅ <b>Atualizações Melhoradas:</b> Sistema de update via GitHub</li>
            <li>✅ <b>Interface Otimizada:</b> Cards maiores e melhor visualização</li>
        </ul>
        
        <p style="text-align: center; margin-top: 20px;">
            <small style="color: #666;">
                © 2025 - Sistema de Controle de Caixas<br>
                <b>🏗️ Build:</b> {datetime.datetime.now().strftime('%d/%m/%Y às %H:%M')}<br>
                <b>🔗 Powered by:</b> GitHub Actions + PyInstaller
            </small>
        </p>
        """
        
        # Cria diálogo customizado
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QPushButton
        
        about_dialog = QDialog(self)
        about_dialog.setWindowTitle(f"Sobre {app_info['name']}")
        about_dialog.setFixedSize(700, 800)  # **CORREÇÃO: Janela maior**
        
        layout = QVBoxLayout(about_dialog)
        
        # Área de scroll para o conteúdo
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        # Widget de conteúdo
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        
        # Label com o texto HTML
        about_label = QLabel(about_text)
        about_label.setWordWrap(True)
        about_label.setOpenExternalLinks(True)
        about_label.setFont(QFont("Arial", 11))  # **CORREÇÃO: Fonte maior**
        about_label.setStyleSheet("""
            QLabel {
                padding: 20px;
                background-color: #f8f9fa;
                border-radius: 8px;
                line-height: 1.4;
            }
        """)
        
        content_layout.addWidget(about_label)
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)
        
        # Botões
        button_layout = QHBoxLayout()
        
        # Botão para verificar atualizações
        update_btn = QPushButton("🔄 Verificar Atualizações")
        update_btn.setFont(QFont("Arial", 11))  # **CORREÇÃO: Fonte maior**
        update_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        update_btn.clicked.connect(self.check_updates_manual)
        button_layout.addWidget(update_btn)
        
        button_layout.addStretch()
        
        # Botão fechar
        close_btn = QPushButton("❌ Fechar")
        close_btn.setFont(QFont("Arial", 11))  # **CORREÇÃO: Fonte maior**
        close_btn.clicked.connect(about_dialog.close)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        about_dialog.exec_()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # Layout principal com splitter
        main_layout = QVBoxLayout(main_widget)
        
        # Status bar personalizada
        self.create_status_section(main_layout)
        
        # Splitter principal
        main_splitter = QSplitter(Qt.Vertical)
        
        # Seção superior - Estoque
        upper_widget = QWidget()
        self.create_stock_section(upper_widget)
        main_splitter.addWidget(upper_widget)
        
        # Seção inferior - Análise detalhada
        lower_widget = QWidget()
        self.create_analysis_section(lower_widget)
        main_splitter.addWidget(lower_widget)
        
        # Configura proporções do splitter
        main_splitter.setSizes([400, 500])
        main_layout.addWidget(main_splitter)

    def create_status_section(self, parent_layout):
        """Cria seção de status do sistema"""
        status_frame = QFrame()
        status_frame.setFrameStyle(QFrame.Box)
        status_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                margin: 2px;
            }
        """)
        
        status_layout = QHBoxLayout(status_frame)
        
        # **CORREÇÃO: Fontes maiores no status**
        status_font = QFont("Arial", 11)
        
        # Status do inventário
        self.inventory_status = QLabel("📦 Inventário: Não carregado")
        self.inventory_status.setFont(status_font)
        self.inventory_status.setStyleSheet("color: #dc3545; font-weight: bold;")
        status_layout.addWidget(self.inventory_status)
        
        status_layout.addStretch()
        
        # Contador de registros
        self.records_count = QLabel("📊 Registros: 0")
        self.records_count.setFont(status_font)
        status_layout.addWidget(self.records_count)
        
        # Última atualização
        self.last_update = QLabel("🕐 Última atualização: --")
        self.last_update.setFont(status_font)
        status_layout.addWidget(self.last_update)
        
        parent_layout.addWidget(status_frame)

    def create_stock_section(self, parent_widget):
        """Cria seção de visualização de estoque"""
        layout = QVBoxLayout(parent_widget)
        
        # Título melhorado
        title_layout = QHBoxLayout()
        title_label = QLabel("📊 VISÃO GERAL DO ESTOQUE")
        title_font = QFont()
        title_font.setPointSize(16)  # **CORREÇÃO: Fonte maior**
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # Botão de atualização rápida
        refresh_btn = QPushButton("🔄 Atualizar")
        refresh_btn.setFont(QFont("Arial", 11))  # **CORREÇÃO: Fonte maior**
        refresh_btn.clicked.connect(self.update_all_views)
        refresh_btn.setStyleSheet("QPushButton { padding: 8px 20px; }")  # **CORREÇÃO: Padding maior**
        title_layout.addWidget(refresh_btn)
        
        layout.addLayout(title_layout)

        # Abas melhoradas
        self.tabs = QTabWidget()
        self.tabs.setFont(QFont("Arial", 10))  # **CORREÇÃO: Fonte maior nas abas**
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #c0c0c0;
                border-radius: 5px;
            }
            QTabBar::tab {
                background: #f0f0f0;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                font-size: 11px;
            }
            QTabBar::tab:selected {
                background: #007bff;
                color: white;
            }
        """)
        
        self.stock_widgets = {}
        
        # Cria abas
        self.create_stock_tab("📊 Total")
        for asset in self.asset_types:
            self.create_stock_tab(f"📦 {asset}")

        layout.addWidget(self.tabs)

    def create_analysis_section(self, parent_widget):
        """Cria seção de análise detalhada"""
        layout = QVBoxLayout(parent_widget)
        
        details_group = QGroupBox("🔍 ANÁLISE DETALHADA POR LOCAL")
        details_group.setFont(QFont("Arial", 12, QFont.Bold))  # **CORREÇÃO: Fonte maior**
        details_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #007bff;
                border-radius: 5px;
                margin-top: 1ex;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 5px;
                background-color: white;
            }
        """)
        
        details_layout = QVBoxLayout(details_group)
        
        # Layout de filtro e ações melhorado
        filter_action_layout = QHBoxLayout()
        
        local_label = QLabel("🏪 Local:")
        local_label.setFont(QFont("Arial", 11))  # **CORREÇÃO: Fonte maior**
        filter_action_layout.addWidget(local_label, 1)
        
        self.location_combo = QComboBox()
        self.location_combo.setFont(QFont("Arial", 11))  # **CORREÇÃO: Fonte maior**
        self.location_combo.setStyleSheet("QComboBox { padding: 8px; }")  # **CORREÇÃO: Padding maior**
        self.location_combo.currentIndexChanged.connect(self.update_location_details)
        filter_action_layout.addWidget(self.location_combo, 4)
        
        # **CORREÇÃO: Botões de ação com fontes maiores**
        button_font = QFont("Arial", 10)
        
        self.view_flow_button = QPushButton("📊 Fluxo Clássico")
        self.view_flow_button.setFont(button_font)
        self.view_flow_button.setStyleSheet("QPushButton { background-color: #28a745; color: white; padding: 8px 15px; }")
        self.view_flow_button.clicked.connect(self.show_flow_dialog)
        filter_action_layout.addWidget(self.view_flow_button, 2)
        
        self.view_visual_flow_button = QPushButton("🎯 Fluxo Visual")
        self.view_visual_flow_button.setFont(button_font)
        self.view_visual_flow_button.setStyleSheet("QPushButton { background-color: #007bff; color: white; padding: 8px 15px; }")
        self.view_visual_flow_button.clicked.connect(self.show_visual_flow_dialog)
        filter_action_layout.addWidget(self.view_visual_flow_button, 2)
        
        self.export_button = QPushButton("💾 Exportar")
        self.export_button.setFont(button_font)
        self.export_button.setStyleSheet("QPushButton { background-color: #6c757d; color: white; padding: 8px 15px; }")
        self.export_button.clicked.connect(self.export_history)
        filter_action_layout.addWidget(self.export_button, 2)
        
        details_layout.addLayout(filter_action_layout)
        
        # **CORREÇÃO: Tabela melhorada com fonte maior**
        self.history_table = QTableView()
        self.history_table.setFont(QFont("Arial", 10))  # **CORREÇÃO: Fonte maior**
        self.history_table.setAlternatingRowColors(True)
        self.history_table.setEditTriggers(QTableView.NoEditTriggers)
        self.history_table.setStyleSheet("""
            QTableView {
                gridline-color: #d0d0d0;
                selection-background-color: #b3d9ff;
            }
            QTableView::item {
                padding: 6px;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 8px;
                border: 1px solid #dee2e6;
                font-weight: bold;
            }
        """)
        
        self.history_model = QStandardItemModel()
        self.history_table.setModel(self.history_model)
        
        details_layout.addWidget(self.history_table)
        layout.addWidget(details_group)

    def create_stock_tab(self, asset_name):
        """Cria aba de estoque com layout melhorado"""
        tab_widget = QWidget()
        layout = QGridLayout(tab_widget)
        layout.setSpacing(15)  # **CORREÇÃO: Espaçamento maior**
        
        widgets = {}
        
        # **CORREÇÃO: Cabeçalho com fonte maior**
        headers = ["🏢 Local", "📦 Estoque Atual", "📈 Status"]
        for i, header in enumerate(headers):
            header_label = QLabel(f"<b>{header}</b>")
            header_label.setFont(QFont("Arial", 12, QFont.Bold))  # **CORREÇÃO: Fonte maior**
            header_label.setStyleSheet("""
                QLabel {
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                    padding: 12px;
                    font-size: 12px;
                }
            """)
            layout.addWidget(header_label, 0, i)
        
        # **CORREÇÃO: Linhas de CDs com fonte maior**
        content_font = QFont("Arial", 11)
        
        row = 1
        for cd_key, cd_name in self.cd_map.items():
            # Nome do CD
            cd_label = QLabel(cd_name)
            cd_label.setFont(content_font)
            cd_label.setStyleSheet("padding: 12px; border-bottom: 1px solid #eee;")
            layout.addWidget(cd_label, row, 0)
            
            # Estoque
            stock_label = QLabel("0")
            stock_label.setFont(QFont("Arial", 11, QFont.Bold))
            stock_label.setStyleSheet("padding: 12px; border-bottom: 1px solid #eee;")
            widgets[cd_key] = stock_label
            layout.addWidget(stock_label, row, 1)
            
            # Status
            status_label = QLabel("🟢 OK")
            status_label.setFont(content_font)
            status_label.setStyleSheet("padding: 12px; border-bottom: 1px solid #eee;")
            widgets[f"{cd_key}_status"] = status_label
            layout.addWidget(status_label, row, 2)
            
            row += 1
            
        # **CORREÇÃO: Linha de total das lojas com destaque e fonte maior**
        total_frame = QFrame()
        total_frame.setStyleSheet("""
            QFrame {
                background-color: #e8f4fd;
                border: 2px solid #007bff;
                border-radius: 5px;
                margin: 8px;
            }
        """)
        total_layout = QGridLayout(total_frame)
        
        total_title = QLabel("<b>🏪 TOTAL ESTOQUE LOJAS</b>")
        total_title.setFont(QFont("Arial", 12, QFont.Bold))
        total_layout.addWidget(total_title, 0, 0)
        
        total_stock_label = QLabel("0")
        total_stock_label.setFont(QFont("Arial", 14, QFont.Bold))  # **CORREÇÃO: Fonte maior**
        total_stock_label.setStyleSheet("color: #007bff;")
        widgets['total_lojas'] = total_stock_label
        total_layout.addWidget(total_stock_label, 0, 1)
        
        total_status_label = QLabel("📊 Calculado")
        total_status_label.setFont(QFont("Arial", 11))
        widgets['total_lojas_status'] = total_status_label
        total_layout.addWidget(total_status_label, 0, 2)
        
        layout.addWidget(total_frame, row, 0, 1, 3)
        
        self.tabs.addTab(tab_widget, asset_name)
        self.stock_widgets[asset_name] = widgets

    # Resto dos métodos permanecem iguais, apenas com fontes corrigidas onde necessário...
    def update_all_views(self):
        """Atualização melhorada com feedback visual"""
        try:
            # Atualiza status
            self.update_status_info()
            
            # Calcula estoques (agora com inventário)
            stock_data = self.db.calculate_stock_by_asset_with_inventory()
            
            # Atualiza abas
            for asset_tab_name, widgets in self.stock_widgets.items():
                total_lojas_asset = 0
                
                # Atualiza CDs
                for cd_key, cd_full_name in self.cd_map.items():
                    cd_stock = 0
                    if "Total" in asset_tab_name:
                        cd_stock = sum(stock_data.get(cd_full_name, {}).values())
                    else:
                        asset_clean = asset_tab_name.replace("📦 ", "")
                        cd_stock = stock_data.get(cd_full_name, {}).get(asset_clean, 0)
                    
                    widgets[cd_key].setText(f"{cd_stock:,}".replace(",", "."))
                    
                    # Atualiza status do CD
                    if cd_stock < 0:
                        widgets[f"{cd_key}_status"].setText("🔴 Negativo")
                        widgets[f"{cd_key}_status"].setStyleSheet("color: #dc3545;")
                    elif cd_stock == 0:
                        widgets[f"{cd_key}_status"].setText("🟡 Zero")
                        widgets[f"{cd_key}_status"].setStyleSheet("color: #ffc107;")
                    else:
                        widgets[f"{cd_key}_status"].setText("🟢 OK")
                        widgets[f"{cd_key}_status"].setStyleSheet("color: #28a745;")
                
                # Calcula total das lojas
                for location, assets in stock_data.items():
                    if location.startswith("LOJA"):
                        if "Total" in asset_tab_name:
                            total_lojas_asset += sum(assets.values())
                        else:
                            asset_clean = asset_tab_name.replace("📦 ", "")
                            total_lojas_asset += assets.get(asset_clean, 0)
               
                widgets['total_lojas'].setText(f"{total_lojas_asset:,}".replace(",", "."))
                
                # Atualiza status do total de lojas
                if total_lojas_asset < 0:
                    widgets['total_lojas_status'].setText("🔴 Estoque Negativo")
                    widgets['total_lojas_status'].setStyleSheet("color: #dc3545;")
                elif total_lojas_asset == 0:
                    widgets['total_lojas_status'].setText("🟡 Sem Estoque")
                    widgets['total_lojas_status'].setStyleSheet("color: #ffc107;")
                else:
                    widgets['total_lojas_status'].setText("🟢 Estoque Positivo")
                    widgets['total_lojas_status'].setStyleSheet("color: #28a745;")

            # Atualiza combo de locais
            self.update_locations_combo()
            
            # Atualiza detalhes do local
            self.update_location_details()
            
            # Atualiza timestamp
            from datetime import datetime
            self.last_update.setText(f"🕐 Última atualização: {datetime.now().strftime('%H:%M:%S')}")
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao atualizar visualizações:\n{e}")

    def update_status_info(self):
        """Atualiza informações de status do sistema"""
        # Verifica se existe inventário
        inventory_check = self.db._execute_query("SELECT COUNT(*) as count FROM inventario_inicial")
        has_inventory = inventory_check[0]['count'] > 0 if inventory_check else False
        
        if has_inventory:
            self.inventory_status.setText("📦 Inventário: ✅ Carregado")
            self.inventory_status.setStyleSheet("color: #28a745; font-weight: bold;")
        else:
            self.inventory_status.setText("📦 Inventário: ❌ Não carregado")
            self.inventory_status.setStyleSheet("color: #dc3545; font-weight: bold;")
        
        # Conta registros de movimentos
        movements_check = self.db._execute_query("SELECT COUNT(*) as count FROM movimentos")
        movements_count = movements_check[0]['count'] if movements_check else 0
        self.records_count.setText(f"📊 Registros: {movements_count:,}".replace(",", "."))

    def update_locations_combo(self):
        """Atualiza combo de locais"""
        self.location_combo.blockSignals(True)
        current_selection = self.location_combo.currentText()
        self.location_combo.clear()
        
        self.location_combo.addItem("🔍 Selecione um local...")
        
        # Adiciona CDs
        cds = sorted(self.db.get_all_locations('cd'))
        if cds:
            for cd in cds:
                self.location_combo.addItem(f"🏢 {cd}")
        
        # Adiciona separador visual
        self.location_combo.insertSeparator(self.location_combo.count())
        
        # Adiciona lojas
        lojas = sorted(self.db.get_all_locations('loja'))
        if lojas:
            for loja in lojas:
                self.location_combo.addItem(f"🏪 {loja}")
        
        # Restaura seleção
        for i in range(self.location_combo.count()):
            if current_selection in self.location_combo.itemText(i):
                self.location_combo.setCurrentIndex(i)
                break
        
        self.location_combo.blockSignals(False)

    def update_location_details(self):
        """Atualiza detalhes do local selecionado"""
        self.history_model.clear()
        self.history_model.setHorizontalHeaderLabels([
            '📅 Data', '🔄 Movimento', '📦 Ativo (RTI)', 
            '📤 Origem', '📥 Destino', '🔢 Quantidade'
        ])
        
        location_text = self.location_combo.currentText()
        if not location_text or "Selecione" in location_text:
            self.view_flow_button.setEnabled(False)
            self.view_visual_flow_button.setEnabled(False)
            self.export_button.setEnabled(False)
            return

        # Extrai nome real do local (remove emoji e prefixo)
        location_name = location_text.replace("🏢 ", "").replace("🏪 ", "")
        
        self.view_flow_button.setEnabled(True)
        self.view_visual_flow_button.setEnabled(True)  # **CORREÇÃO: Sempre habilitado**
        self.export_button.setEnabled(True)
        
        # Busca histórico
        history = self.db.get_location_history(location_name)
        
        for row_data in history:
            items = []
            for i, item in enumerate(row_data):
                if i == 0 and item:  # Data
                    try:
                        from datetime import datetime
                        date_obj = datetime.strptime(str(item), '%Y-%m-%d')
                        formatted_date = date_obj.strftime('%d/%m/%Y')
                        items.append(QStandardItem(formatted_date))
                    except:
                        items.append(QStandardItem(str(item) if item else ""))
                elif i == 1 and item:  # Tipo de movimento
                    movement_icons = {
                        'Remessa': '📤',
                        'Regresso': '📥', 
                        'Entrega': '🚚',
                        'Devolução de Entrega': '↩️',
                        'Transferencia': '🔄',
                        'Retorno': '🔙'
                    }
                    icon = movement_icons.get(item, '📋')
                    items.append(QStandardItem(f"{icon} {item}"))
                else:
                    items.append(QStandardItem(str(item) if item is not None else ""))
            
            self.history_model.appendRow(items)
        
        # **CORREÇÃO: Configura colunas com tamanhos adequados**
        header = self.history_table.horizontalHeader()
        header.setFont(QFont("Arial", 10, QFont.Bold))  # **CORREÇÃO: Fonte maior no header**
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Data
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Movimento
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # RTI
        header.setSectionResizeMode(3, QHeaderView.Stretch)           # Origem
        header.setSectionResizeMode(4, QHeaderView.Stretch)           # Destino
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Quantidade

    # Resto dos métodos permanecem iguais...
    def quick_upload_inventory(self):
        """Upload rápido de inventário pelo menu"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Arquivo de Inventário", "", 
            "Arquivos de Dados (*.csv *.xlsx)"
        )
        
        if file_path:
            settings_dialog = SettingsDialog(self.db, self)
            try:
                # Simula upload usando o método da settings dialog
                df = pd.read_csv(file_path, sep=';') if file_path.endswith('.csv') else pd.read_excel(file_path)
                
                # Validações
                required_columns = ['loja_nome', 'ativo', 'quantidade']
                if not all(col in df.columns for col in required_columns):
                    raise ValueError(f"O arquivo deve conter as colunas: {', '.join(required_columns)}")
                
                self.db.insert_inventory_data(df)
                QMessageBox.information(
                    self, "Sucesso", 
                    f"Inventário inicial carregado!\n{len(df)} registros processados."
                )
                self.update_all_views()
                
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro no upload:\n{e}")

    def handle_upload(self):
        """Upload de movimentos com verificação de inventário"""
        # Verifica se há inventário carregado
        inventory_check = self.db._execute_query("SELECT COUNT(*) as count FROM inventario_inicial")
        has_inventory = inventory_check[0]['count'] > 0 if inventory_check else False
        
        if not has_inventory:
            reply = QMessageBox.question(
                self, "Inventário Não Encontrado",
                "Não foi encontrado inventário inicial carregado.\n\n"
                "É recomendado carregar o inventário inicial antes dos movimentos.\n"
                "Deseja continuar mesmo assim?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Arquivo de Movimentos", "", 
            "Arquivos de Dados (*.csv *.xlsx)"
        )
        
        if file_path:
            try:
                df = pd.read_csv(file_path, sep=';') if file_path.endswith('.csv') else pd.read_excel(file_path)
                
                if 'Data' not in df.columns or 'Quant.' not in df.columns or 'RTI' not in df.columns:
                    raise ValueError("O arquivo deve conter as colunas 'Data', 'Quant.' e 'RTI'.")
                
                self.db.insert_data(df)
                QMessageBox.information(self, "Sucesso", f"{len(df)} registros de movimento importados.")
                self.update_all_views()
                
            except Exception as e:
                QMessageBox.critical(self, "Erro no Upload", f"Falha ao processar arquivo:\n{e}")

    def show_flow_dialog(self):
        """Mostra diálogo de fluxo clássico"""
        location_text = self.location_combo.currentText()
        if location_text and "Selecione" not in location_text:
            location_name = location_text.replace("🏢 ", "").replace("🏪 ", "")
            flow_data = self.db.get_location_history(location_name)  # **CORREÇÃO: Usa histórico em vez de flow_data**
            dialog = FlowDialog(location_name, flow_data, self)
            dialog.exec_()

    def export_complete_report(self):
        """Exporta relatório completo do sistema"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Salvar Relatório Completo", 
                f"relatorio_completo_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.xlsx", 
                "Excel (*.xlsx)"
            )
            
            if file_path:
                with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                    # Estoque atual
                    stock_data = self.db.calculate_stock_by_asset_with_inventory()
                    stock_list = []
                    for location, assets in stock_data.items():
                        for asset, qty in assets.items():
                            stock_list.append({
                                'Local': location,
                                'Ativo': asset,
                                'Quantidade': qty,
                                'Tipo': 'CD' if 'CD' in location else 'Loja'
                            })
                    
                    if stock_list:
                        stock_df = pd.DataFrame(stock_list)
                        stock_df.to_excel(writer, sheet_name='Estoque Atual', index=False)
                    
                    # Movimentos
                    movements_query = """
                    SELECT data_movimento, tipo_movimento, local_origem, local_destino, 
                            rti, quantidade, guia, nota_fiscal
                    FROM movimentos ORDER BY data_movimento DESC
                    """
                    movements = self.db._execute_query(movements_query)
                    if movements:
                        movements_df = pd.DataFrame([dict(row) for row in movements])
                        movements_df.to_excel(writer, sheet_name='Movimentos', index=False)
                    
                    # Inventário inicial
                    inventory_query = """
                    SELECT loja_nome_simples, ativo, quantidade, data_inventario
                    FROM inventario_inicial ORDER BY loja_nome_simples
                    """
                    inventory = self.db._execute_query(inventory_query)
                    if inventory:
                        inventory_df = pd.DataFrame([dict(row) for row in inventory])
                        inventory_df.to_excel(writer, sheet_name='Inventario Inicial', index=False)
                
                QMessageBox.information(self, "Sucesso", f"Relatório completo exportado para:\n{file_path}")
                
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar relatório:\n{e}")

    def export_history(self):
        """Exporta histórico do local selecionado"""
        location_text = self.location_combo.currentText()
        if not location_text or self.history_model.rowCount() == 0:
            QMessageBox.warning(self, "Aviso", "Não há dados para exportar.")
            return

        location_name = location_text.replace("🏢 ", "").replace("🏪 ", "")
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Salvar Histórico", 
            f"historico_{location_name.replace(' ', '_')}.csv", 
            "CSV (*.csv)"
        )
        
        if file_path:
            try:
                data = []
                headers = [self.history_model.horizontalHeaderItem(i).text() 
                            for i in range(self.history_model.columnCount())]
                
                for row in range(self.history_model.rowCount()):
                    row_data = [self.history_model.item(row, col).text() 
                                for col in range(self.history_model.columnCount())]
                    data.append(row_data)
                
                df = pd.DataFrame(data, columns=headers)
                df.to_csv(file_path, index=False, sep=';', encoding='utf-8-sig')
                QMessageBox.information(self, "Sucesso", f"Histórico exportado para:\n{file_path}")
                
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao exportar:\n{e}")

    def open_settings(self):
        """Abre diálogo de ferramentas (compatibilidade)"""
        self.open_tools_dialog()

    def closeEvent(self, event):
        """Evento de fechamento da aplicação"""
        reply = QMessageBox.question(
            self, "Confirmar Saída",
            "Deseja realmente sair do sistema?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.db.close()
            event.accept()
        else:
            event.ignore()

if __name__ == '__main__':
    # **CORREÇÃO CRÍTICA: Configura DPI ANTES de criar QApplication**
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    os.environ["QT_SCALE_FACTOR"] = "1.0"
    
    app = QApplication(sys.argv)
    
    # **CORREÇÃO: Ativa High DPI scaling**
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # **CORREÇÃO: Font global responsivo**
    screen = app.primaryScreen()
    screen_size = screen.size()
    
    if screen_size.width() < 1920:

        app.setFont(QFont("Arial", 9))
    else:
        app.setFont(QFont("Arial", 10))
    
    # Configuração do estilo da aplicação
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.show()
    
    # **NOVO: Verificação automática de atualizações na inicialização**
    try:
        update_dialog = UpdateDialog(window, auto_check=True)
    except Exception as e:
        print(f"⚠️ Não foi possível verificar atualizações: {e}")
    
    sys.exit(app.exec_())