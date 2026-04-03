import customtkinter as ctk
import tkinter as tk
import threading
import json
import os
import requests as req
import random
from PIL import Image, ImageTk
from io import BytesIO
from CTkListbox import CTkListbox

from api.meals import random_meal, search_meal, get_ingredients, vegetarian_meals, is_halal, is_vegan, is_keto, is_non_dairy, is_sugar_free, is_non_alcoholic_meals
from api.drinks import random_drink, search_drink, get_ingredients, random_non_alcoholic, is_vegan_drink, is_keto_drink, is_non_dairy_drink, is_sugar_free_drink

# -----------------------------
# App Setup
# -----------------------------
ctk.set_appearance_mode("dark")
root = ctk.CTk()
root.geometry("1200x750")
root.title("Meal & Drink Finder")

os.makedirs("data", exist_ok=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

BOOKMARK_FILE = os.path.join(BASE_DIR, "data", "bookmarks.json")
NOTES_FILE = os.path.join(BASE_DIR, "data", "notes.json")
AUTOSAVE_DELAY = 1000  # milliseconds

# Loading Overlay
loading_frame = ctk.CTkFrame(root, fg_color="transparent")
loading_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
loading_frame.lower()  # hide initially

loading_label = ctk.CTkLabel(
    loading_frame, 
    text="Loading...", 
    font=("Arial", 24, "bold")
)
loading_label.pack(expand=True)

def show_loading():
    loading_frame.lift()  # bring to front
    root.update()  # force redraw

def hide_loading():
    loading_frame.lower()
    root.update()

# -----------------------------
# State
# -----------------------------
autosave_job = None
current_recipe_id = None
current_item = None
current_type = None
combo_meal = None
combo_drink = None
combo_mode = None
cached_veg_meals = None

# -----------------------------
# Diet Filters
# -----------------------------
diet_vars = {
    "Halal": ctk.BooleanVar(),
    "Keto": ctk.BooleanVar(),
    "Non-Alcoholic": ctk.BooleanVar(),
    "Vegetarian": ctk.BooleanVar(),
    "Vegan": ctk.BooleanVar(),
    "Dairy-Free": ctk.BooleanVar(),
    "Sugar-Free": ctk.BooleanVar()
}

# -----------------------------
# UI Variables
# -----------------------------
title_var = tk.StringVar()
ingredients_var = tk.StringVar()
instructions_var = tk.StringVar()
search_var = tk.StringVar()

# =====================================================
# PAGE 1 — HOME
# =====================================================
home_frame = ctk.CTkFrame(root)
home_frame.pack(fill="both", expand=True)

ctk.CTkLabel(
    home_frame,
    text="The Meal and Cocktail Finder!",
    font=("Arial", 26, "bold")
).pack(pady=20)

search_entry = ctk.CTkEntry(
    home_frame,
    textvariable=search_var,
    placeholder_text="Search meals or drinks...",
    width=400
)
search_entry.pack(pady=5)

suggestions = CTkListbox(home_frame, font=("Helvetica", 14), height=100, width=500,)
suggestions.pack(pady=5)

def update_suggestions(*_):
    suggestions.delete(0, tk.END)
    query = search_var.get().strip()

    if len(query) < 2:
        return

    # --- Search meals ---
    meals = [m for m in search_meal(query) if meal_passes_filters(m)][:5]
    for meal in meals:
        suggestions.insert(
            tk.END,
            f"🍽 {meal['strMeal']}"
        )

    # --- Search drinks ---
    drinks = [d for d in search_drink(query) if drink_passes_filters(d)][:5]
    for drink in drinks:
        suggestions.insert(
            tk.END,
            f"🍹 {drink['strDrink']}"
        )

search_var.trace_add("write", update_suggestions)

def select_suggestion(event):
    if not suggestions.curselection():
        return

    value = suggestions.get(tk.ACTIVE)

    # Meal
    if value.startswith("🍽"):
        name = value.replace("🍽 ", "")
        results = search_meal(name)
        if results:
            display_item(results[0], "meal")

    # Drink
    elif value.startswith("🍹"):
        name = value.replace("🍹 ", "")
        results = search_drink(name)
        if results:
            display_item(results[0], "drink")

suggestions.bind("<<ListboxSelect>>", select_suggestion)

ctk.CTkLabel(home_frame,
    text="Filter for Random Food & Drink",
    font=("Arial", 13, "bold")
).pack(pady=5)

# -----------------------------
# Responsive diet checkboxes     (A little extra, but I want it in a row and I am still adding more diets)
# -----------------------------
MAX_CHECKBOXES_PER_ROW = 4

# Outer container that centers everything
outer_container = ctk.CTkFrame(home_frame, fg_color="transparent")
outer_container.pack(pady=15, fill="x")

# Inner container for grid
diet_container = ctk.CTkFrame(outer_container, fg_color="transparent")
diet_container.pack()  # .pack without fill centers it horizontally

# Place checkboxes in grid
for idx, (diet, var) in enumerate(diet_vars.items()):
    row = idx // MAX_CHECKBOXES_PER_ROW
    col = idx % MAX_CHECKBOXES_PER_ROW

    chk = ctk.CTkCheckBox(
        diet_container,
        text=diet,
        variable=var
    )
    chk.grid(row=row, column=col, padx=10, pady=5)

# Make columns expand evenly
for col in range(MAX_CHECKBOXES_PER_ROW):
    diet_container.grid_columnconfigure(col, weight=1)

# -----------------------------
# Action Buttons (centered & responsive)
# -----------------------------
button_container = ctk.CTkFrame(home_frame, fg_color="transparent")
button_container.pack(pady=10)

# Random Food
ctk.CTkButton(button_container, text="Random Food", command=lambda:random_food()).grid(row=0, column=0, padx=10, pady=5, sticky="ew")
# Random Drink
ctk.CTkButton(button_container, text="Random Drink", command=lambda:random_drink_btn()).grid(row=0, column=1, padx=10, pady=5, sticky="ew")
# Random Meal & Drink
ctk.CTkButton(button_container, text="Random Meal & Drink", command=lambda:random_both()).grid(row=0, column=2, padx=10, pady=5, sticky="ew")
# View Notes
ctk.CTkButton(button_container, text="📝 View Notes", command=lambda:show_notes()).grid(row=1, column=0, padx=10, pady=5, sticky="ew")
# View Bookmarks
ctk.CTkButton(button_container, text="⭐ View Bookmarks", command=lambda: (load_bookmarks(), show_bookmarks())).grid(row=1, column=1, padx=10, pady=5, sticky="ew")

# Make all columns expand evenly
for col in range(3):
    button_container.grid_columnconfigure(col, weight=1)

def schedule_autosave(event=None):
    global autosave_job

    if autosave_job:
        root.after_cancel(autosave_job)

    autosave_job = root.after(AUTOSAVE_DELAY, save_notes)

# =====================================================
# PAGE 2 — RECIPE (SPLIT LAYOUT)
# =====================================================
recipe_frame = ctk.CTkFrame(root)
recipe_frame.pack_propagate(False)

# Two-column layout
recipe_frame.grid_columnconfigure(0, weight=3)
recipe_frame.grid_columnconfigure(1, weight=1)
recipe_frame.grid_rowconfigure(0, weight=1)

# -----------------------------
# LEFT — Scrollable Recipe
# -----------------------------
recipe_scroll = ctk.CTkScrollableFrame(recipe_frame)
recipe_scroll.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

recipe_card = ctk.CTkFrame(
    recipe_scroll,
    corner_radius=20,
    fg_color=("gray90", "gray15")
)
recipe_card.pack(fill="both", expand=True, padx=20, pady=20)

toggle_btn = ctk.CTkButton(
    recipe_card,
    text="🍹 Show Drink",
    command=lambda: toggle_combo()
)
toggle_btn.pack(fill="x", padx=10, pady=5)
toggle_btn.configure(state="disabled")


image_label = ctk.CTkLabel(recipe_card, text="")
image_label.pack(pady=10)

ctk.CTkLabel(
    recipe_card,
    textvariable=title_var,
    font=("Arial", 22, "bold"),
    wraplength=600
).pack(pady=(5, 10))

ctk.CTkLabel(
    recipe_card,
    text="Ingredients",
    font=("Arial", 16, "bold")
).pack(anchor="w", padx=20)

ctk.CTkLabel(
    recipe_card,
    textvariable=ingredients_var,
    justify="left",
    wraplength=600
).pack(padx=20, pady=(0, 10))

ctk.CTkLabel(
    recipe_card,
    text="Instructions",
    font=("Arial", 16, "bold")
).pack(anchor="w", padx=20)

ctk.CTkLabel(
    recipe_card,
    textvariable=instructions_var,
    justify="left",
    wraplength=600
).pack(padx=20, pady=(0, 20))

# -----------------------------
# RIGHT — Notes & Actions
# -----------------------------
side_panel = ctk.CTkFrame(recipe_frame, width=250)
side_panel.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
side_panel.pack_propagate(False)

ctk.CTkLabel(
    side_panel,
    text="Notes",
    font=("Arial", 18, "bold")
).pack(pady=(10, 5))

notes_box = ctk.CTkTextbox(side_panel, height=300)
notes_box.bind("<KeyRelease>", schedule_autosave)
notes_box.pack(fill="both", expand=True, padx=10)

ctk.CTkButton(
    side_panel,
    text="💾 Save Notes",
    command=lambda: save_notes()
).pack(fill="x", padx=10, pady=(10, 5))

ctk.CTkButton(
    side_panel,
    text="⭐ Bookmark",
    command=lambda: save_bookmark()
).pack(fill="x", padx=10, pady=5)

ctk.CTkButton(
    side_panel,
    text="⬅ Back",
    command=lambda: show_home()
).pack(fill="x", padx=10, pady=(20, 10))

# =====================================================
# Navigation
# =====================================================
def show_home():
    hide_all_pages()
    home_frame.pack(fill="both", expand=True)

def show_recipe():
    hide_all_pages()
    recipe_frame.pack(fill="both", expand=True)
    
def show_bookmarks():
    hide_all_pages()
    bookmarks_frame.pack(fill="both", expand=True)

def show_notes():
    hide_all_pages()
    load_notes_list()
    notes_frame.pack(fill="both", expand=True)
   
def hide_all_pages():
    home_frame.pack_forget()
    recipe_frame.pack_forget()
    bookmarks_frame.pack_forget()
    notes_frame.pack_forget()

# =====================================================
# Display Logic
# =====================================================
def display_item(item, item_type):
    global current_item, current_type, current_recipe_id

    current_item = item
    current_type = item_type

    # -----------------------------
    # Set unique recipe ID
    # -----------------------------
    current_recipe_id = (
        item.get("idMeal") if item_type == "meal" else item.get("idDrink")
    )

    # -----------------------------
    # Update UI text
    # -----------------------------
    title_var.set(item["strMeal"] if item_type == "meal" else item["strDrink"])
    instructions_var.set(item["strInstructions"])
    ingredients_var.set("\n".join(get_ingredients(item)))

    # -----------------------------
    # Load image
    # -----------------------------
    img_url = item["strMealThumb"] if item_type == "meal" else item["strDrinkThumb"]
    img_data = req.get(img_url).content
    pil_img = Image.open(BytesIO(img_data))

    ctk_img = ctk.CTkImage(
        light_image=pil_img,
        dark_image=pil_img,
        size=(300, 300)
    )
    
    image_label.configure(image=ctk_img)
    image_label.image = ctk_img

    # -----------------------------
    # Load notes for this recipe
    # -----------------------------
    load_notes_list(current_recipe_id)

    # -----------------------------
    # Switch to recipe page
    # -----------------------------
    show_recipe()
    
    #------------------------------
    # Toggle button for combo
    #------------------------------
    if combo_meal and combo_drink:
        toggle_btn.configure(state="normal")
    else:
        toggle_btn.configure(state="disabled")
    
def toggle_combo():
    global combo_mode

    if not combo_meal or not combo_drink:
        return

    if combo_mode == "meal":
        combo_mode = "drink"
        display_item(combo_drink, "drink")
        toggle_btn.configure(text="🍽 Show Meal")
    else:
        combo_mode = "meal"
        display_item(combo_meal, "meal")
        toggle_btn.configure(text="🍹 Show Drink")    

# ================================
# NOTES PAGE
# ================================
notes_frame = ctk.CTkFrame(root)
notes_frame.grid_columnconfigure(0, weight=1)
notes_frame.grid_rowconfigure(1, weight=1)

# Title
ctk.CTkLabel(
    notes_frame,
    text="📝 Saved Notes",
    font=("Arial", 24, "bold")
).grid(row=0, column=0, pady=15)

# Scrollable list for notes cards
notes_scroll = ctk.CTkScrollableFrame(notes_frame)
notes_scroll.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)

