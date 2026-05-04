import tkinter as tk
from tkinter import ttk, messagebox
import random
import string
import json
import os
import datetime
import sys
import unittest

# ---------- Конфигурация ----------
HISTORY_FILE = "history.json"

# ---------- Валидация и генерация ----------
def validate_params(length, use_digits, use_letters, use_specials):
    """Возвращает (True, "") если параметры валидны, иначе (False, сообщение)"""
    if length < 1 or length > 128:
        return False, "Длина пароля должна быть от 1 до 128."
    if not (use_digits or use_letters or use_specials):
        return False, "Выберите хотя бы один тип символов."
    return True, ""

def generate_password(length, use_digits, use_letters, use_specials):
    """Генерирует пароль, гарантируя наличие хотя бы одного символа каждого выбранного типа."""
    pool = ""
    required = []
    if use_digits:
        pool += string.digits
        required.append(random.choice(string.digits))
    if use_letters:
        pool += string.ascii_letters
        required.append(random.choice(string.ascii_letters))
    if use_specials:
        specials = "!@#$%^&*()-_=+[]{}|;:,.<>?/~`"
        pool += specials
        required.append(random.choice(specials))

    remaining_length = length - len(required)
    password_chars = required + random.choices(pool, k=remaining_length)
    random.shuffle(password_chars)
    return ''.join(password_chars)

# ---------- Работа с JSON ----------
def load_history():
    """Загружает историю из файла. Возвращает список словарей."""
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
    except (json.JSONDecodeError, IOError):
        pass
    return []

def save_history(history):
    """Сохраняет историю в файл."""
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def clear_history():
    """Очищает файл истории."""
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump([], f)

# ---------- Графический интерфейс ----------
class PasswordGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Random Password Generator")
        self.root.resizable(False, False)

        # Переменные
        self.length_var = tk.IntVar(value=12)
        self.digits_var = tk.BooleanVar(value=True)
        self.letters_var = tk.BooleanVar(value=True)
        self.specials_var = tk.BooleanVar(value=True)

        # История
        self.history = load_history()
        self._build_ui()
        self._populate_history_table()

    def _build_ui(self):
        # Фрейм настроек
        settings_frame = ttk.LabelFrame(self.root, text="Параметры пароля", padding=10)
        settings_frame.pack(fill="x", padx=10, pady=5)

        # Ползунок длины
        ttk.Label(settings_frame, text="Длина пароля:").grid(row=0, column=0, sticky="w")
        self.length_scale = ttk.Scale(settings_frame, from_=1, to=128,
                                      orient="horizontal", variable=self.length_var,
                                      command=self._on_scale_change)
        self.length_scale.grid(row=1, column=0, sticky="ew", padx=(0,10))
        self.length_label = ttk.Label(settings_frame, text=str(self.length_var.get()))
        self.length_label.grid(row=1, column=1, sticky="w")

        # Чекбоксы
        ttk.Checkbutton(settings_frame, text="Цифры (0-9)", variable=self.digits_var)\
            .grid(row=2, column=0, sticky="w", pady=2)
        ttk.Checkbutton(settings_frame, text="Буквы (A-Z, a-z)", variable=self.letters_var)\
            .grid(row=3, column=0, sticky="w", pady=2)
        ttk.Checkbutton(settings_frame, text="Спецсимволы (!@#$...)", variable=self.specials_var)\
            .grid(row=4, column=0, sticky="w", pady=2)

        settings_frame.columnconfigure(0, weight=1)

        # Кнопка генерации
        ttk.Button(self.root, text="Сгенерировать пароль",
                   command=self._generate).pack(pady=5)

        # Таблица истории
        history_frame = ttk.LabelFrame(self.root, text="История", padding=5)
        history_frame.pack(fill="both", expand=True, padx=10, pady=5)

        columns = ("password", "length", "digits", "letters", "specials", "datetime")
        self.tree = ttk.Treeview(history_frame, columns=columns, show="headings", height=10)
        self.tree.heading("password", text="Пароль")
        self.tree.heading("length", text="Длина")
        self.tree.heading("digits", text="Цифры")
        self.tree.heading("letters", text="Буквы")
        self.tree.heading("specials", text="Спецсимволы")
        self.tree.heading("datetime", text="Дата/Время")
        self.tree.column("password", width=200)
        self.tree.column("length", width=50, anchor="center")
        self.tree.column("digits", width=50, anchor="center")
        self.tree.column("letters", width=50, anchor="center")
        self.tree.column("specials", width=70, anchor="center")
        self.tree.column("datetime", width=130, anchor="center")

        scrollbar = ttk.Scrollbar(history_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Кнопки управления историей
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(pady=5)
        ttk.Button(btn_frame, text="Очистить историю",
                   command=self._clear_history).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Удалить выбранное",
                   command=self._delete_selected).pack(side="left", padx=5)

    def _on_scale_change(self, value):
        self.length_label.config(text=str(int(float(value))))

    def _generate(self):
        length = int(self.length_var.get())
        use_digits = self.digits_var.get()
        use_letters = self.letters_var.get()
        use_specials = self.specials_var.get()

        valid, error_msg = validate_params(length, use_digits, use_letters, use_specials)
        if not valid:
            messagebox.showerror("Ошибка", error_msg)
            return

        password = generate_password(length, use_digits, use_letters, use_specials)
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        record = {
            "password": password,
            "length": length,
            "digits": use_digits,
            "letters": use_letters,
            "specials": use_specials,
            "datetime": now
        }
        self.history.insert(0, record)
        save_history(self.history)
        self._insert_row(record, index=0)

    def _populate_history_table(self):
        for record in self.history:
            self._insert_row(record)

    def _insert_row(self, record, index=None):
        values = (
            record["password"],
            record["length"],
            "Да" if record["digits"] else "Нет",
            "Да" if record["letters"] else "Нет",
            "Да" if record["specials"] else "Нет",
            record["datetime"]
        )
        if index is not None:
            self.tree.insert("", index, values=values)
        else:
            self.tree.insert("", "end", values=values)

    def _clear_history(self):
        if messagebox.askyesno("Подтверждение", "Удалить всю историю?"):
            self.tree.delete(*self.tree.get_children())
            self.history = []
            clear_history()

    def _delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Информация", "Выберите запись для удаления.")
            return
        for item in selected:
            values = self.tree.item(item)["values"]
            self.history = [r for r in self.history
                            if not (r["password"] == values[0] and r["datetime"] == values[5])]
            self.tree.delete(item)
        save_history(self.history)

