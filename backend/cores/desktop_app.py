import sys
from dataclasses import dataclass
from typing import List, Dict

from PySide6 import QtCore, QtGui, QtWidgets

from dbinit import SQLinit
from storage import SQLStorage
from settings_store import load_settings, save_settings


@dataclass
class Task:
    id: int
    description: str
    details: str
    completed: bool
    due_date: str | None
    category: str
    priority: str
    color: str | None


STRINGS = {
    "en": {
        "eyebrow": "Daily Focus",
        "title": "My Tasks",
        "subtitle": "Stay on top of work, study, and personal goals.",
        "addTask": "Add task",
        "titleLabel": "Title*",
        "titlePlaceholder": "Prepare weekly report",
        "details": "Details",
        "detailsPlaceholder": "Add notes or links...",
        "category": "Category",
        "priority": "Priority",
        "color": "Color",
        "dueDate": "Due date",
        "add": "Add task",
        "saving": "Saving...",
        "refresh": "Refresh list",
        "tasks": "Tasks",
        "itemsCount": "{count} items • {open} open",
        "all": "All",
        "open": "Open",
        "done": "Done",
        "searchPlaceholder": "Search title or details...",
        "allCategories": "All categories",
        "allPriorities": "All priorities",
        "loading": "Loading...",
        "noTasks": "No tasks yet.",
        "noDueDate": "No due date",
        "due": "Due",
        "complete": "Complete",
        "reopen": "Reopen",
        "edit": "Edit",
        "delete": "Delete",
        "save": "Save",
        "cancel": "Cancel",
        "settings": "Settings",
        "language": "Language",
    },
    "zh": {
        "eyebrow": "日常管理",
        "title": "我的任务",
        "subtitle": "更清晰地管理工作、学习与生活。",
        "addTask": "新增任务",
        "titleLabel": "标题*",
        "titlePlaceholder": "准备周报",
        "details": "详情",
        "detailsPlaceholder": "可填写备注或链接...",
        "category": "分类",
        "priority": "优先级",
        "color": "颜色",
        "dueDate": "截止日期",
        "add": "添加任务",
        "saving": "保存中...",
        "refresh": "刷新列表",
        "tasks": "任务列表",
        "itemsCount": "{count} 条 • {open} 未完成",
        "all": "全部",
        "open": "未完成",
        "done": "已完成",
        "searchPlaceholder": "搜索标题或详情...",
        "allCategories": "全部分类",
        "allPriorities": "全部优先级",
        "loading": "加载中...",
        "noTasks": "暂无任务。",
        "noDueDate": "无截止",
        "due": "截止",
        "complete": "完成",
        "reopen": "重新打开",
        "edit": "编辑",
        "delete": "删除",
        "save": "保存",
        "cancel": "取消",
        "settings": "设置",
        "language": "语言",
    },
}

CATEGORY_LABELS = {
    "en": {"work": "Work", "study": "Study", "personal": "Personal"},
    "zh": {"work": "工作", "study": "学习", "personal": "个人"},
}

PRIORITY_LABELS = {
    "en": {"high": "High", "medium": "Medium", "low": "Low"},
    "zh": {"high": "高", "medium": "中", "low": "低"},
}

PRIORITY_COLORS = {
    "high": "#ef4444",
    "medium": "#f59e0b",
    "low": "#10b981",
}


