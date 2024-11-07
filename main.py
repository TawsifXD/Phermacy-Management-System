import tkinter as tk
from tkinter import ttk, messagebox
from ttkthemes import ThemedTk
import tkinter.font as tkfont
import pandas as pd
from datetime import datetime
import os

# Configurable default usernames and passwords
DEFAULT_USERS = {
    "admin": "admin",
    "staff": "staff"
}

INVENTORY_FILE = "inventory.csv"
SALES_FILE = "sales.csv"


class Inventory:
    def __init__(self):
        self.load_inventory()

    def load_inventory(self):
        if os.path.exists(INVENTORY_FILE):
            self.data = pd.read_csv(INVENTORY_FILE)
        else:
            self.data = pd.DataFrame(columns=["ID", "Name", "Quantity", "Expiration Date"])

    def save_inventory(self):
        self.data.to_csv(INVENTORY_FILE, index=False)

    def add_item(self, item_id, name, quantity, expiration_date):
        # Check if item with the same ID already exists
        if item_id in self.data['ID'].values:
            return False, "An item with this ID already exists."

        # Convert the expiration_date to datetime and then back to string in YYYY-MM-DD format
        try:
            date_obj = pd.to_datetime(expiration_date).date()
            formatted_date = date_obj.strftime('%Y-%m-%d')
        except ValueError:
            return False, "Invalid date format. Use YYYY-MM-DD."

        new_item = pd.DataFrame([[item_id, name, quantity, formatted_date]], columns=self.data.columns)
        self.data = pd.concat([self.data, new_item], ignore_index=True)
        self.save_inventory()
        return True, "Item added successfully."

    def edit_item(self, item_id, quantity=None, expiration_date=None):
        item_id = str(item_id).strip()
        self.data['ID'] = self.data['ID'].astype(str).str.strip()
        
        if item_id in self.data['ID'].values:
            if quantity is not None:
                self.data.loc[self.data['ID'] == item_id, 'Quantity'] = quantity
            if expiration_date is not None:
                # Ensure the expiration date is in YYYY-MM-DD format
                try:
                    date_obj = pd.to_datetime(expiration_date).date()
                    formatted_date = date_obj.strftime('%Y-%m-%d')
                    self.data.loc[self.data['ID'] == item_id, 'Expiration Date'] = formatted_date
                except ValueError:
                    return False, "Invalid date format. Use YYYY-MM-DD."
            self.save_inventory()
            return True, "Item updated successfully."
        return False, "Item not found."

    def delete_item(self, item_id):
        self.data = self.data[self.data['ID'] != item_id]
        self.save_inventory()

    def get_inventory(self):
        return self.data

    def search_inventory(self, search_term):
        # Filter the inventory based on the search term
        filtered_data = self.data[
            self.data['ID'].astype(str).str.contains(search_term, case=False) |
            self.data['Name'].str.contains(search_term, case=False)
        ]
        return filtered_data

    def check_expirations(self):
        today = pd.Timestamp.now()
        thirty_days = pd.Timedelta(days=30)
        
        # Convert expiration dates to datetime
        self.data['Expiration Date'] = pd.to_datetime(self.data['Expiration Date'])
        
        # Filter items expiring within 30 days
        expiring_items = self.data[
            (self.data['Expiration Date'] - today) <= thirty_days
        ]
        
        return expiring_items
class Sales:
    def __init__(self):
        self.load_sales()

    def load_sales(self):
        if os.path.exists(SALES_FILE):
            self.sales_data = pd.read_csv(SALES_FILE)
        else:
            self.sales_data = pd.DataFrame(columns=["Item ID", "Item Name", "Quantity", "Date", "Time"])

    def save_sales(self):
        self.sales_data.to_csv(SALES_FILE, index=False)

    def record_sale(self, item_id, item_name, quantity):
        now = datetime.now()
        sale_date = now.strftime("%Y-%m-%d")
        sale_time = now.strftime("%H:%M:%S")
        
        # Create new sale DataFrame with explicit column names
        new_sale = pd.DataFrame({
            "Item ID": [item_id],
            "Item Name": [item_name],
            "Quantity": [quantity],
            "Date": [sale_date],
            "Time": [sale_time]
        })
        
        # Ensure columns match before concatenation
        self.sales_data = pd.concat([self.sales_data, new_sale], ignore_index=True)
        self.save_sales()

