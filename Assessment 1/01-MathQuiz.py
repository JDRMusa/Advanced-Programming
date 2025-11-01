import tkinter as tk
from tkinter import messagebox
import random

# Placeholder as it's outside the function currently
app = None

# Function for the menu difficulty
def displayMenu():
   app.show_menu()

def randomInt(minv, maxv):
   return random.randint(minv, maxv)

def decideOperation():
   return random.choice(['+', '-'])

def displayProblem(a, b, op):
   app.show_problem(a, b, op)

def isCorrect(userAnswer, correctAnswer):
   return userAnswer == correctAnswer

def displayResults(score):
   app.show_results(score)

class QuizApp:
   def __init__(self, root):
      self.root = root
      root.title("Math Quiz!")
      self.minv = 0
      self.maxv = 9
      self.total_questions = 10

      #Default States
      self.current_q_no = 0
      self.score = 0
      self.attempt = 1
      self.current_answer = 0

      #Frames
      self.menu_frame = tk.Frame(root)
      self.quiz_frame = tk.Frame(root)
      self.result_frame = tk.Frame(root)
      self.build_menu()
      self.build_quiz()
      self.build_result()

      #Sets the app as global so it loads properly in the end
      global app
      app = self

      #Shows the menu
      self.show_menu()

   def build_menu(self):
      f = self.menu_frame
      tk.Label(f, text="DIFFICULTY LEVEL", font=('Arial', 16)).pack(pady=10)
      self.diff_var = tk.IntVar(value=1)
      tk.Radiobutton(f, text="1. Easy (single digit)", variable=self.diff_var, value=1).pack(anchor='w')
      tk.Radiobutton(f, text="2. Moderate (double digit)", variable=self.diff_var, value=2).pack(anchor='w')
      tk.Radiobutton(f, text="3. Advanced (4-digit)", variable=self.diff_var, value=3).pack(anchor='w')
      tk.Button(f, text="Start Quiz", command=self.start_quiz).pack(pady=10)
      tk.Button(f, text="Quit", command=self.root.quit).pack()

   def build_quiz(self):
      f = self.quiz_frame
      self.question_label = tk.Label(f, text="", font=('Arial', 18))
      self.question_label.pack(pady=10)
      self.entry = tk.Entry(f, font=('Arial', 14))
      self.entry.pack()
      self.entry.bind("<Return>", lambda e: self.submit_answer())
      self.submit_btn = tk.Button(f, text="Submit", command=self.submit_answer)
      self.submit_btn.pack(pady=5)
      self.feedback_label = tk.Label(f, text="", font=('Arial', 12))
      self.feedback_label.pack(pady=5)
      self.progress_label = tk.Label(f, text="")
      self.progress_label.pack(pady=5)

   def build_result(self):
      f = self.result_frame
      self.result_label = tk.Label(f, text="", font=('Arial', 16))
      self.result_label.pack(pady=10)
      self.rank_label = tk.Label(f, text="", font=('Arial', 14))
      self.rank_label.pack(pady=5)
      tk.Button(f, text="Play Again", command=self.play_again).pack(side='left', padx=10, pady=10)
      tk.Button(f, text="Quit", command=self.root.quit).pack(side='right', padx=10, pady=10)

   #User Interface
   def show_menu(self):
      self.hide_all()
      self.menu_frame.pack(padx=20, pady=20)

   def show_problem(self, a, b, op):
      self.hide_all()
      self.quiz_frame.pack(padx=20, pady=20)
      self.question_label.config(text=f"{a} {op} {b} =")
      self.entry.delete(0, tk.END)
      self.feedback_label.config(text="")
      self.progress_label.config(text=f"Question {self.current_q_no+1} of {self.total_questions}    Score: {self.score}")
      self.entry.focus_set()

   def show_results(self, score):
      self.hide_all()
      self.result_frame.pack(padx=20, pady=20)
      self.result_label.config(text=f"Final Score: {score} / {self.total_questions*10}")
      rank = self.grade(score)
      self.rank_label.config(text=f"Rank: {rank}")

   def hide_all(self):
      for f in (self.menu_frame, self.quiz_frame, self.result_frame):
         f.pack_forget()

   #Difficulty control
   def start_quiz(self):
      diff = self.diff_var.get()
      if diff == 1:
         self.minv, self.maxv = 0, 9
      elif diff == 2:
         self.minv, self.maxv = 10, 99
      else:
         self.minv, self.maxv = 1000, 9999
      self.current_q_no = 0
      self.score = 0
      self.attempt = 1
      self.next_question()

   def next_question(self):
      if self.current_q_no >= self.total_questions:
         displayResults(self.score)
         return
      a = randomInt(self.minv, self.maxv)
      b = randomInt(self.minv, self.maxv)
      op = decideOperation()
      #Answer Checking
      self.current_answer = a + b if op == '+' else a - b
      self.attempt = 1
      displayProblem(a, b, op)

   def submit_answer(self):
      txt = self.entry.get().strip()
      if txt == "":
         self.feedback_label.config(text="Please enter an answer.")
         return
      try:
         user = int(txt)
      except ValueError:
         self.feedback_label.config(text="Enter a valid number (No '.').")
         return

      if isCorrect(user, self.current_answer):
         if self.attempt == 1:
            self.score += 10
            self.feedback_label.config(text="Correct! (+10)")
         else:
            self.score += 5
            self.feedback_label.config(text="Correct on second try! (+5)")
         self.current_q_no += 1
         self.root.after(800, self.next_question)
      else:
         if self.attempt == 1:
            self.attempt = 2
            self.feedback_label.config(text="Incorrect. Try once more.")
            self.entry.delete(0, tk.END)
         else:
            self.feedback_label.config(text=f"Incorrect again. Answer: {self.current_answer}")
            self.current_q_no += 1
            self.root.after(1000, self.next_question)

      self.progress_label.config(text=f"Question {self.current_q_no+1} of {self.total_questions}    Score: {self.score}")

   def grade(self, score):
      total = score / (self.total_questions * 10) * 100
      if total > 90:
         return "A+"
      if total > 80:
         return "A"
      if total > 70:
         return "B"
      if total > 60:
         return "C"
      if total > 50:
         return "D"
      return "F"

#Self explanatory
   def play_again(self):
      if messagebox.askyesno("Play Again", "Do you want to play again?"):
         displayMenu()
      else:
         self.root.quit()

#Statement to rename app and root so that it runs
if __name__ == "__main__":
   root = tk.Tk()
   app = QuizApp(root)
   root.mainloop()