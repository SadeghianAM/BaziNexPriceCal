import tkinter as tk
from tkinter import ttk, messagebox
import requests
import math
import threading

# تعریف ثابت‌ها
FIELD_DEFINITIONS = {
    "product_price_usd": "هزینه نهایی محصول (ارز)",
    "exchange_rate": "قیمت روز ارز (تومان)",
    "transfer_fee_toman": "کارمزد انتقال (تومان)",
    "transfer_fee_currency": "کارمزد انتقال (ارز)",
    "fixed_fee_toman": "کارمزد ثابت (تومان)",
    "fixed_fee_percentage": "کارمزد ثابت (درصد)",
}

CURRENCIES = ["USDT", "SOL", "LTC", "BCH", "TRX", "ADA", "AVAX"]
ROUNDING_OPTIONS = ["بدون گرد کردن", "هزار تومان", "ده هزار تومان"]


class PriceCalculator:
    # تعریف مجموعه فیلدهایی که نیاز به ۶ رقم اعشار دارند
    DECIMAL_FIELDS = {"product_price_usd", "transfer_fee_currency"}

    def __init__(self):
        self.fields = {}  # مقداردهی اولیه دیکشنری fields
        self.root = tk.Tk()
        self.setup_window()
        self.create_widgets()
        self.create_buttons()
        self.create_result_frame()
        self.root.mainloop()

    def setup_window(self):
        self.root.title("محاسبه گر قیمت بازینکس")
        self.root.geometry("425x600")  # افزایش ارتفاع پنجره برای جا دادن فیلد جدید
        self.root.resizable(False, False)
        try:
            self.root.iconbitmap(r".\icon\icon.ico")
        except:
            pass  # در صورتی که آیکون موجود نباشد از خطا جلوگیری می‌کند
        self.style = ttk.Style()
        self.style.configure("TLabel", font=("Vazirmatn", 12), anchor="e")
        self.style.configure("TButton", font=("Vazirmatn", 12))
        self.style.configure("Small.TLabel", font=("Vazirmatn", 10), anchor="e")

    def create_widgets(self):
        self.create_entry_fields()

    def create_entry_fields(self):
        fields_frame = ttk.Frame(self.root, padding=10)
        fields_frame.pack(fill="both", pady=10, padx=10, expand=True)

        for idx, (key, label_text) in enumerate(FIELD_DEFINITIONS.items()):
            ttk.Label(fields_frame, text=label_text).grid(
                row=idx, column=1, padx=5, pady=5, sticky="e"
            )
            entry = self.create_entry(fields_frame)
            entry.grid(row=idx, column=0, padx=5, pady=5, sticky="ew")
            entry.bind("<FocusOut>", self.format_number)
            self.fields[key] = entry

        # تنظیمات Dropdown برای انتخاب ارز
        currency_row = len(FIELD_DEFINITIONS)
        ttk.Label(fields_frame, text="انتخاب ارز").grid(
            row=currency_row, column=1, padx=5, pady=5, sticky="e"
        )
        self.currency_var = tk.StringVar(value=CURRENCIES[0])
        self.currency_dropdown = ttk.Combobox(
            fields_frame,
            textvariable=self.currency_var,
            state="readonly",
            values=CURRENCIES,
            font=("Vazirmatn", 12),
        )
        self.currency_dropdown.grid(
            row=currency_row, column=0, padx=5, pady=5, sticky="ew"
        )

        # تنظیمات Dropdown برای گرد کردن
        rounding_row = currency_row + 1
        ttk.Label(fields_frame, text="گرد کردن").grid(
            row=rounding_row, column=1, padx=5, pady=5, sticky="e"
        )
        self.rounding_option = tk.StringVar(value=ROUNDING_OPTIONS[0])
        self.rounding_combobox = ttk.Combobox(
            fields_frame,
            textvariable=self.rounding_option,
            state="readonly",
            values=ROUNDING_OPTIONS,
            justify="right",
            font=("Vazirmatn", 12),
        )
        self.rounding_combobox.current(0)
        self.rounding_combobox.grid(
            row=rounding_row, column=0, padx=5, pady=5, sticky="ew"
        )

    def create_entry(self, parent):
        entry = tk.Entry(
            parent,
            font=("Vazirmatn", 12),
            relief="flat",
            borderwidth=0,
            highlightthickness=1,
            highlightbackground="#cccccc",
            highlightcolor="#333333",
        )
        return entry

    def create_buttons(self):
        button_frame = ttk.Frame(self.root, padding=10)
        button_frame.pack(pady=10, padx=10, fill="x", expand=True)

        # استفاده از pack برای قرارگیری دکمه‌ها به صورت افقی و با عرض مساوی
        ttk.Button(
            button_frame, text="محاسبه", command=self.calculate_final_price
        ).pack(side="left", expand=True, fill="x", padx=5, pady=5)

        ttk.Button(
            button_frame,
            width=15,
            text="دریافت قیمت ارز",
            command=self.fetch_dollar_price_thread,
        ).pack(side="left", expand=True, fill="x", padx=5, pady=5)

        ttk.Button(button_frame, text="پاک کردن", command=self.clear_fields).pack(
            side="left", expand=True, fill="x", padx=5, pady=5
        )

    def create_result_frame(self):
        self.result_frame = ttk.Frame(
            self.root, padding=20, borderwidth=2, relief="solid"
        )
        self.result_frame.pack(pady=10, padx=10, fill="both", expand=True)

        self.result_label = ttk.Label(
            self.result_frame,
            text="",
            font=("Vazirmatn", 16),
            anchor="center",
            justify="center",
        )
        self.result_label.pack(fill="both", expand=True)

        copyright_label = ttk.Label(
            self.result_frame,
            text="©2025 BaziNex Inc.",
            font=("Vazirmatn", 10),
            foreground="gray",
            anchor="center",
        )
        copyright_label.pack()

    def fetch_dollar_price_thread(self):
        thread = threading.Thread(target=self.fetch_dollar_price, daemon=True)
        thread.start()

    def fetch_dollar_price(self):
        try:
            selected_currency = self.currency_var.get()
            headers = {"Accept": "application/json", "User-Agent": "Mozilla/5.0"}
            response = requests.get(
                "https://api.bitpin.ir/api/v1/mkt/tickers/", headers=headers, timeout=15
            )
            response.raise_for_status()
            markets = response.json()

            selected_market = next(
                (
                    item
                    for item in markets
                    if item.get("symbol") == f"{selected_currency}_IRT"
                ),
                None,
            )
            if selected_market:
                currency_price = float(selected_market["price"])
                # استفاده از self.root.after برای به‌روزرسانی GUI در رشته اصلی
                self.root.after(
                    0, lambda: self.set_entry_value("exchange_rate", currency_price)
                )
            else:
                raise ValueError(f"بازار {selected_currency}/IRT یافت نشد")
        except Exception as e:
            # نمایش پیغام خطا در رشته اصلی
            self.root.after(
                0,
                lambda: messagebox.showerror(
                    "خطا", f"خطا در دریافت قیمت {selected_currency}: {str(e)}"
                ),
            )

    def set_entry_value(self, field_key, value):
        entry = self.fields.get(field_key)
        if entry:
            entry.delete(0, tk.END)
            if field_key in self.DECIMAL_FIELDS:
                formatted_value = f"{value:,.6f}"
            else:
                if isinstance(value, float):
                    if value.is_integer():
                        formatted_value = f"{int(value):,}"
                    else:
                        formatted_value = f"{value:,.2f}"
                else:
                    formatted_value = f"{value:,}"
            entry.insert(0, formatted_value)

    def format_number(self, event):
        widget = event.widget
        value = widget.get().replace(",", "")
        if value:
            try:
                if any(widget == self.fields[field] for field in self.DECIMAL_FIELDS):
                    formatted_value = f"{float(value):,.6f}"
                else:
                    number = float(value)
                    if number.is_integer():
                        formatted_value = f"{int(number):,}"
                    else:
                        formatted_value = f"{number:,.2f}"
                widget.delete(0, tk.END)
                widget.insert(0, formatted_value)
            except ValueError:
                messagebox.showerror("خطا", "لطفا عدد وارد کنید")
                widget.focus_set()

    def calculate_final_price(self):
        try:
            # دریافت مقادیر ورودی
            product_price_usd = self.get_value("product_price_usd", is_decimal=True)
            exchange_rate = self.get_value("exchange_rate")
            transfer_fee_toman = self.get_value("transfer_fee_toman")
            transfer_fee_currency = self.get_value(
                "transfer_fee_currency", default=0, is_decimal=True
            )
            fixed_fee_toman = self.get_value("fixed_fee_toman")
            fixed_fee_percentage = self.get_value("fixed_fee_percentage")

            # اعتبارسنجی مقادیر
            if product_price_usd <= 0 or exchange_rate <= 0:
                raise ValueError("قیمت محصول یا قیمت ارز نمی‌تواند صفر یا منفی باشد.")

            # محاسبات
            base_price = product_price_usd * exchange_rate
            seller_fee_total = fixed_fee_toman + (
                base_price * fixed_fee_percentage / 100
            )

            # محاسبه کارمزد انتقال در ارز و تبدیل به تومان
            transfer_fee_currency_toman = transfer_fee_currency * exchange_rate

            final_price = (
                base_price
                + transfer_fee_toman
                + transfer_fee_currency_toman
                + seller_fee_total
            )

            # اعمال گرد کردن
            rounding = self.rounding_option.get()
            if rounding == "هزار تومان":
                final_price = math.ceil(final_price / 1000) * 1000
            elif rounding == "ده هزار تومان":
                final_price = math.ceil(final_price / 10000) * 10000

            # نمایش نتیجه
            self.result_label.config(
                text=f"قیمت نهایی : {int(final_price):,} تومان", foreground="red"
            )
        except ValueError as e:
            messagebox.showerror("خطا", f"خطا: {str(e)}")

    def get_value(self, field_key, default=0, is_decimal=False):
        value_str = self.fields.get(field_key).get().replace(",", "")
        try:
            value = float(value_str) if value_str else default
            return value
        except ValueError:
            messagebox.showerror(
                "خطا",
                f"لطفا عدد معتبر در فیلد '{FIELD_DEFINITIONS.get(field_key, field_key)}' وارد کنید.",
            )
            raise

    def clear_fields(self):
        for entry in self.fields.values():
            entry.delete(0, tk.END)
        self.result_label.config(text="")
        # بازنشانی گزینه کارمزد انتقال به حالت پیش‌فرض (در صورتی که تغییراتی اضافه شده باشد)
        # اگر نیاز به بازنشانی بیشتر دارید، اینجا می‌توانید اضافه کنید


if __name__ == "__main__":
    PriceCalculator()
