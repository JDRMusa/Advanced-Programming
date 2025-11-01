import csv, os, tkinter as tk
from tkinter import ttk, messagebox, simpledialog

DATA_FILE = os.path.join(os.path.dirname(__file__), "Resource Folder", "studentMarks.txt")

def load_students(path=DATA_FILE):
    students = []
    try:
        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            lines = list(reader)
            for row in lines[1:]:
                if not row: continue
                code = int(row[0]); name = row[1]
                c1, c2, c3 = map(int, row[2:5]); exam = int(row[5])
                students.append({"code": code, "name": name, "coursework": [c1, c2, c3], "exam": exam})
    except FileNotFoundError:
        pass
    return students

def save_students(students, path=DATA_FILE):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([len(students)])
        for s in students:
            writer.writerow([s["code"], s["name"]] + s["coursework"] + [s["exam"]])

def coursework_total(s): return sum(s["coursework"])
def overall_percent(s): return (coursework_total(s) + s["exam"]) / 160 * 100
def grade(p):
    if p >= 70: return "A"
    if p >= 60: return "B"
    if p >= 50: return "C"
    if p >= 40: return "D"
    return "F"

class StudentDialog(simpledialog.Dialog):
    def __init__(self, parent, title=None, student=None):
        self.student = student
        super().__init__(parent, title)

    def body(self, master):
        labels = ["Code:", "Name:", "CW1:", "CW2:", "CW3:", "Exam:"]
        self.entries = []
        for i, text in enumerate(labels):
            ttk.Label(master, text=text).grid(row=i, column=0, sticky="w")
            e = ttk.Entry(master); e.grid(row=i, column=1, padx=6, pady=2)
            self.entries.append(e)
        if self.student:
            s = self.student
            self.entries[0].insert(0, str(s["code"]))
            self.entries[1].insert(0, s["name"])
            for i in range(3):
                self.entries[2 + i].insert(0, str(s["coursework"][i]))
            self.entries[5].insert(0, str(s["exam"]))
        return self.entries[0]

    def validate(self):
        try:
            code = int(self.entries[0].get().strip())
            name = self.entries[1].get().strip()
            cws = [int(self.entries[2+i].get().strip()) for i in range(3)]
            exam = int(self.entries[5].get().strip())
            if not (1000 <= code <= 9999): raise ValueError("Code must be 1000-9999")
            for x in cws:
                if not (0 <= x <= 20): raise ValueError("Coursework 0-20")
            if not (0 <= exam <= 100): raise ValueError("Exam 0-100")
            self.result = (code, name, cws, exam)
            return True
        except Exception as e:
            messagebox.showerror("Invalid", f"Invalid input: {e}")
            return False