# Buttons at bottom
btn_frame = ctk.CTkFrame(notes_frame, fg_color="transparent")
btn_frame.grid(row=2, column=0, pady=10)

ctk.CTkButton(
    btn_frame,
    text="⬅ Back",
    command=show_home
).pack(side="left", padx=5)

ctk.CTkButton(
    btn_frame,
    text="🗑 Delete Note",
    fg_color="red",
    command=lambda: delete_note_from_sidepanel()
).pack(side="right", padx=5)

# ================================
# Notes Functions
# ================================

def load_notes_list(recipe_id=None):
    # Clear existing widgets
    for widget in notes_scroll.winfo_children():
        widget.destroy()

    if not os.path.exists(NOTES_FILE):
        return

    try:
        with open(NOTES_FILE, "r") as f:
            notes = json.load(f)
    except json.JSONDecodeError:
        notes = []

    for index, note in enumerate(notes):
        card = ctk.CTkFrame(notes_scroll, corner_radius=12)
        card.pack(fill="x", padx=10, pady=6)

        # Highlight if this is the current recipe
        if recipe_id and note["id"] == recipe_id:
            card.configure(fg_color=("gray40", "gray20"))

        ctk.CTkLabel(
            card,
            text=note["name"],
            font=("Arial", 16, "bold")
        ).pack(anchor="w", padx=10, pady=(8, 2))

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(fill="x", padx=10, pady=(0, 8))

        ctk.CTkButton(
            btn_row,
            text="Open",
            width=80,
            command=lambda n=note: open_note_from_list(n)
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_row,
            text="Delete",
            fg_color="red",
            width=80,
            command=lambda i=index: delete_note_by_index(i)
        ).pack(side="right", padx=5)

