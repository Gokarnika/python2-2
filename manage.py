import tkinter as tk
from tkinter import *
from tkinter import ttk, messagebox, filedialog
import mysql.connector
import csv
import datetime
import os
import tempfile
import platform
import subprocess

# Initialize database and tables (drop old tables if any)
def init_db():
    db = mysql.connector.connect(user="root", passwd="root", host="localhost")
    cursor = db.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS Shop")
    db.database = 'Shop'

    # Drop tables to avoid conflicts
    cursor.execute("DROP TABLE IF EXISTS sale")
    cursor.execute("DROP TABLE IF EXISTS products")

    cursor.execute("""
        CREATE TABLE products (
            date VARCHAR(10),
            prodName VARCHAR(50),
            prodPrice INT,
            category VARCHAR(20)
        )
    """)

    cursor.execute("""
        CREATE TABLE sale (
            custName VARCHAR(50),
            date VARCHAR(10),
            prodName VARCHAR(50),
            qty INT,
            price INT
        )
    """)

    db.commit()
    cursor.close()
    db.close()

# Insert default products if none exist, with extended product list
def insert_default_products():
    db = mysql.connector.connect(user="root", passwd="root", host="localhost", database="Shop")
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM products")
    count = cursor.fetchone()[0]
    if count == 0:
        default_products = [
            # Grocery
            ('2025-07-18', 'Rice', 50, 'Grocery'),
            ('2025-07-18', 'Wheat Flour', 40, 'Grocery'),
            ('2025-07-18', 'Cooking Oil', 120, 'Grocery'),
            ('2025-07-18', 'Sugar', 45, 'Grocery'),
            ('2025-07-18', 'Salt', 10, 'Grocery'),
            ('2025-07-18', 'Tea Powder', 150, 'Grocery'),
            ('2025-07-18', 'Coffee', 200, 'Grocery'),
            ('2025-07-18', 'Pulses', 70, 'Grocery'),
            # Food Items
            ('2025-07-18', 'Bread', 20, 'Food Items'),
            ('2025-07-18', 'Eggs', 5, 'Food Items'),
            ('2025-07-18', 'Milk', 30, 'Food Items'),
            ('2025-07-18', 'Butter', 60, 'Food Items'),
            ('2025-07-18', 'Cheese', 80, 'Food Items'),
            ('2025-07-18', 'Yogurt', 50, 'Food Items'),
            ('2025-07-18', 'Chicken', 180, 'Food Items'),
            ('2025-07-18', 'Fish', 220, 'Food Items'),
            # Clothes
            ('2025-07-18', 'T-Shirt', 250, 'Clothes'),
            ('2025-07-18', 'Jeans', 900, 'Clothes'),
            ('2025-07-18', 'Jacket', 1200, 'Clothes'),
            ('2025-07-18', 'Sweater', 600, 'Clothes'),
            ('2025-07-18', 'Cap', 150, 'Clothes'),
            ('2025-07-18', 'Socks', 100, 'Clothes'),
            ('2025-07-18', 'Scarf', 350, 'Clothes'),
            ('2025-07-18', 'Gloves', 200, 'Clothes'),
        ]
        cursor.executemany("INSERT INTO products (date, prodName, prodPrice, category) VALUES (%s, %s, %s, %s)", default_products)
        db.commit()
    cursor.close()
    db.close()

# Login window
def login():
    def verify():
        if user.get() == 'admin' and pwd.get() == '1234':
            login_win.destroy()
            main_window()
        else:
            messagebox.showerror("Login Failed", "Invalid Credentials")

    login_win = Tk()
    login_win.title("Shop Management")
    login_win.geometry("300x200")
    login_win.configure(bg='white')

    Label(login_win, text="Username", bg='white').pack(pady=5)
    user = Entry(login_win)
    user.pack(pady=5)

    Label(login_win, text="Password", bg='white').pack(pady=5)
    pwd = Entry(login_win, show='*')
    pwd.pack(pady=5)

    Button(login_win, text="Login", command=verify).pack(pady=20)

    login_win.mainloop()

# View Products window (no stock column)
def view_products():
    win = Toplevel()
    win.title("View Products")
    win.geometry("700x400")

    tree = ttk.Treeview(win, columns=("Date", "Name", "Price", "Category"), show='headings')
    tree.heading("Date", text="Date")
    tree.heading("Name", text="Product Name")
    tree.heading("Price", text="Price")
    tree.heading("Category", text="Category")

    db = mysql.connector.connect(user="root", passwd="root", host="localhost", database="Shop")
    cursor = db.cursor()
    cursor.execute("SELECT date, prodName, prodPrice, category FROM products ORDER BY category, prodName")
    for row in cursor.fetchall():
        tree.insert('', END, values=row)

    cursor.close()
    db.close()

    tree.pack(expand=True, fill=BOTH)

# Export sales report to CSV
def export_report():
    db = mysql.connector.connect(user="root", passwd="root", host="localhost", database="Shop")
    cursor = db.cursor()
    cursor.execute("SELECT * FROM sale")
    rows = cursor.fetchall()
    filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
    if filepath:
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([desc[0] for desc in cursor.description])
            writer.writerows(rows)
        messagebox.showinfo("Exported", f"Report saved to {filepath}")
    cursor.close()
    db.close()

