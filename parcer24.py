import requests
from bs4 import BeautifulSoup
from tkinter import *
from tkinter import ttk, messagebox, filedialog
import threading
from openpyxl import Workbook
from datetime import datetime
import pyperclip
import re
import random
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class PriceTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Price Tracker Pro")
        self.root.geometry("500x450")
        self.root.resizable(width=False, height=False)

        # Настройка сессии для запросов
        self.session = self._setup_session()
        self.urls = []
        self.last_results = []

        self.load_urls()
        self.create_widgets()

    def _setup_session(self):
        """Настраивает сессию с повторными попытками"""
        session = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[403, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session

    def _generate_headers(self):
        """Генерирует случайные заголовки для запроса"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]

        return {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.google.com/',
            'DNT': '1'
        }

    def load_urls(self):
        """Загружает сохраненные URL из файла"""
        try:
            with open("product_urls.txt", "r") as url_file:
                data = url_file.read()
                self.urls = data.split()
        except FileNotFoundError:
            self.urls = []

    def create_widgets(self):
        """Создает элементы интерфейса"""
        # Основные элементы
        Label(self.root, text="Price Tracker Pro", font=('Arial', 14, 'bold')).pack(pady=10)

        # Фрейм для URL
        url_frame = Frame(self.root)
        url_frame.pack(pady=5)

        ttk.Button(url_frame, text="Добавить ссылки", command=self.add_urls_window).pack(side=LEFT, padx=5)
        ttk.Button(url_frame, text="Очистить все", command=self.clear_urls).pack(side=LEFT, padx=5)

        # Кнопка запуска
        ttk.Button(self.root, text="Запустить проверку цен", command=self.start_parsing,
                   style='Accent.TButton').pack(pady=10)

        # Прогресс бар
        self.progress = ttk.Progressbar(self.root, orient=HORIZONTAL, length=400, mode='determinate')
        self.progress.pack(pady=5)

        # Статус
        self.status_var = StringVar()
        self.status_var.set("Готов к работе")
        ttk.Label(self.root, textvariable=self.status_var).pack(pady=5)

        # Кнопки результатов
        result_frame = Frame(self.root)
        result_frame.pack(pady=10)

        ttk.Button(result_frame, text="Показать результаты", command=self.show_results).pack(side=LEFT, padx=5)
        ttk.Button(result_frame, text="Экспорт в Excel", command=self.save_to_excel).pack(side=LEFT, padx=5)

        # Стилизация
        self.root.style = ttk.Style()
        self.root.style.configure('Accent.TButton', foreground='white', background='#4CAF50')

    def add_urls_window(self):
        """Окно добавления новых URL"""
        top = Toplevel(self.root)
        top.title("Добавление ссылок")
        top.geometry("600x500")

        Label(top, text="Введите ссылки на товары (по одной на строку):").pack(pady=10)

        self.text_area = Text(top, height=20, width=70, font=('Arial', 10))
        self.text_area.pack(pady=5, padx=10)

        if self.urls:
            self.text_area.insert(END, "\n".join(self.urls))

        # Панель кнопок
        button_frame = Frame(top)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Вставить из буфера", command=self.paste_from_clipboard).pack(side=LEFT, padx=5)
        ttk.Button(button_frame, text="Очистить", command=lambda: self.text_area.delete(1.0, END)).pack(side=LEFT,
                                                                                                        padx=5)
        ttk.Button(button_frame, text="Сохранить", command=self.save_urls).pack(side=LEFT, padx=5)
        ttk.Button(button_frame, text="Отмена", command=top.destroy).pack(side=LEFT, padx=5)

    def paste_from_clipboard(self):
        """Вставка из буфера обмена"""
        try:
            text = pyperclip.paste()
            if text:
                self.text_area.insert(END, text)
                messagebox.showinfo("Успех", "Текст из буфера добавлен!")
            else:
                messagebox.showwarning("Предупреждение", "Буфер обмена пуст")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось вставить: {str(e)}")

    def clear_urls(self):
        """Очищает список URL"""
        if messagebox.askyesno("Подтверждение", "Очистить все сохраненные ссылки?"):
            self.urls = []
            try:
                with open("product_urls.txt", "w") as f:
                    f.write("")
                messagebox.showinfo("Успех", "Список ссылок очищен")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось очистить файл: {str(e)}")

    def save_urls(self):
        """Сохраняет URL в файл"""
        try:
            # Получаем текст до закрытия окна
            input_text = self.text_area.get("1.0", END).strip()
            top_window = self.text_area.master  # Запоминаем окно

            lines = [line.strip() for line in input_text.split('\n') if line.strip()]

            # Проверка URL
            valid_urls = []
            errors = []

            for i, line in enumerate(lines, 1):
                urls_in_line = re.findall(r'https?://[^\s]+', line)
                if len(urls_in_line) > 1:
                    errors.append(f"Строка {i}: Несколько URL в одной строке")
                elif not urls_in_line:
                    errors.append(f"Строка {i}: Не найден URL")
                else:
                    url = urls_in_line[0]
                    if not re.match(
                            r'^https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]*)$',
                            url):
                        errors.append(f"Строка {i}: Некорректный URL")
                    else:
                        valid_urls.append(url)

            if errors:
                messagebox.showerror("Ошибки", "Обнаружены ошибки:\n\n" + "\n".join(errors[:5]) +
                                     ("\n\n...и другие" if len(errors) > 5 else ""))
                return

            if not valid_urls:
                messagebox.showwarning("Предупреждение", "Не найдено валидных URL")
                return

            self.urls = valid_urls
            try:
                with open("product_urls.txt", "w") as f:
                    f.write(" ".join(valid_urls))
                messagebox.showinfo("Успех", f"Сохранено {len(valid_urls)} ссылок")
                top_window.destroy()  # Закрываем окно только после всех операций
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить: {str(e)}")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Неожиданная ошибка: {str(e)}")

    def start_parsing(self):
        """Запускает процесс парсинга"""
        if not self.urls:
            messagebox.showwarning("Ошибка", "Нет ссылок для проверки")
            return

        self.status_var.set("Подготовка...")
        self.progress["value"] = 0
        self.progress["maximum"] = len(self.urls)

        # Запуск в отдельном потоке
        threading.Thread(target=self.parse_prices, daemon=True).start()

    def parse_prices(self):
        """Основной метод парсинга"""
        results = []
        try:
            with open("price_results.txt", "w", encoding="utf-8") as file:
                file.write("=== Результаты проверки цен ===\n\n")

                for i, url in enumerate(self.urls, 1):
                    try:
                        self.root.after(0, lambda: self.status_var.set(f"Обработка {i}/{len(self.urls)}"))
                        self.root.after(0, lambda: self.progress.step(1))

                        # Случайная задержка
                        time.sleep(random.uniform(1, 2))

                        # Запрос с рандомными заголовками
                        response = self.session.get(url, headers=self._generate_headers(), timeout=15)
                        response.raise_for_status()

                        # Парсинг
                        product_data = self.parse_product_page(response.text, url)

                        # Запись результатов
                        if product_data["error"]:
                            file.write(f"Ошибка: {product_data['error']}\nURL: {url}\n\n")
                        else:
                            file.write(f"{product_data['name']}\n")
                            file.write(f"Цена: {product_data['price']}\n")
                            if product_data['old_price']:
                                file.write(f"Старая цена: {product_data['old_price']}\n")
                            file.write(f"URL: {url}\n\n")

                        # Сохранение для Excel
                        results.append({
                            "Название": product_data["name"],
                            "Цена": product_data["price"],
                            "Старая цена": product_data["old_price"],
                            "URL": url,
                            "Статус": "Ошибка" if product_data["error"] else "Успех"
                        })

                    except Exception as e:
                        error_msg = f"Ошибка при обработке {url}: {str(e)}"
                        file.write(f"{error_msg}\n\n")
                        results.append({
                            "Название": f"Ошибка: {str(e)}",
                            "Цена": "",
                            "Старая цена": "",
                            "URL": url,
                            "Статус": "Ошибка"
                        })

            self.last_results = results
            self.root.after(0, lambda: self.status_var.set(f"Готово! Обработано {len(self.urls)} товаров"))
            self.root.after(0, lambda: messagebox.showinfo("Готово", "Проверка цен завершена!"))

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Ошибка", f"Критическая ошибка: {str(e)}"))
            self.root.after(0, lambda: self.status_var.set("Ошибка выполнения"))

    def parse_product_page(self, html, url):
        """Парсит страницу товара с форматированием цен"""
        result = {
            "name": "Неизвестно",
            "price": "Не определена",
            "old_price": "",
            "error": ""
        }

        try:
            soup = BeautifulSoup(html, 'lxml')
            site = 'kaup24' if 'kaup24.ee' in url else 'other'

            # Название товара
            name_tag = soup.find("h1", class_="c-product__name")
            if name_tag:
                result["name"] = name_tag.get_text(strip=True)

            # Определяем теги цен в зависимости от сайта
            price_selectors = {
                "current": [
                    {"class": "c-price h-price--xx-large h-price--new"},
                    {"class": "c-price h-price--xx-large h-price"}
                ],
                "old": [
                    {"class": "c-price h-price--x-large h-price--old"}
                ]
            }

            # Текущая цена
            for selector in price_selectors["current"]:
                price_tag = soup.find("div", **selector)
                if price_tag:
                    raw_price = price_tag.get_text(strip=True)
                    result["price"] = self._format_price(raw_price)
                    break

            # Старая цена
            for selector in price_selectors["old"]:
                old_price_tag = soup.find("div", **selector)
                if old_price_tag:
                    raw_old_price = old_price_tag.get_text(strip=True)
                    result["old_price"] = self._format_price(raw_old_price)
                    break

        except Exception as e:
            result["error"] = str(e)

        return result

    def _format_price(self, price_str, site=None):  # Добавим необязательный параметр site
        """
        Форматирует цену в единый формат XX.XX€
        Принимает:
        - price_str: строка с ценой
        - site: необязательный параметр (для совместимости)
        """
        if not price_str or not isinstance(price_str, str):
            return "0.00€"

        # Удаляем все нецифровые символы, кроме запятой и точки
        cleaned = re.sub(r'[^\d,.]', '', price_str.strip())

        # Заменяем запятые на точки
        cleaned = cleaned.replace(',', '.')

        # Обработка формата без десятичных
        if '.' not in cleaned:
            if len(cleaned) < 3:
                cleaned = '0.' + cleaned.zfill(2)
            else:
                cleaned = cleaned[:-2] + '.' + cleaned[-2:]

        # Удаляем лишние точки (если их несколько)
        parts = cleaned.split('.')
        if len(parts) > 2:
            cleaned = parts[0] + '.' + ''.join(parts[1:])

        # Оставляем 2 знака после запятой
        if '.' in cleaned:
            int_part, dec_part = cleaned.split('.')
            dec_part = dec_part[:2].ljust(2, '0')
            cleaned = f"{int_part}.{dec_part}"

        # Корректируем случаи типа ".99" → "0.99"
        if cleaned.startswith('.'):
            cleaned = '0' + cleaned
        if not cleaned or cleaned == '.':
            cleaned = '0.00'

        return f"{cleaned}€"

    def show_results(self):
        """Показывает результаты в новом окне"""
        try:
            with open("price_results.txt", "r", encoding="utf-8") as f:
                content = f.read()

            top = Toplevel(self.root)
            top.title("Результаты проверки")
            top.geometry("800x600")

            # Текстовое поле с прокруткой
            text_frame = Frame(top)
            text_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)

            scrollbar = Scrollbar(text_frame)
            scrollbar.pack(side=RIGHT, fill=Y)

            text = Text(text_frame, wrap=WORD, yscrollcommand=scrollbar.set,
                        font=('Consolas', 10), padx=10, pady=10)
            text.pack(fill=BOTH, expand=True)

            text.insert(END, content)
            text.config(state=DISABLED)
            scrollbar.config(command=text.yview)

            # Кнопки
            btn_frame = Frame(top)
            btn_frame.pack(pady=10)

            ttk.Button(btn_frame, text="Сохранить как TXT", command=self.save_results).pack(side=LEFT, padx=5)
            ttk.Button(btn_frame, text="Экспорт в Excel", command=self.save_to_excel).pack(side=LEFT, padx=5)
            ttk.Button(btn_frame, text="Закрыть", command=top.destroy).pack(side=LEFT, padx=5)

        except FileNotFoundError:
            messagebox.showwarning("Ошибка", "Файл результатов не найден. Сначала запустите проверку.")

    def save_results(self):
        """Сохраняет результаты в выбранный файл"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")],
            title="Сохранить результаты"
        )

        if file_path:
            try:
                with open("price_results.txt", "r", encoding="utf-8") as src, \
                        open(file_path, "w", encoding="utf-8") as dest:
                    dest.write(src.read())
                messagebox.showinfo("Успех", "Результаты успешно сохранены!")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить: {str(e)}")

    def save_to_excel(self):
        """Экспортирует результаты в Excel"""
        if not self.last_results:
            messagebox.showwarning("Ошибка", "Нет данных для экспорта")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel файлы", "*.xlsx"), ("Все файлы", "*.*")],
            title="Экспорт в Excel"
        )

        if not file_path:
            return

        try:
            wb = Workbook()
            ws = wb.active
            ws.title = "Цены товаров"

            # Заголовки
            headers = ["Название", "Цена", "Старая цена", "URL", "Статус", "Дата проверки"]
            ws.append(headers)

            # Данные
            for item in self.last_results:
                ws.append([
                    item["Название"],
                    item["Цена"],
                    item["Старая цена"],
                    item["URL"],
                    item["Статус"],
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ])

            # Автоподбор ширины столбцов
            for col in ws.columns:
                max_length = 0
                column = col[0].column_letter
                for cell in col:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = (max_length + 2) * 1.2
                ws.column_dimensions[column].width = adjusted_width

            wb.save(file_path)
            messagebox.showinfo("Успех", f"Данные экспортированы в:\n{file_path}")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось экспортировать: {str(e)}")


if __name__ == "__main__":
    root = Tk()
    app = PriceTracker(root)
    root.mainloop()