def open_note_from_list(note):
    # Open a note in the side panel (recipe + text)
    global current_item, current_type, combo_meal, combo_drink, combo_mode

    current_type = note["type"]
    current_item = note.get("data")

    if not current_item:
        print("Recipe not found")
        return

    # Reset combo unless stored
    combo_data = note.get("combo")
    if combo_data:
        combo_meal = combo_data.get("meal")
        combo_drink = combo_data.get("drink")
        combo_mode = current_type
        toggle_btn.configure(state="normal")
    else:
        combo_meal = combo_drink = None
        combo_mode = None
        toggle_btn.configure(state="disabled")

    # Display recipe in main side panel
    display_item(current_item, current_type)

    # Fill notes box
    notes_box.delete("1.0", "end")
    notes_box.insert("1.0", note["text"])
    show_recipe()

def delete_note_by_index(idx):
    # Delete note by index in notes list
    if not os.path.exists(NOTES_FILE):
        return

    try:
        with open(NOTES_FILE, "r") as f:
            notes = json.load(f)
    except json.JSONDecodeError:
        notes = []

    if idx < len(notes):
        notes.pop(idx)

    with open(NOTES_FILE, "w") as f:
        json.dump(notes, f, indent=2)

    load_notes_list()

def delete_note_from_sidepanel():
    # Delete currently opened note from notes box
    if not current_item:
        return

    note_id = get_item_id(current_item, current_type)

    if not os.path.exists(NOTES_FILE):
        return

    try:
        with open(NOTES_FILE, "r") as f:
            notes = json.load(f)
    except json.JSONDecodeError:
        notes = []

    notes = [n for n in notes if n["id"] != note_id]

    with open(NOTES_FILE, "w") as f:
        json.dump(notes, f, indent=2)

    # Clear side panel and reload notes list
    notes_box.delete("1.0", "end")
    load_notes_list()