# Show today's sales summary
def daily_summary():
    today = datetime.date.today().strftime('%Y-%m-%d')
    db = mysql.connector.connect(user="root", passwd="root", host="localhost", database="Shop")
    cursor = db.cursor()
    cursor.execute("SELECT SUM(price) FROM sale WHERE date = %s", (today,))
    total = cursor.fetchone()[0] or 0
    messagebox.showinfo("Today's Summary", f"Total Sales for {today}: ₹{total}")
    cursor.close()
    db.close()

# Billing system with print, save, and clear bill options
def billing():
    win = Toplevel()
    win.title("Billing")
    win.geometry("600x550")

    cart = []

    db = mysql.connector.connect(user="root", passwd="root", host="localhost", database="Shop")
    cursor = db.cursor()
    today = datetime.date.today().strftime('%Y-%m-%d')

    def add_to_cart():
        pname = product_name.get()
        try:
            qty = int(quantity.get())
            if qty <= 0:
                raise ValueError
        except:
            messagebox.showerror("Input Error", "Enter a valid quantity (positive integer)")
            return

        cursor.execute("SELECT prodPrice FROM products WHERE prodName=%s", (pname,))
        result = cursor.fetchone()

        if result:
            price = result[0]
            total_price = price * qty
            cart.append((cust_name.get(), today, pname, qty, total_price))
            display.insert(END, f"{pname} x{qty} = ₹{total_price}\n")
        else:
            messagebox.showerror("Error", "Product not found")

    def complete_sale():
        if not cart:
            messagebox.showwarning("Empty Cart", "Add products before completing sale.")
            return
        for item in cart:
            cursor.execute("INSERT INTO sale (custName, date, prodName, qty, price) VALUES (%s, %s, %s, %s, %s)", item)
        db.commit()
        messagebox.showinfo("Success", "Sale completed")
        win.destroy()

    def get_bill_text():
        bill_content = f"*** Shop Bill ***\nDate: {today}\nCustomer: {cust_name.get()}\n\n"
        bill_content += "Product\tQty\tPrice\n"
        total_amt = 0
        for _, _, pname, qty, price in cart:
            bill_content += f"{pname}\t{qty}\t₹{price}\n"
            total_amt += price
        bill_content += f"\nTotal Amount: ₹{total_amt}"
        return bill_content

    def print_bill():
        if not cart:
            messagebox.showwarning("Empty Cart", "No items in the cart to print.")
            return
        bill_text = get_bill_text()

        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt', mode='w', encoding='utf-8') as tmp_file:
            tmp_file.write(bill_text)
            temp_path = tmp_file.name

        try:
            if platform.system() == "Windows":
                os.startfile(temp_path)
            elif platform.system() == "Darwin":
                subprocess.call(["open", temp_path])
            else:
                subprocess.call(["xdg-open", temp_path])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open bill in text editor:\n{e}")

    def save_bill():
        if not cart:
            messagebox.showwarning("Empty Cart", "No items in the cart to save.")
            return
        filepath = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if not filepath:
            return
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(get_bill_text())
            messagebox.showinfo("Saved", f"Bill saved successfully at {filepath}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save bill: {e}")

    def clear_bill():
        cart.clear()
        display.delete('1.0', END)

    Label(win, text="Customer Name").pack()
    cust_name = Entry(win)
    cust_name.pack()

    Label(win, text="Product Name").pack()
    product_name = Entry(win)
    product_name.pack()

    Label(win, text="Quantity").pack()
    quantity = Entry(win)
    quantity.pack()

    Button(win, text="Add to Cart", command=add_to_cart).pack(pady=10)
    display = Text(win, height=10)
    display.pack()

    btn_frame = Frame(win)
    btn_frame.pack(pady=10)

    Button(btn_frame, text="Print Bill", command=print_bill, width=12).grid(row=0, column=0, padx=5)
    Button(btn_frame, text="Save Bill", command=save_bill, width=12).grid(row=0, column=1, padx=5)
    Button(btn_frame, text="Complete Sale", command=complete_sale, width=12).grid(row=0, column=2, padx=5)
    Button(btn_frame, text="Clear Bill", command=clear_bill, width=12).grid(row=0, column=3, padx=5)

    def on_close():
        cursor.close()
        db.close()
        win.destroy()

    win.protocol("WM_DELETE_WINDOW", on_close)

# Main window with buttons (Add Product removed)
def main_window():
    root = Tk()
    root.title("Shop Management")
    root.geometry("400x480")
    root.configure(bg='honeydew2')

    Button(root, text="View Products", width=25, height=2, command=view_products).pack(pady=15)
    Button(root, text="Billing", width=25, height=2, command=billing).pack(pady=15)
    Button(root, text="Export Sales Report", width=25, height=2, command=export_report).pack(pady=15)
    Button(root, text="Today's Sales Summary", width=25, height=2, command=daily_summary).pack(pady=15)

    root.mainloop()

# Initialize database, insert defaults and start app
init_db()
insert_default_products()
login()
