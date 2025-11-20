import sys
import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QTabWidget, QLabel, QLineEdit,
    QPushButton, QHeaderView, QTextEdit, QFrame, QSpacerItem, QSizePolicy,
    QDialog, QFormLayout, QMessageBox, QDialogButtonBox
)
from PyQt5.QtGui import QIcon, QFont, QColor
from PyQt5.QtCore import QTimer, Qt, QSize

DB_FILE = "questions.db"

def get_db_conn():
    return sqlite3.connect(DB_FILE, check_same_thread=False)


class FuturisticAdmin(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CS2 Bot — Админ Панель")
        self.setGeometry(100, 50, 1500, 900)
        self.setMinimumSize(1200, 700)

        
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0d1117;
                color: #c9d1d9;
            }
            QLabel {
                color: #58a6ff;
                font-size: 16px;
                font-weight: 600;
                padding: 8px 0;
            }
            QLabel#header {
                font-size: 28px;
                font-weight: bold;
                color: #58a6ff;
                padding: 20px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1a1f2d, stop:1 #21262d);
                border-bottom: 1px solid #30363d;
            }
            QPushButton {
                background-color: #21262d;
                color: #c9d1d9;
                border: 1px solid #30363d;
                border-radius: 10px;
                padding: 10px 20px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1f6feb;
                border: 1px solid #388bfd;
                color: white;
            }
            QPushButton:pressed {
                background-color: #1a5fb4;
            }
            QPushButton#editBtn {
                background-color: #30363d;
                padding: 8px 16px;
                border-radius: 8px;
            }
            QPushButton#editBtn:hover {
                background-color: #58a6ff;
                color: #000;
            }
            QLineEdit {
                background-color: #161b22;
                color: #c9d1d9;
                border: 1px solid #30363d;
                border-radius: 10px;
                padding: 12px 16px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #58a6ff;
                background-color: #0d1117;
            }
            QTextEdit {
                background-color: #161b22;
                color: #c9d1d9;
                border: 1px solid #30363d;
                border-radius: 10px;
                padding: 12px;
                font-size: 14px;
            }
            QTableWidget {
                background-color: #161b22;
                gridline-color: #30363d;
                color: #c9d1d9;
                border: none;
                border-radius: 12px;
                font-size: 14px;
            }
            QTableWidget::item {
                padding: 10px;
            }
            QTableWidget::item:selected {
                background-color: #1f6feb;
            }
            QHeaderView::section {
                background-color: #21262d;
                color: #58a6ff;
                padding: 12px;
                border: none;
                font-weight: bold;
                font-size: 14px;
            }
            QTabWidget::pane {
                border: none;
                background-color: #0d1117;
            }
            QTabBar::tab {
                background-color: #161b22;
                color: #8b949e;
                padding: 14px 28px;
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
                margin-right: 4px;
                font-size: 15px;
                font-weight: 500;
            }
            QTabBar::tab:selected {
                background-color: #1f6feb;
                color: white;
            }
            QTabBar::tab:hover:!selected {
                background-color: #30363d;
                color: white;
            }
            QScrollBar:vertical {
                background: #0d1117;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #30363d;
                border-radius: 6px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: #58a6ff;
            }
        """)

        
        header = QLabel("CS2 Bot — Панель управления")
        header.setObjectName("header")
        header.setAlignment(Qt.AlignCenter)
        header.setFont(QFont("Segoe UI", 20, QFont.Bold))

        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        main_layout.addWidget(header)

        self.tabs = QTabWidget()
        self.tabs.setFont(QFont("Segoe UI", 11))
        main_layout.addWidget(self.tabs)

        self.init_logs_tab()
        self.init_users_tab()
        self.init_qa_tab()
        self.init_feedback_tab()
        self.init_stats_tab()

        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_all)
        self.timer.start(4000)

    def refresh_all(self):
        self.load_logs()
        self.load_users()
        self.load_qa()
        self.load_feedback()
        self.update_stats()

   
    def init_logs_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("🔍 Поиск:"))
        self.search_logs = QLineEdit()
        self.search_logs.setPlaceholderText("Введите ID или часть вопроса...")
        self.search_logs.textChanged.connect(self.load_logs)
        search_layout.addWidget(self.search_logs)
        layout.addLayout(search_layout)

        layout.addWidget(QLabel("🛰 Последние запросы пользователей"))
        
        self.logs_table = QTableWidget()
        self.logs_table.setColumnCount(3)
        self.logs_table.setHorizontalHeaderLabels(["User ID", "Вопрос", "Время"])
        self.logs_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.logs_table)

        self.tabs.addTab(tab, " Логи")

    def load_logs(self):
        query = self.search_logs.text().lower()
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT user_id, question, timestamp FROM logs ORDER BY id DESC LIMIT 100")
        rows = cur.fetchall()
        conn.close()

        if query:
            rows = [r for r in rows if query in str(r[0]) or query in r[1].lower()]

        self.logs_table.setRowCount(len(rows))
        for i, (uid, q, ts) in enumerate(rows):
            self.logs_table.setItem(i, 0, QTableWidgetItem(str(uid)))
            item = QTableWidgetItem(q)
            item.setToolTip(q)
            self.logs_table.setItem(i, 1, item)
            self.logs_table.setItem(i, 2, QTableWidgetItem(ts))

    
    def init_users_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)

        layout.addWidget(QLabel("👥 Пользователи бота"))
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(4)
        self.users_table.setHorizontalHeaderLabels(["ID", "Имя", "Возраст", "Город"])
        self.users_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.users_table)
        self.tabs.addTab(tab, " Пользователи")

    def load_users(self):
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, name, age, city FROM users ORDER BY id DESC")
        rows = cur.fetchall()
        conn.close()
        self.users_table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                self.users_table.setItem(i, j, QTableWidgetItem(str(val) if val is not None else ""))

    
    def init_qa_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        top = QHBoxLayout()
        top.addWidget(QLabel("🔍 Поиск в базе знаний:"))
        self.search_qa = QLineEdit()
        self.search_qa.setPlaceholderText("Вопрос или ответ...")
        self.search_qa.textChanged.connect(self.load_qa)
        top.addWidget(self.search_qa)
        layout.addLayout(top)

        layout.addWidget(QLabel("💡 База вопросов и ответов"))

        self.qa_table = QTableWidget()
        self.qa_table.setColumnCount(5)
        self.qa_table.setHorizontalHeaderLabels(["Вопрос", "Ответ", "Тип", "Реакция", "Действие"])
        self.qa_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.qa_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        layout.addWidget(self.qa_table)

        self.tabs.addTab(tab, " База знаний")

    def load_qa(self):
        query = self.search_qa.text().lower()
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, question, answer, type, reaction FROM qa ORDER BY id DESC")
        rows = cur.fetchall()
        conn.close()

        if query:
            rows = [r for r in rows if query in r[1].lower() or query in r[2].lower()]

        self.qa_table.setRowCount(len(rows))
        for i, (qid, question, answer, qtype, reaction) in enumerate(rows):
            self.qa_table.setItem(i, 0, QTableWidgetItem(question))
            item = QTableWidgetItem(answer)
            item.setToolTip(answer)
            self.qa_table.setItem(i, 1, item)
            self.qa_table.setItem(i, 2, QTableWidgetItem(qtype or ""))
            self.qa_table.setItem(i, 3, QTableWidgetItem(reaction or "—"))

            edit_btn = QPushButton("Редактировать")
            edit_btn.setObjectName("editBtn")
            edit_btn.clicked.connect(lambda _, id=qid: self.edit_qa(id))
            self.qa_table.setCellWidget(i, 4, edit_btn)

    def edit_qa(self, qid):
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT question, answer FROM qa WHERE id=?", (qid,))
        row = cur.fetchone()
        conn.close()
        if not row: return

        dialog = QDialog(self)
        dialog.setWindowTitle("Редактировать запись")
        dialog.setFixedSize(700, 500)
        layout = QFormLayout(dialog)

        q_edit = QLineEdit(row[0])
        a_edit = QTextEdit(row[1])
        a_edit.setAcceptRichText(False)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(lambda: self.save_qa(qid, q_edit.text(), a_edit.toPlainText(), dialog))
        buttons.rejected.connect(dialog.reject)

        layout.addRow("Вопрос:", q_edit)
        layout.addRow("Ответ:", a_edit)
        layout.addRow(buttons)
        dialog.exec_()

    def save_qa(self, qid, question, answer, dialog):
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("UPDATE qa SET question=?, answer=? WHERE id=?", (question, answer, qid))
        conn.commit()
        conn.close()
        dialog.accept()
        self.load_qa()
        QMessageBox.information(self, "Готово", "Ответ успешно обновлён!")

    
    def init_feedback_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)

        layout.addWidget(QLabel("Отзывы и реакции пользователей"))

        self.feedback_table = QTableWidget()
        self.feedback_table.setColumnCount(5)
        self.feedback_table.setHorizontalHeaderLabels(["Вопрос", "Ответ", "User ID", "Оценка", "Время"])
        self.feedback_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.feedback_table)
        self.tabs.addTab(tab, " Отзывы")

    def load_feedback(self):
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT question, answer, user_id, liked, ts FROM feedback ORDER BY id DESC LIMIT 100")
        rows = cur.fetchall()
        conn.close()

        self.feedback_table.setRowCount(len(rows))
        for i, (q, a, uid, liked, ts) in enumerate(rows):
            self.feedback_table.setItem(i, 0, QTableWidgetItem(q))
            self.feedback_table.setItem(i, 1, QTableWidgetItem(a))
            self.feedback_table.setItem(i, 2, QTableWidgetItem(str(uid)))
            like_item = QTableWidgetItem("Отлично!" if liked else "Плохо")
            like_item.setForeground(QColor("#00ff00" if liked else "#ff0066"))
            like_item.setTextAlignment(Qt.AlignCenter)
            self.feedback_table.setItem(i, 3, like_item)
            self.feedback_table.setItem(i, 4, QTableWidgetItem(ts))

    
    def init_stats_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        layout.addWidget(QLabel("📈 Статистика бота"))

        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(2)
        self.stats_table.setHorizontalHeaderLabels(["Показатель", "Значение"])
        self.stats_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.stats_table.setRowCount(4)
        self.stats_table.setVerticalHeaderLabels(["", "", "", ""])
        self.stats_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.stats_table)

        self.tabs.addTab(tab, " Статистика")

    def update_stats(self):
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM logs"); logs = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM users"); users = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM qa"); qa = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM feedback WHERE liked=1"); likes = cur.fetchone()[0]
        conn.close()

        data = [
            ("Всего запросов", f"{logs:,}".replace(",", " ")),
            ("Пользователей", f"{users:,}".replace(",", " ")),
            ("Записей в базе", f"{qa:,}".replace(",", " ")),
            ("Положительных оценок", f"{likes:,}".replace(",", " "))
        ]
        for i, (name, val) in enumerate(data):
            self.stats_table.setItem(i, 0, QTableWidgetItem(name))
            item = QTableWidgetItem(val)
            item.setTextAlignment(Qt.AlignCenter)
            item.setForeground(QColor("#58a6ff"))
            item.setFont(QFont("Segoe UI", 16, QFont.Bold))
            self.stats_table.setItem(i, 1, item)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion") 
    window = FuturisticAdmin()
    window.show()
    sys.exit(app.exec_())