class UserManager:
    def __init__(self):
        self.users = pd.DataFrame(columns=["Username", "Password", "Role"])
        self.initialize_default_users()

    def initialize_default_users(self):
        for username, password in DEFAULT_USERS.items():
            self.add_user(username, password, "admin" if username == "admin" else "staff")

    def add_user(self, username, password, role):
        new_user = pd.DataFrame([[username, password, role]], columns=self.users.columns)
        self.users = pd.concat([self.users, new_user], ignore_index=True)

    def authenticate(self, username, password):
        user = self.users[(self.users['Username'] == username) & (self.users['Password'] == password)]
        if not user.empty:
            return user['Role'].values[0]
        else:
            return None


class PharmacyApp:
    def __init__(self, root, role):
        self.root = root
        self.role = role
        self.inventory = Inventory()
        self.sales = Sales()
        self.user_manager = UserManager()

        self.create_widgets()
        self.check_expirations()  # This will now work correctly

    def check_expirations(self):
        try:
            expiring_items = self.inventory.check_expirations()
            if not expiring_items.empty:
                message = "The following items are expiring within 30 days:\n\n"
                for _, item in expiring_items.iterrows():
                    expiry_date = item['Expiration Date'].strftime('%Y-%m-%d')
                    message += f"{item['Name']}: {expiry_date}\n"
                messagebox.showwarning("Expiring Items", message)
        except Exception as e:
            print(f"Error checking expirations: {e}")

    def create_widgets(self):
        style = ttk.Style()
        style.configure("TNotebook", background='#f0f0f0')
        style.configure("TNotebook.Tab", padding=[10, 5], font=('TkDefaultFont', 10, 'bold'))
        style.configure("Treeview", rowheight=25, font=('TkDefaultFont', 9))
        style.configure("Treeview.Heading", font=('TkDefaultFont', 10, 'bold'))

        # Create a notebook (tab) widget
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)

        # Create tabs
        self.inventory_tab = ttk.Frame(self.notebook)
        self.sales_tab = ttk.Frame(self.notebook)

        # Add tabs to notebook
        self.notebook.add(self.inventory_tab, text='Inventory')
        self.notebook.add(self.sales_tab, text='Sales')

        # Create inventory tab widgets
        self.create_inventory_widgets()

        # Create sales tab widgets
        self.create_sales_widgets()


    def create_inventory_widgets(self):
        # Create a frame to hold both sections side by side
        self.inventory_frame = ttk.Frame(self.inventory_tab, padding="10 10 10 10")
        self.inventory_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)  # Use expand=True

        # Frame for adding items
        self.add_item_frame = ttk.LabelFrame(self.inventory_frame, text="Add Item", padding="10 10 10 10")
        self.add_item_frame.grid(row=0, column=0, padx=10, pady=10, sticky=tk.NSEW)  # Place it in the first column

        ttk.Label(self.add_item_frame, text="ID").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.item_id = ttk.Entry(self.add_item_frame)
        self.item_id.grid(row=0, column=1, sticky=tk.W, pady=2)

        tk.Label(self.add_item_frame, text="Name").grid(row=1, column=0)
        self.item_name = tk.Entry(self.add_item_frame)
        self.item_name.grid(row=1, column=1)

        tk.Label(self.add_item_frame, text="Quantity").grid(row=2, column=0)
        self.item_quantity = tk.Entry(self.add_item_frame)
        self.item_quantity.grid(row=2, column=1)

        tk.Label(self.add_item_frame, text="Expiration Date").grid(row=3, column=0)
        self.item_expiration = tk.Entry(self.add_item_frame)
        self.item_expiration.grid(row=3, column=1)

        self.add_button = ttk.Button(self.add_item_frame, text="Add Item", command=self.add_item)
        self.add_button.grid(row=4, columnspan=2, pady=5)

        # Frame for searching, editing, and deleting items
        self.search_edit_frame = ttk.LabelFrame(self.inventory_frame, text="Search and Edit", padding="10 10 10 10")
        self.search_edit_frame.grid(row=0, column=1, padx=10, pady=10, sticky=tk.NSEW)  # Place it in the second column

        # Search section
        tk.Label(self.search_edit_frame, text="Search").grid(row=0, column=0)
        self.search_entry = tk.Entry(self.search_edit_frame)
        self.search_entry.grid(row=0, column=1)
        self.search_button = ttk.Button(self.search_edit_frame, text="Search", command=self.search_inventory)
        self.search_button.grid(row=0, column=2)

        # Edit and Delete section
        tk.Label(self.search_edit_frame, text="Quantity").grid(row=1, column=0)
        self.edit_quantity = tk.Entry(self.search_edit_frame)
        self.edit_quantity.grid(row=1, column=1)

        tk.Label(self.search_edit_frame, text="Expiration Date").grid(row=2, column=0)
        self.edit_expiration = tk.Entry(self.search_edit_frame)
        self.edit_expiration.grid(row=2, column=1)

        self.edit_button = ttk.Button(self.search_edit_frame, text="Edit Item", command=self.edit_item)
        self.edit_button.grid(row=3, column=0)

        self.delete_button = ttk.Button(self.search_edit_frame, text="Delete Item", command=self.delete_item)
        self.delete_button.grid(row=3, column=1)

        # Frame for inventory list
        self.inventory_list_frame = ttk.Frame(self.inventory_tab, padding="10 10 10 10")
        self.inventory_list_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)  # Use expand=True

        self.inventory_tree = ttk.Treeview(self.inventory_list_frame, columns=["ID", "Name", "Quantity", "Expiration Date"], show="headings")
        self.inventory_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)  # Use expand=True

        self.inventory_scrollbar = tk.Scrollbar(self.inventory_list_frame, orient=tk.VERTICAL, command=self.inventory_tree.yview)
        self.inventory_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.inventory_tree.configure(yscrollcommand=self.inventory_scrollbar.set)

        self.inventory_tree.heading("ID", text="ID")
        self.inventory_tree.heading("Name", text="Name")
        self.inventory_tree.heading("Quantity", text="Quantity")
        self.inventory_tree.heading("Expiration Date", text="Expiration Date")

        # Configure column widths
        self.inventory_tree.column("ID", width=50)
        self.inventory_tree.column("Name", width=150)
        self.inventory_tree.column("Quantity", width=100)
        self.inventory_tree.column("Expiration Date", width=100)

        self.update_inventory_list()

        self.inventory_tree.bind("<<TreeviewSelect>>", self.on_select)

    def create_sales_widgets(self):
        # Frame for recording sales
        self.sales_frame = ttk.LabelFrame(self.sales_tab, text="Record Sale", padding="10 10 10 10")
        self.sales_frame.pack(pady=10, padx=10, fill=tk.X)

        ttk.Label(self.sales_frame, text="Item ID").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.sales_item_id = ttk.Entry(self.sales_frame)
        self.sales_item_id.grid(row=0, column=1, sticky=tk.W, pady=2)

        ttk.Label(self.sales_frame, text="Quantity").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.sales_quantity = ttk.Entry(self.sales_frame)
        self.sales_quantity.grid(row=1, column=1, sticky=tk.W, pady=2)

        self.record_sale_button = ttk.Button(self.sales_frame, text="Record Sale", command=self.record_sale)
        self.record_sale_button.grid(row=2, column=0, columnspan=2, pady=10)

        # Frame for sales history
        self.sales_history_frame = ttk.Frame(self.sales_tab, padding="10 10 10 10")
        self.sales_history_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        # Create the Treeview widget for sales history
        self.sales_history_tree = ttk.Treeview(
            self.sales_history_frame, 
            columns=("Item ID", "Item Name", "Quantity", "Date", "Time"),
            show="headings"
        )
        self.sales_history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Add a scrollbar
        scrollbar = ttk.Scrollbar(self.sales_history_frame, orient=tk.VERTICAL, command=self.sales_history_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.sales_history_tree.configure(yscrollcommand=scrollbar.set)

        # Configure the columns
        for col in ("Item ID", "Item Name", "Quantity", "Date", "Time"):
            self.sales_history_tree.heading(col, text=col)
            self.sales_history_tree.column(col, width=100)

        # Update the sales history display
        self.update_sales_history()

    def add_item(self):
        item_id = self.item_id.get().strip()
        name = self.item_name.get().strip()
        quantity = self.item_quantity.get().strip()
        expiration_date = self.item_expiration.get().strip()

        # Check if any field is empty
        if not all([item_id, name, quantity, expiration_date]):
            messagebox.showerror("Error", "All fields must be filled!")
            return

        # Check if quantity is a valid number
        try:
            quantity = int(quantity)
            if quantity <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Quantity must be a positive integer!")
            return

        # Check if the expiration date is valid
        try:
            # Parse the date string to ensure it's a valid date
            datetime.strptime(expiration_date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Error", "Invalid expiration date format. Use YYYY-MM-DD.")
            return

        # If all checks pass, add the item
        success, message = self.inventory.add_item(item_id, name, quantity, expiration_date)
        if success:
            messagebox.showinfo("Success", message)
            self.update_inventory_list()

            # Clear the input fields
            self.item_id.delete(0, tk.END)
            self.item_name.delete(0, tk.END)
            self.item_quantity.delete(0, tk.END)
            self.item_expiration.delete(0, tk.END)
        else:
            messagebox.showerror("Error", message)

    def update_inventory_list(self, search_term=None):
        self.inventory_tree.delete(*self.inventory_tree.get_children())
        if search_term:
            inventory_data = self.inventory.search_inventory(search_term)
        else:
            inventory_data = self.inventory.get_inventory()
        for index, row in inventory_data.iterrows():
            self.inventory_tree.insert("", "end", values=list(row))

    def update_sales_history(self):
        # Clear the existing items in the tree
        for item in self.sales_history_tree.get_children():
            self.sales_history_tree.delete(item)

        # Get the sales data
        sales_data = self.sales.sales_data

        # Populate the tree with sales data
        for _, row in sales_data.iterrows():
            self.sales_history_tree.insert("", "end", values=(
                row["Item ID"],
                row["Item Name"],
                row["Quantity"],
                row["Date"],
                row["Time"]
            ))
    def on_select(self, event):
        selected_item = self.inventory_tree.selection()  # Get the selected item
        if selected_item:  # Check if an item is selected
            item = self.inventory_tree.item(selected_item[0])  # Get the item details
            if item and 'values' in item:
                self.edit_quantity.delete(0, tk.END)
                self.edit_quantity.insert(0, item['values'][2])  # Quantity
                self.edit_expiration.delete(0, tk.END)
                self.edit_expiration.insert(0, item['values'][3])  # Expiration Date

    def search_inventory(self):
        search_term = self.search_entry.get()
        self.update_inventory_list(search_term)

    def edit_item(self):
        selected_item = self.inventory_tree.selection()  # Get the selected item
        if selected_item:  # Check if an item is selected
            item_id = self.inventory_tree.item(selected_item[0])['values'][0]
            quantity = self.edit_quantity.get()
            expiration_date = self.edit_expiration.get()
            self.inventory.edit_item(item_id, quantity, expiration_date)
            messagebox.showinfo("Success", "Item edited successfully!")
            self.update_inventory_list()

    def delete_item(self):
        selected_item = self.inventory_tree.selection()  # Get the selected item
        if selected_item:  # Check if an item is selected
            item_id = self.inventory_tree.item(selected_item[0])['values'][0]
            self.inventory.delete_item(item_id)
            messagebox.showinfo("Success", "Item deleted successfully!")
            self.update_inventory_list()

    def record_sale(self):
        item_id = self.sales_item_id.get().strip()
        quantity = self.sales_quantity.get().strip()

        print(f"Attempting to record sale: Item ID: {item_id}, Quantity: {quantity}")

        # Validate inputs
        if not item_id or not quantity:
            messagebox.showerror("Error", "All fields must be filled!")
            return

        try:
            quantity = int(quantity)
            if quantity <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Quantity must be a positive integer!")
            return

        # Check if item exists in inventory
        inventory_data = self.inventory.get_inventory()

        # Convert item_id to string and strip whitespace from inventory IDs
        item_id = str(item_id).strip()
        inventory_data['ID'] = inventory_data['ID'].astype(str).str.strip()

        item = inventory_data[inventory_data['ID'] == item_id]

        if item.empty:
            messagebox.showerror("Error", f"Item ID '{item_id}' not found in inventory!")
            return

        current_quantity = int(item['Quantity'].iloc[0])
        if quantity > current_quantity:
            messagebox.showerror("Error", "Not enough stock available!")
            return

        # Update inventory quantity
        new_quantity = current_quantity - quantity
        self.inventory.edit_item(item_id, new_quantity)

        # Record the sale
        item_name = item['Name'].iloc[0]
        print(f"Recording sale with: Item ID: {item_id}, Item Name: {item_name}, Quantity: {quantity}")
        self.sales.record_sale(item_id, item_name, quantity)

        messagebox.showinfo("Success", "Sale recorded successfully!")

        # Clear input fields
        self.sales_item_id.delete(0, tk.END)
        self.sales_quantity.delete(0, tk.END)

        # Update both inventory and sales displays
        self.update_inventory_list()
        self.update_sales_history()  # Make sure this line is here

def main():
    root = ThemedTk(theme="arc")  # Use a modern theme
    root.title("Pharmacy Management System")

    # Set minimum and maximum window sizes
    root.minsize(800, 600)
    root.maxsize(1200, 800)

    # Set custom fonts
    default_font = tkfont.nametofont("TkDefaultFont")
    default_font.configure(size=10)
    root.option_add("*Font", default_font)

    # Set color scheme
    root.configure(background='#f0f0f0')

    # Create a frame for login
    login_frame = ttk.Frame(root, padding="20 20 20 20")
    login_frame.pack(fill=tk.BOTH, expand=True)

    ttk.Label(login_frame, text="Username").grid(row=0, column=0, sticky=tk.W, pady=5)
    username_entry = ttk.Entry(login_frame)
    username_entry.grid(row=0, column=1, sticky=tk.E, pady=5)

    ttk.Label(login_frame, text="Password").grid(row=1, column=0, sticky=tk.W, pady=5)
    password_entry = ttk.Entry(login_frame, show="*")
    password_entry.grid(row=1, column=1, sticky=tk.E, pady=5)

    def login():
        username = username_entry.get()
        password = password_entry.get()
        user_manager = UserManager()
        role = user_manager.authenticate(username, password)
        if role:
            # Hide the login frame and show the main application
            login_frame.pack_forget()
            app = PharmacyApp(root, role)
        else:
            messagebox.showerror("Invalid Credentials", "Invalid username or password.")

    login_button = ttk.Button(login_frame, text="Login", command=login)
    login_button.grid(row=2, column=0, columnspan=2, pady=10)

    # Create custom styles
    style = ttk.Style()
    style.configure("Accent.TButton", foreground="white", background="#007bff")

    root.mainloop()

if __name__ == "__main__":
    main()