def save_notes(event=None):
    """Save current note (recipe + text)"""
    if not current_item:
        return

    note_text = notes_box.get("1.0", "end").strip()
    if not note_text:
        return

    note_id = get_item_id(current_item, current_type)

    notes = []
    if os.path.exists(NOTES_FILE):
        try:
            with open(NOTES_FILE, "r") as f:
                notes = json.load(f)
        except json.JSONDecodeError:
            notes = []

    # Update existing note
    for note in notes:
        if note["id"] == note_id:
            note["text"] = note_text
            note["data"] = current_item
            break
    else:
        # Add new note
        notes.append({
            "id": note_id,
            "type": current_type,
            "name": title_var.get(),
            "text": note_text,
            "data": current_item
        })

    with open(NOTES_FILE, "w") as f:
        json.dump(notes, f, indent=2)

    load_notes_list()

# =====================================================
# Bookmarks
# =====================================================

bookmarks_frame = ctk.CTkFrame(root)

bookmarks_frame.grid_columnconfigure(0, weight=1)
bookmarks_frame.grid_rowconfigure(1, weight=1)

ctk.CTkLabel(
    bookmarks_frame,
    text="⭐ Bookmarks",
    font=("Arial", 24, "bold")
).grid(row=0, column=0, pady=15)

bookmark_scroll = ctk.CTkScrollableFrame(bookmarks_frame)
bookmark_scroll.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)

