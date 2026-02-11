import customtkinter as ctk
from tkinter import messagebox
from typing import List, Dict, Callable
import os

from ui.ui_config import center_window_adaptive


class TestSelectionWindow:
    """Окно выбора тестов"""

    def __init__(self, parent, tree_data: Dict, on_selected: Callable[[List[str]], None]):
        self.parent = parent
        self.tree_data = tree_data
        self.on_selected = on_selected
        self.selected_files = set()

        self.file_items: Dict[str, Dict] = {}
        self.folder_items: Dict[str, Dict] = {}

        self.window = ctk.CTkToplevel(parent)
        self._setup_ui()
        self._center_window(900, 700)

        self.window.transient(parent)
        self.window.grab_set()

    def _setup_ui(self):
        self.window.title("Выбор тестов")

        main_frame = ctk.CTkFrame(self.window)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        title_label = ctk.CTkLabel(
            main_frame,
            text="Выберите тесты для загрузки",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=(10, 20))

        self.scrollable_frame = ctk.CTkScrollableFrame(main_frame, height=420)
        self.scrollable_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self._display_tree(self.scrollable_frame, self.tree_data)

        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", pady=15, padx=20)

        ctk.CTkButton(button_frame, text="Выбрать все", command=self._select_all, width=120, height=35).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Свернуть все", command=self._collapse_all, width=120, height=35).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Развернуть все", command=self._expand_all, width=120, height=35).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Загрузить выбранные", command=self._load_selected, width=170, height=35, fg_color="#4CAF50").pack(side="right", padx=5)
        ctk.CTkButton(button_frame, text="Отмена", command=self.window.destroy, width=120, height=35, fg_color="#9E9E9E").pack(side="right", padx=5)

    def _display_tree(self, parent_frame, node, path="", depth=0):
        for key, value in node.items():
            is_folder = isinstance(value, dict)
            item_path = os.path.join(path, key) if path else key

            item_holder = ctk.CTkFrame(parent_frame, fg_color="transparent")
            item_holder.pack(fill="x", padx=(depth * 18, 0), pady=1, anchor="w")

            row = ctk.CTkFrame(item_holder, fg_color="transparent")
            row.pack(fill="x", anchor="w")

            if is_folder:
                folder_var = ctk.BooleanVar(value=False)

                toggle_btn = ctk.CTkButton(
                    row,
                    text="▶",
                    width=26,
                    height=26,
                    corner_radius=6,
                    fg_color="transparent",
                    text_color=("#404040", "#c8c8c8"),
                    hover_color=("#e8e8e8", "#2f2f2f"),
                )
                toggle_btn.pack(side="left", padx=(0, 4))

                checkbox = ctk.CTkCheckBox(
                    row,
                    text=f"📁 {key}",
                    variable=folder_var,
                    command=lambda fp=item_path, v=folder_var: self._on_folder_toggle(fp, v.get()),
                    font=ctk.CTkFont(size=14),
                )
                checkbox.pack(anchor="w", side="left")

                children_container = ctk.CTkFrame(item_holder, fg_color="transparent")
                # По умолчанию папки свернуты
                expanded = False

                self.folder_items[item_path] = {
                    "var": folder_var,
                    "toggle_btn": toggle_btn,
                    "children_container": children_container,
                    "expanded": expanded,
                }

                toggle_btn.configure(command=lambda fp=item_path: self._toggle_folder(fp))

                self._display_tree(children_container, value, item_path, depth + 1)
            else:
                file_var = ctk.BooleanVar(value=False)
                checkbox = ctk.CTkCheckBox(
                    row,
                    text=f"📄 {key}",
                    variable=file_var,
                    command=lambda fid=item_path, p=value, v=file_var: self._on_file_toggle(fid, p, v.get()),
                    font=ctk.CTkFont(size=14),
                )
                checkbox.pack(anchor="w", side="left")

                self.file_items[item_path] = {"var": file_var, "path": value}

    def _toggle_folder(self, folder_path: str):
        item = self.folder_items.get(folder_path)
        if not item:
            return

        item["expanded"] = not item["expanded"]
        if item["expanded"]:
            item["toggle_btn"].configure(text="▼")
            item["children_container"].pack(fill="x", padx=0, pady=(2, 0), anchor="w")
        else:
            item["toggle_btn"].configure(text="▶")
            item["children_container"].pack_forget()

    def _expand_all(self):
        for folder_path in self.folder_items.keys():
            item = self.folder_items[folder_path]
            if not item["expanded"]:
                self._toggle_folder(folder_path)

    def _collapse_all(self):
        for folder_path in self.folder_items.keys():
            item = self.folder_items[folder_path]
            if item["expanded"]:
                self._toggle_folder(folder_path)

    def _on_folder_toggle(self, folder_name: str, selected: bool):
        prefix = f"{folder_name}{os.sep}"
        for file_id, item in self.file_items.items():
            if file_id.startswith(prefix):
                item["var"].set(selected)
                if selected:
                    self.selected_files.add(item["path"])
                else:
                    self.selected_files.discard(item["path"])

        self._update_all_folder_states()

    def _on_file_toggle(self, file_id: str, file_path: str, selected: bool):
        if selected:
            self.selected_files.add(file_path)
        else:
            self.selected_files.discard(file_path)

        self._update_parent_folder_states(file_id)

    def _update_parent_folder_states(self, file_id: str):
        parent = os.path.dirname(file_id)
        while parent:
            self._recompute_folder_state(parent)
            parent = os.path.dirname(parent)

    def _update_all_folder_states(self):
        for folder_path in sorted(self.folder_items.keys(), key=lambda x: x.count(os.sep), reverse=True):
            self._recompute_folder_state(folder_path)

    def _recompute_folder_state(self, folder_path: str):
        prefix = f"{folder_path}{os.sep}"
        children = [item for fid, item in self.file_items.items() if fid.startswith(prefix)]
        if not children:
            return

        all_selected = all(item["var"].get() for item in children)
        self.folder_items[folder_path]["var"].set(all_selected)

    def _select_all(self):
        for item in self.file_items.values():
            item['var'].set(True)
            self.selected_files.add(item['path'])
        self._update_all_folder_states()

    def _load_selected(self):
        if not self.selected_files:
            messagebox.showwarning("Внимание", "Выберите хотя бы один тест!")
            return

        self.window.destroy()
        self.on_selected(list(self.selected_files))

    def _center_window(self, width: int, height: int):
        center_window_adaptive(self.window, width, height)

    def show(self):
        self.parent.wait_window(self.window)