class App:
    def __init__(self, root):
        self.root = root
        root.title("Student Manager")
        self.students = load_students()
        self.create_ui()
        self.refresh_list()

    def create_ui(self):
        frm = ttk.Frame(self.root, padding=8); frm.pack(fill="both", expand=True)
        self.lb = tk.Listbox(frm, width=30, exportselection=False)
        # anchor listbox to the left and allow the right column to expand
        self.lb.grid(row=0, column=0, rowspan=8, sticky="nsw", padx=(0,8))
        self.lb.bind("<<ListboxSelect>>", lambda *_: self.show_selected())

        frm.columnconfigure(0, weight=0)
        frm.columnconfigure(1, weight=1)

        info = ttk.Frame(frm); info.grid(row=0, column=1, sticky="nw", padx=10)
        keys = ["Name", "Code", "Coursework total", "Exam mark", "Overall %", "Grade"]
        self.info = {}
        for i, k in enumerate(keys):
            ttk.Label(info, text=k + ":").grid(row=i, column=0, sticky="w")
            lbl = ttk.Label(info, text=""); lbl.grid(row=i, column=1, sticky="w")
            self.info[k] = lbl

        btns = [
            ("View All", self.view_all), ("Individual", self.view_individual),
            ("Highest", self.show_highest), ("Lowest", self.show_lowest),
            ("Sort", self.sort_students), ("Add", self.add_student),
            ("Edit", self.edit_student), ("Delete", self.delete_student),
            ("Save", self.save), ("Exit", self.root.quit)
        ]
        btn_frame = ttk.Frame(frm); btn_frame.grid(row=8, column=0, columnspan=2, pady=(8,0))
        max_rows = 2
        cols = (len(btns) + max_rows - 1) // max_rows
        for c in range(cols):
            btn_frame.columnconfigure(c, weight=1)
        for i, (t, cmd) in enumerate(btns):
            r = i % max_rows
            c = i // max_rows
            ttk.Button(btn_frame, text=t, command=cmd).grid(row=r, column=c, padx=3, pady=2, sticky="ew")

    def refresh_list(self):
        self.lb.delete(0, tk.END)
        for s in self.students:
            self.lb.insert(tk.END, f"{s['name']} ({s['code']})")
        self.clear_info()

    def clear_info(self):
        for v in self.info.values(): v.config(text="")

    def show_selected(self):
        sel = self.lb.curselection()
        if not sel:
            self.clear_info(); return
        s = self.students[sel[0]]
        p = overall_percent(s)
        self.info["Name"].config(text=s["name"])
        self.info["Code"].config(text=str(s["code"]))
        self.info["Coursework total"].config(text=f"{coursework_total(s)} / 60")
        self.info["Exam mark"].config(text=f"{s['exam']} / 100")
        self.info["Overall %"].config(text=f"{p:.2f}%")
        self.info["Grade"].config(text=grade(p))

    def view_all(self):
        if not self.students:
            messagebox.showinfo("Info", "No students loaded.")
            return
        win = tk.Toplevel(self.root); win.title("All Students")
        txt = tk.Text(win, width=80, height=25); txt.pack(fill="both", expand=True)
        total = 0
        for s in self.students:
            p = overall_percent(s); total += p
            txt.insert(tk.END, self.format_student(s, p) + "\n")
        avg = total / len(self.students)
        txt.insert(tk.END, f"\nTotal students: {len(self.students)}\nAverage %: {avg:.2f}%")
        txt.config(state="disabled")

    def format_student(self, s, p=None):
        if p is None: p = overall_percent(s)
        return (f"Name: {s['name']}\n"
                f"Code: {s['code']}\n"
                f"Coursework total: {coursework_total(s)} / 60\n"
                f"Exam mark: {s['exam']} / 100\n"
                f"Overall %: {p:.2f}%\n"
                f"Grade: {grade(p)}\n{'-'*40}")

    def view_individual(self):
        sel = self.lb.curselection()
        if sel:
            s = self.students[sel[0]]
        else:
            key = simpledialog.askstring("Find", "Enter student name or code:")
            if not key: return
            s = None
            for x in self.students:
                if key.isdigit() and int(key) == x["code"] or key.lower() in x["name"].lower():
                    s = x; break
            if not s:
                messagebox.showinfo("Not found", "No matching student.")
                return
        win = tk.Toplevel(self.root); win.title(f"{s['name']}")
        tk.Label(win, text=self.format_student(s), justify="left").pack(padx=8, pady=8)

    def show_highest(self):
        if not self.students: return messagebox.showinfo("Info", "No students.")
        s = max(self.students, key=lambda x: overall_percent(x))
        messagebox.showinfo("Highest", self.format_student(s))

    def show_lowest(self):
        if not self.students: return messagebox.showinfo("Info", "No students.")
        s = min(self.students, key=lambda x: overall_percent(x))
        messagebox.showinfo("Lowest", self.format_student(s))

    def sort_students(self):
        fld = simpledialog.askstring("Sort", "Sort by 'name' or 'overall' [overall]:") or "overall"
        order = simpledialog.askstring("Order", "Order 'asc' or 'desc' [asc]:") or "asc"
        rev = order.lower() == "desc"
        if fld.lower() == "name":
            self.students.sort(key=lambda x: x["name"].lower(), reverse=rev)
        else:
            self.students.sort(key=lambda x: overall_percent(x), reverse=rev)
        self.refresh_list()

    def add_student(self):
        d = StudentDialog(self.root, title="Add Student")
        if getattr(d, "result", None):
            code, name, cws, exam = d.result
            if any(s["code"] == code for s in self.students):
                messagebox.showerror("Error", "Code already exists."); return
            self.students.append({"code": code, "name": name, "coursework": cws, "exam": exam})
            self.refresh_list()

    def edit_student(self):
        sel = self.lb.curselection()
        if not sel:
            messagebox.showinfo("Edit", "Select a student first."); return
        s = self.students[sel[0]]
        d = StudentDialog(self.root, title="Edit Student", student=s)
        if getattr(d, "result", None):
            code, name, cws, exam = d.result
            if any(x["code"] == code and x is not s for x in self.students):
                messagebox.showerror("Error", "Code exists."); return
            s.update({"code": code, "name": name, "coursework": cws, "exam": exam})
            self.refresh_list()

    def delete_student(self):
        sel = self.lb.curselection()
        if not sel:
            messagebox.showinfo("Delete", "Select a student first."); return
        s = self.students[sel[0]]
        if messagebox.askyesno("Confirm", f"Delete {s['name']} ({s['code']})?"):
            del self.students[sel[0]]; self.refresh_list()

    def save(self):
        save_students(self.students)
        messagebox.showinfo("Save", "Saved successfully.")

if __name__ == "__main__":
    root = tk.Tk()
    ttk.Style().theme_use('clam')
    App(root)
    root.mainloop()