ctk.CTkButton(
    bookmarks_frame,
    text="⬅ Back",
    command=lambda: show_home()
).grid(row=2, column=0, pady=10)

def get_item_id(item, item_type):
    return item.get("idMeal") if item_type == "meal" else item.get("idDrink")

def save_bookmark():
    if not current_item:
        return

    current_id = get_item_id(current_item, current_type)

    bookmarks = []
    if os.path.exists(BOOKMARK_FILE):
        try:
            with open(BOOKMARK_FILE, "r") as f:
                bookmarks = json.load(f)
        except json.JSONDecodeError:
            bookmarks = []

    # -----------------------------
    # Prevent duplicates
    # -----------------------------
    for bm in bookmarks:
        bm_id = get_item_id(bm["data"], bm["type"])
        if bm_id == current_id:
            print("Bookmark already exists")
            return  # already saved

    # -----------------------------
    # Save new bookmark
    # -----------------------------
    bookmarks.append({
        "type": current_type,
        "name": title_var.get(),
        "data": current_item
    })

    with open(BOOKMARK_FILE, "w") as f:
        json.dump(bookmarks, f, indent=2)

    load_bookmarks()

def load_bookmarks():
    for widget in bookmark_scroll.winfo_children():
        widget.destroy()

    if not os.path.exists(BOOKMARK_FILE):
        return

    with open(BOOKMARK_FILE, "r") as f:
        bookmarks = json.load(f)

    for index, bm in enumerate(bookmarks):
        card = ctk.CTkFrame(bookmark_scroll, corner_radius=12)
        card.pack(fill="x", padx=10, pady=6)

        ctk.CTkLabel(
            card,
            text=bm["name"],
            font=("Arial", 16, "bold")
        ).pack(anchor="w", padx=10, pady=(8, 2))

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(fill="x", padx=10, pady=(0, 8))

        ctk.CTkButton(
            btn_row,
            text="Open",
            width=80,
            command=lambda b=bm: display_item(b["data"], b["type"])
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_row,
            text="Delete",
            fg_color="red",
            width=80,
            command=lambda i=index: delete_bookmark(i)
        ).pack(side="right", padx=5)