# ---------- Тесты ----------
class TestPasswordGenerator(unittest.TestCase):
    def test_generate_password_length_12_all_types(self):
        pwd = generate_password(12, True, True, True)
        self.assertEqual(len(pwd), 12)
        self.assertTrue(any(c.isdigit() for c in pwd))
        self.assertTrue(any(c.isalpha() for c in pwd))
        self.assertTrue(any(c in "!@#$%^&*()-_=+[]{}|;:,.<>?/~`" for c in pwd))

    def test_generate_only_digits(self):
        pwd = generate_password(8, True, False, False)
        self.assertEqual(len(pwd), 8)
        self.assertTrue(all(c.isdigit() for c in pwd))

    def test_generate_only_letters(self):
        pwd = generate_password(20, False, True, False)
        self.assertEqual(len(pwd), 20)
        self.assertTrue(all(c.isalpha() for c in pwd))

    def test_generate_min_length(self):
        pwd = generate_password(1, True, False, False)
        self.assertEqual(len(pwd), 1)

    def test_generate_max_length(self):
        pwd = generate_password(128, True, True, True)
        self.assertEqual(len(pwd), 128)

    def test_validate_valid_params(self):
        valid, msg = validate_params(10, True, True, False)
        self.assertTrue(valid)
        self.assertEqual(msg, "")

    def test_validate_length_zero(self):
        valid, msg = validate_params(0, True, False, False)
        self.assertFalse(valid)
        self.assertIn("от 1 до 128", msg)

    def test_validate_length_negative(self):
        valid, msg = validate_params(-5, True, True, True)
        self.assertFalse(valid)

    def test_validate_no_charset_selected(self):
        valid, msg = validate_params(10, False, False, False)
        self.assertFalse(valid)
        self.assertIn("хотя бы один тип", msg)

    def test_randomness_distinct(self):
        pwd1 = generate_password(16, True, True, True)
        pwd2 = generate_password(16, True, True, True)
        self.assertNotEqual(pwd1, pwd2)

# ---------- Точка входа ----------
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Запуск тестов при передаче аргумента 'test'
        del sys.argv[1]  # убираем, чтобы unittest не путался
        suite = unittest.TestLoader().loadTestsFromTestCase(TestPasswordGenerator)
        runner = unittest.TextTestRunner(verbosity=2)
        runner.run(suite)
    else:
        # Запуск графического интерфейса
        root = tk.Tk()
        app = PasswordGeneratorApp(root)
        root.mainloop()