class TaskCard(QtWidgets.QFrame):
    action_triggered = QtCore.Signal(str, int)

    def __init__(self, task: Task, language: str, parent=None):
        super().__init__(parent)
        self.task = task
        self.language = language
        self.setObjectName("taskCard")
        self.setProperty("done", task.completed)
        self._build()

    def _build(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        head = QtWidgets.QHBoxLayout()
        head_left = QtWidgets.QVBoxLayout()
        task_id = QtWidgets.QLabel(f"#{self.task.id}")
        task_id.setObjectName("taskId")
        title = QtWidgets.QLabel(self.task.description)
        title.setWordWrap(True)
        title.setObjectName("taskTitle")
        head_left.addWidget(task_id)
        head_left.addWidget(title)
        head.addLayout(head_left, 1)

        tag_color = self.task.color or PRIORITY_COLORS.get(self.task.priority, "#0f766e")
        tag = QtWidgets.QLabel(self.task.priority.upper())
        tag.setObjectName("tag")
        tag.setStyleSheet(f"background: {tag_color};")
        head.addWidget(tag, 0, QtCore.Qt.AlignRight | QtCore.Qt.AlignTop)
        layout.addLayout(head)

        if self.task.details:
            details = QtWidgets.QLabel(self.task.details)
            details.setWordWrap(True)
            details.setObjectName("metaText")
            layout.addWidget(details)

        due_text = STRINGS[self.language]["noDueDate"]
        if self.task.due_date:
            due_text = f"{STRINGS[self.language]['due']}: {self.task.due_date}"
        due = QtWidgets.QLabel(due_text)
        due.setObjectName("due")
        layout.addWidget(due)

        actions = QtWidgets.QHBoxLayout()
        actions.setSpacing(10)
        if self.task.completed:
            btn_reopen = QtWidgets.QPushButton(STRINGS[self.language]["reopen"])
            btn_reopen.clicked.connect(lambda: self.action_triggered.emit("reopen", self.task.id))
            actions.addWidget(btn_reopen)
        else:
            btn_done = QtWidgets.QPushButton(STRINGS[self.language]["complete"])
            btn_done.clicked.connect(lambda: self.action_triggered.emit("done", self.task.id))
            actions.addWidget(btn_done)

        btn_edit = QtWidgets.QPushButton(STRINGS[self.language]["edit"])
        btn_edit.setProperty("ghost", True)
        btn_edit.clicked.connect(lambda: self.action_triggered.emit("edit", self.task.id))
        actions.addWidget(btn_edit)

        btn_delete = QtWidgets.QPushButton(STRINGS[self.language]["delete"])
        btn_delete.setProperty("danger", True)
        btn_delete.clicked.connect(lambda: self.action_triggered.emit("delete", self.task.id))
        actions.addWidget(btn_delete)
        actions.addStretch(1)
        layout.addLayout(actions)


class EditDialog(QtWidgets.QDialog):
    def __init__(self, task: Task, language: str, parent=None):
        super().__init__(parent)
        self.task = task
        self.language = language
        self.setWindowTitle(STRINGS[language]["edit"])
        self.setModal(True)
        self._build()

    def _build(self):
        layout = QtWidgets.QVBoxLayout(self)

        self.title_input = QtWidgets.QLineEdit(self.task.description)
        self.details_input = QtWidgets.QTextEdit(self.task.details or "")
        self.details_input.setFixedHeight(80)
        self.category = QtWidgets.QComboBox()
        self.category.addItems(["work", "study", "personal"])
        self.category.setCurrentText(self.task.category or "personal")

        self.priority = QtWidgets.QComboBox()
        self.priority.addItems(["high", "medium", "low"])
        self.priority.setCurrentText(self.task.priority or "medium")

        self.color_button = QtWidgets.QPushButton()
        self.color_button.setObjectName("colorButton")
        self.color = self.task.color or PRIORITY_COLORS.get(self.task.priority, "#0f766e")
        self._update_color_button()
        self.color_button.clicked.connect(self._pick_color)

        self.due_date = QtWidgets.QDateEdit()
        self.due_date.setCalendarPopup(True)
        if self.task.due_date:
            self.due_date.setDate(QtCore.QDate.fromString(self.task.due_date, "yyyy-MM-dd"))
        else:
            self.due_date.setDate(QtCore.QDate.currentDate())

        form = QtWidgets.QFormLayout()
        form.addRow(STRINGS[self.language]["titleLabel"], self.title_input)
        form.addRow(STRINGS[self.language]["details"], self.details_input)
        form.addRow(STRINGS[self.language]["category"], self.category)
        form.addRow(STRINGS[self.language]["priority"], self.priority)
        form.addRow(STRINGS[self.language]["color"], self.color_button)
        form.addRow(STRINGS[self.language]["dueDate"], self.due_date)
        layout.addLayout(form)

        buttons = QtWidgets.QHBoxLayout()
        btn_save = QtWidgets.QPushButton(STRINGS[self.language]["save"])
        btn_cancel = QtWidgets.QPushButton(STRINGS[self.language]["cancel"])
        btn_save.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)
        buttons.addStretch(1)
        buttons.addWidget(btn_save)
        buttons.addWidget(btn_cancel)
        layout.addLayout(buttons)

    def _pick_color(self):
        color = QtWidgets.QColorDialog.getColor(QtGui.QColor(self.color), self)
        if color.isValid():
            self.color = color.name()
            self._update_color_button()

    def _update_color_button(self):
        self.color_button.setStyleSheet(f"background: {self.color}; border-radius: 8px;")

    def get_data(self):
        return {
            "description": self.title_input.text().strip(),
            "details": self.details_input.toPlainText().strip(),
            "category": self.category.currentText(),
            "priority": self.priority.currentText(),
            "color": self.color,
            "due_date": self.due_date.date().toString("yyyy-MM-dd"),
        }


class TodoWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        SQLinit("tasks")
        self.storage = SQLStorage("tasks")
        self.language = load_settings().get("language", "en")
        if self.language not in STRINGS:
            self.language = "en"
        self.tasks: List[Task] = []
        self.status_filter = "all"
        self.category_filter = "all"
        self.priority_filter = "all"
        self.search_term = ""
        self._build_ui()
        self.load_tasks()

    def _t(self, key: str, **kwargs):
        value = STRINGS[self.language].get(key, key)
        if kwargs:
            return value.format(**kwargs)
        return value

    def _build_ui(self):
        self.setWindowTitle("TodoList")
        self.resize(1200, 900)
        self.setStyleSheet(self._stylesheet())

        central = QtWidgets.QWidget()
        central_layout = QtWidgets.QVBoxLayout(central)
        central_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)

        content = QtWidgets.QWidget()
        content_layout = QtWidgets.QVBoxLayout(content)
        content_layout.setContentsMargins(24, 24, 24, 48)
        content_layout.setSpacing(28)

        # Header
        header = QtWidgets.QHBoxLayout()
        header_left = QtWidgets.QVBoxLayout()
        self.eyebrow = QtWidgets.QLabel(self._t("eyebrow"))
        self.eyebrow.setObjectName("eyebrow")
        self.title = QtWidgets.QLabel(self._t("title"))
        self.title.setObjectName("title")
        self.subtitle = QtWidgets.QLabel(self._t("subtitle"))
        self.subtitle.setObjectName("subtitle")
        self.subtitle.setWordWrap(True)
        header_left.addWidget(self.eyebrow)
        header_left.addWidget(self.title)
        header_left.addWidget(self.subtitle)
        header.addLayout(header_left, 1)

        summary = QtWidgets.QHBoxLayout()
        self.open_card = self._summary_card(self._t("open"), "0", False)
        self.done_card = self._summary_card(self._t("done"), "0", True)
        summary.addWidget(self.open_card)
        summary.addWidget(self.done_card)
        header.addLayout(summary)
        content_layout.addLayout(header)

        # Add form panel
        add_panel = self._panel()
        add_layout = QtWidgets.QVBoxLayout(add_panel)
        add_layout.setSpacing(16)
        add_title = QtWidgets.QLabel(self._t("addTask"))
        add_title.setObjectName("panelTitle")
        add_layout.addWidget(add_title)

        self.title_input = QtWidgets.QLineEdit()
        self.title_input.setPlaceholderText(self._t("titlePlaceholder"))
        self.details_input = QtWidgets.QTextEdit()
        self.details_input.setPlaceholderText(self._t("detailsPlaceholder"))
        self.details_input.setFixedHeight(80)

        self.category_select = QtWidgets.QComboBox()
        self.category_select.addItems(["work", "study", "personal"])

        self.priority_select = QtWidgets.QComboBox()
        self.priority_select.addItems(["high", "medium", "low"])
        self.priority_select.setCurrentText("medium")

        self.color_button = QtWidgets.QPushButton()
        self.color_button.setObjectName("colorButton")
        self.color = "#0f766e"
        self._update_color_button()
        self.color_button.clicked.connect(self._pick_color)

        self.due_date = QtWidgets.QDateEdit()
        self.due_date.setCalendarPopup(True)
        self.due_date.setDate(QtCore.QDate.currentDate())

        add_layout.addWidget(self._field(self._t("titleLabel"), self.title_input))
        add_layout.addWidget(self._field(self._t("details"), self.details_input))
        row = QtWidgets.QHBoxLayout()
        row.setSpacing(14)
        row.addWidget(self._field(self._t("category"), self.category_select))
        row.addWidget(self._field(self._t("priority"), self.priority_select))
        row.addWidget(self._field(self._t("color"), self.color_button))
        row.addWidget(self._field(self._t("dueDate"), self.due_date))
        add_layout.addLayout(row)

        actions = QtWidgets.QHBoxLayout()
        self.add_button = QtWidgets.QPushButton(self._t("add"))
        self.add_button.clicked.connect(self.add_task)
        refresh = QtWidgets.QPushButton(self._t("refresh"))
        refresh.setProperty("ghost", True)
        refresh.clicked.connect(self.load_tasks)
        actions.addWidget(self.add_button)
        actions.addWidget(refresh)
        actions.addStretch(1)
        add_layout.addLayout(actions)
        content_layout.addWidget(add_panel)

        # Tasks panel
        tasks_panel = self._panel()
        tasks_layout = QtWidgets.QVBoxLayout(tasks_panel)
        header_row = QtWidgets.QHBoxLayout()
        title_box = QtWidgets.QVBoxLayout()
        self.tasks_title = QtWidgets.QLabel(self._t("tasks"))
        self.tasks_title.setObjectName("panelTitle")
        self.items_label = QtWidgets.QLabel("")
        self.items_label.setObjectName("muted")
        title_box.addWidget(self.tasks_title)
        title_box.addWidget(self.items_label)
        header_row.addLayout(title_box, 1)

        filters = QtWidgets.QHBoxLayout()
        filters.setSpacing(8)
        self.filter_all = self._filter_button(self._t("all"), "all")
        self.filter_open = self._filter_button(self._t("open"), "open")
        self.filter_done = self._filter_button(self._t("done"), "done")
        group = QtWidgets.QButtonGroup(self)
        group.setExclusive(True)
        for btn in (self.filter_all, self.filter_open, self.filter_done):
            group.addButton(btn)
            filters.addWidget(btn)
        self.filter_all.setChecked(True)
        header_row.addLayout(filters)
        tasks_layout.addLayout(header_row)

        toolbar = QtWidgets.QHBoxLayout()
        self.search_input = QtWidgets.QLineEdit()
        self.search_input.setPlaceholderText(self._t("searchPlaceholder"))
        self.search_input.textChanged.connect(self._on_filter_change)

        self.category_filter_select = QtWidgets.QComboBox()
        self.category_filter_select.addItem(self._t("allCategories"), "all")
        self.category_filter_select.addItem("work", "work")
        self.category_filter_select.addItem("study", "study")
        self.category_filter_select.addItem("personal", "personal")
        self.category_filter_select.currentIndexChanged.connect(self._on_filter_change)

        self.priority_filter_select = QtWidgets.QComboBox()
        self.priority_filter_select.addItem(self._t("allPriorities"), "all")
        self.priority_filter_select.addItem("high", "high")
        self.priority_filter_select.addItem("medium", "medium")
        self.priority_filter_select.addItem("low", "low")
        self.priority_filter_select.currentIndexChanged.connect(self._on_filter_change)

        self.loading_label = QtWidgets.QLabel(self._t("loading"))
        self.loading_label.setObjectName("pill")
        self.loading_label.setVisible(False)

        toolbar.addWidget(self.search_input, 2)
        toolbar.addWidget(self.category_filter_select, 1)
        toolbar.addWidget(self.priority_filter_select, 1)
        toolbar.addWidget(self.loading_label)
        tasks_layout.addLayout(toolbar)

        self.error_label = QtWidgets.QLabel("")
        self.error_label.setObjectName("error")
        self.error_label.setVisible(False)
        tasks_layout.addWidget(self.error_label)

        self.task_container = QtWidgets.QWidget()
        self.task_container_layout = QtWidgets.QVBoxLayout(self.task_container)
        self.task_container_layout.setSpacing(16)
        tasks_layout.addWidget(self.task_container)

        content_layout.addWidget(tasks_panel)

        scroll.setWidget(content)
        central_layout.addWidget(scroll)
        self.setCentralWidget(central)

    def _summary_card(self, label: str, value: str, muted: bool):
        frame = QtWidgets.QFrame()
        frame.setObjectName("summaryCardMuted" if muted else "summaryCard")
        layout = QtWidgets.QVBoxLayout(frame)
        layout.setContentsMargins(14, 12, 14, 12)
        title = QtWidgets.QLabel(label)
        title.setObjectName("summaryLabel")
        number = QtWidgets.QLabel(value)
        number.setObjectName("summaryValue")
        layout.addWidget(title)
        layout.addWidget(number)
        return frame

    def _panel(self):
        frame = QtWidgets.QFrame()
        frame.setObjectName("panel")
        frame.setFrameShape(QtWidgets.QFrame.NoFrame)
        return frame

    def _field(self, label: str, widget: QtWidgets.QWidget):
        box = QtWidgets.QVBoxLayout()
        box.setSpacing(6)
        lbl = QtWidgets.QLabel(label)
        lbl.setObjectName("fieldLabel")
        box.addWidget(lbl)
        box.addWidget(widget)
        container = QtWidgets.QWidget()
        container.setLayout(box)
        return container

    def _filter_button(self, label: str, value: str):
        btn = QtWidgets.QPushButton(label)
        btn.setCheckable(True)
        btn.setProperty("filterValue", value)
        btn.clicked.connect(self._on_filter_change)
        return btn

    def _on_filter_change(self):
        sender = self.sender()
        if isinstance(sender, QtWidgets.QPushButton) and sender.isCheckable():
            value = sender.property("filterValue")
            self.status_filter = value
            for btn in (self.filter_all, self.filter_open, self.filter_done):
                btn.setChecked(btn is sender)
        self.search_term = self.search_input.text().strip().lower()
        self.category_filter = self.category_filter_select.currentData() or "all"
        self.priority_filter = self.priority_filter_select.currentData() or "all"
        self.render_tasks()

    def _pick_color(self):
        color = QtWidgets.QColorDialog.getColor(QtGui.QColor(self.color), self)
        if color.isValid():
            self.color = color.name()
            self._update_color_button()

    def _update_color_button(self):
        self.color_button.setStyleSheet(f"background: {self.color}; border-radius: 10px;")

    def load_tasks(self):
        self.loading_label.setVisible(True)
        QtWidgets.QApplication.processEvents()
        try:
            tasks = self.storage.list_task_flasks() or []
            self.tasks = [Task(**task) for task in tasks]
            self.error_label.setVisible(False)
        except Exception as exc:
            self.error_label.setText(str(exc))
            self.error_label.setVisible(True)
            self.tasks = []
        finally:
            self.loading_label.setVisible(False)
        self.render_tasks()

    def add_task(self):
        description = self.title_input.text().strip()
        if not description:
            self._show_error("Description is required")
            return
        payload = {
            "description": description,
            "details": self.details_input.toPlainText().strip(),
            "due_date": self.due_date.date().toString("yyyy-MM-dd"),
            "category": self.category_select.currentText(),
            "priority": self.priority_select.currentText(),
            "color": self.color,
        }
        try:
            self.storage.add_task(payload)
            self.title_input.clear()
            self.details_input.clear()
            self.color = "#0f766e"
            self._update_color_button()
            self.load_tasks()
        except Exception as exc:
            self._show_error(str(exc))

    def _show_error(self, text: str):
        self.error_label.setText(text)
        self.error_label.setVisible(True)

    def render_tasks(self):
        for i in reversed(range(self.task_container_layout.count())):
            item = self.task_container_layout.takeAt(i)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        filtered = []
        for task in self.tasks:
            if self.status_filter == "open" and task.completed:
                continue
            if self.status_filter == "done" and not task.completed:
                continue
            if self.category_filter != "all" and task.category != self.category_filter:
                continue
            if self.priority_filter != "all" and task.priority != self.priority_filter:
                continue
            if self.search_term:
                haystack = f"{task.description} {task.details or ''}".lower()
                if self.search_term not in haystack:
                    continue
            filtered.append(task)

        completed = len([t for t in self.tasks if t.completed])
        open_count = len(self.tasks) - completed
        self.items_label.setText(self._t("itemsCount", count=len(filtered), open=open_count))
        self.open_card.findChild(QtWidgets.QLabel, "summaryValue").setText(str(open_count))
        self.done_card.findChild(QtWidgets.QLabel, "summaryValue").setText(str(completed))

        if not filtered:
            empty = QtWidgets.QLabel(self._t("noTasks"))
            empty.setObjectName("muted")
            self.task_container_layout.addWidget(empty)
            return

        grouped: Dict[str, List[Task]] = {"work": [], "study": [], "personal": []}
        for task in filtered:
            grouped.setdefault(task.category or "personal", []).append(task)

        for group, items in grouped.items():
            if not items:
                continue
            group_box = QtWidgets.QWidget()
            group_layout = QtWidgets.QVBoxLayout(group_box)
            group_layout.setSpacing(12)

            header = QtWidgets.QHBoxLayout()
            title = QtWidgets.QHBoxLayout()
            dot = QtWidgets.QLabel()
            dot.setObjectName("groupDot")
            label = QtWidgets.QLabel(CATEGORY_LABELS[self.language].get(group, group))
            label.setObjectName("groupTitle")
            title.addWidget(dot)
            title.addWidget(label)
            header.addLayout(title)
            count = QtWidgets.QLabel(str(len(items)))
            count.setObjectName("pillSubtle")
            header.addStretch(1)
            header.addWidget(count)
            group_layout.addLayout(header)

            grid = QtWidgets.QGridLayout()
            grid.setHorizontalSpacing(16)
            grid.setVerticalSpacing(16)
            columns = 2
            for idx, task in enumerate(items):
                card = TaskCard(task, self.language)
                card.action_triggered.connect(self._handle_task_action)
                row = idx // columns
                col = idx % columns
                grid.addWidget(card, row, col)
            group_layout.addLayout(grid)
            self.task_container_layout.addWidget(group_box)

    def _handle_task_action(self, action: str, task_id: int):
        if action == "done":
            self.storage.done_task(task_id)
            self.load_tasks()
        elif action == "reopen":
            self.storage.reopen_task(task_id)
            self.load_tasks()
        elif action == "delete":
            self.storage.remove_task(task_id)
            self.load_tasks()
        elif action == "edit":
            task = next((t for t in self.tasks if t.id == task_id), None)
            if not task:
                return
            dialog = EditDialog(task, self.language, self)
            if dialog.exec() == QtWidgets.QDialog.Accepted:
                data = dialog.get_data()
                if not data["description"]:
                    return
                self.storage.update_task(
                    task_id,
                    data["description"],
                    data["details"],
                    data["due_date"],
                    data["category"],
                    data["priority"],
                    data["color"],
                )
                self.load_tasks()

    def _stylesheet(self):
        return """
        QWidget {
            font-family: Inter, "Helvetica Neue", Arial, sans-serif;
            color: #0f172a;
        }
        QMainWindow {
            background: #eef2ff;
        }
        #eyebrow {
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 2px;
            color: #64748b;
            font-weight: 600;
        }
        #title {
            font-size: 32px;
            font-weight: 700;
            margin: 6px 0;
        }
        #subtitle {
            color: #4b5563;
        }
        #summaryCard {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1d4ed8, stop:1 #1e3a8a);
            border-radius: 16px;
            color: #f8fafc;
        }
        #summaryCardMuted {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 16px;
        }
        #summaryLabel {
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: rgba(248, 250, 252, 0.8);
        }
        #summaryCardMuted #summaryLabel {
            color: #64748b;
        }
        #summaryValue {
            font-size: 24px;
            font-weight: 700;
        }
        #panel {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 18px;
        }
        #panelTitle {
            font-size: 20px;
            font-weight: 700;
        }
        #fieldLabel {
            font-weight: 600;
            color: #1f2937;
        }
        QLineEdit, QTextEdit, QComboBox, QDateEdit {
            border: 1px solid #d1d5db;
            border-radius: 12px;
            padding: 10px 12px;
            background: #f8fafc;
        }
        QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QDateEdit:focus {
            border-color: #2563eb;
            box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.15);
            background: #ffffff;
        }
        QPushButton {
            border-radius: 12px;
            border: 1px solid #1d4ed8;
            padding: 10px 16px;
            font-weight: 600;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #2563eb, stop:1 #1d4ed8);
            color: #ffffff;
        }
        QPushButton:hover:!disabled {
            box-shadow: 0 12px 28px rgba(37, 99, 235, 0.2);
            transform: translateY(-1px);
        }
        QPushButton[ghost="true"] {
            background: #f1f5f9;
            color: #1e293b;
            border-color: #e2e8f0;
        }
        QPushButton[danger="true"] {
            background: #fef2f2;
            color: #b91c1c;
            border-color: #fecaca;
        }
        QPushButton[filterValue] {
            border-radius: 999px;
            border: none;
            background: transparent;
            color: #475569;
            padding: 6px 12px;
        }
        QPushButton[filterValue]:checked {
            background: #1d4ed8;
            color: #f8fafc;
        }
        #taskCard {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 16px;
        }
        #taskCard[done="true"] {
            background: #f0f9ff;
            border-color: #bae6fd;
        }
        #taskId {
            font-size: 12px;
            color: #64748b;
        }
        #metaText {
            font-size: 12px;
            color: #64748b;
        }
        #due {
            font-weight: 600;
            color: #334155;
        }
        #tag {
            color: #ffffff;
            border-radius: 999px;
            padding: 4px 10px;
            font-size: 11px;
            font-weight: 600;
        }
        #muted {
            color: #64748b;
        }
        #pill {
            background: #dbeafe;
            color: #1d4ed8;
            border-radius: 999px;
            padding: 6px 10px;
            font-weight: 700;
            font-size: 12px;
        }
        #pillSubtle {
            background: #f1f5f9;
            color: #475569;
            border-radius: 999px;
            padding: 6px 10px;
            font-weight: 700;
            font-size: 12px;
        }
        #groupDot {
            min-width: 10px;
            min-height: 10px;
            max-width: 10px;
            max-height: 10px;
            border-radius: 5px;
            background: #1d4ed8;
        }
        #error {
            background: #fef2f2;
            color: #991b1b;
            border: 1px solid #fecdd3;
            border-radius: 10px;
            padding: 10px 12px;
        }
        """


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = TodoWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