def delete_bookmark(index):
    with open(BOOKMARK_FILE, "r") as f:
        bookmarks = json.load(f)

    bookmarks.pop(index)

    with open(BOOKMARK_FILE, "w") as f:
        json.dump(bookmarks, f, indent=2)

    load_bookmarks()

# =====================================================
# Random Fetching
# =====================================================
def meal_passes_filters(meal):
    if diet_vars["Halal"].get() and not is_halal(meal):
        return False
    if diet_vars["Keto"].get() and not is_keto(meal):
        return False
    if diet_vars["Vegetarian"].get() and not vegetarian_meals(meal):
        return False
    if diet_vars["Vegan"].get() and not is_vegan(meal):
        return False
    if diet_vars["Dairy-Free"].get() and not is_non_dairy(meal):
        return False
    if diet_vars["Sugar-Free"].get() and not is_sugar_free(meal):
        return False
    if diet_vars["Non-Alcoholic"].get() and not is_non_alcoholic_meals(meal):
        return False
    return True

def drink_passes_filters(drink):
    if diet_vars["Keto"].get() and not is_keto_drink(drink):
        return False
    if diet_vars["Vegan"].get() and not is_vegan_drink(drink):
        return False
    if diet_vars["Dairy-Free"].get() and not is_non_dairy_drink(drink):
        return False
    if diet_vars["Sugar-Free"].get() and not is_sugar_free_drink(drink):
        return False
    return True

def random_food():
    def task():
        meal = None
        # --- Vegetarian option ---
        if diet_vars.get("Vegetarian") and diet_vars["Vegetarian"].get():
            global cached_veg_meals
            if cached_veg_meals is None:
                cached_veg_meals = vegetarian_meals()  # Fetch once

            veg_meals = cached_veg_meals
            if veg_meals:
                # Pick until it passes other filters
                while True:
                    meal = random.choice(veg_meals)
                    if meal_passes_filters(meal):
                        break
        else:
            # Pick normal random meal until it passes filters
            while True:
                meal = random_meal()
                if meal and meal_passes_filters(meal):
                    break

        root.after(0, lambda: display_item(meal, "meal"))
        root.after(0, hide_loading)  # Hide overlay when done

    show_loading()  # Show overlay immediately
    threading.Thread(target=task, daemon=True).start()
    
def random_drink_btn():
    def task():
        while True:
            drink = (
                random_non_alcoholic()
                if diet_vars["Non-Alcoholic"].get()
                else random_drink()
            )
            if drink_passes_filters(drink):
                root.after(0, display_item, drink, "drink")
                break
        
        root.after(0, hide_loading)  # Hide overlay when done

    show_loading()  # Show overlay immediately
    threading.Thread(target=task, daemon=True).start()
    
def random_both():
    def task():
        # --- For Meal ---
        meal = None
        if diet_vars["Vegetarian"].get():
            # Use cached vegetarian meals if available
            global cached_veg_meals
            if cached_veg_meals is None:
                cached_veg_meals = vegetarian_meals()
            veg_meals = cached_veg_meals

            if veg_meals:
                while True:
                    meal = random.choice(veg_meals)
                    if meal_passes_filters(meal):
                        break
        else:
            # Pick normal random meal until it passes filters
            while True:
                meal = random_meal()
                if meal and meal_passes_filters(meal):
                    break

        # --- For Drink ---
        drink = (
            random_non_alcoholic()
            if diet_vars["Non-Alcoholic"].get()
            else random_drink()
        )

        # Show Combo
        def show_combo():
            global combo_meal, combo_drink, combo_mode
            combo_meal = meal
            combo_drink = drink
            combo_mode = "meal"
            display_item(combo_meal, "meal")
            toggle_btn.configure(text="🍹 Show Drink")

        root.after(0, show_combo)
        root.after(0, hide_loading)  # Hide overlay when done

    show_loading()  # Show overlay immediately
    threading.Thread(target=task, daemon=True).start()

# -----------------------------
root.mainloop()
