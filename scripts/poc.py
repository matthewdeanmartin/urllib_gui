import tkinter as tk
import webbrowser


def insert_link(text, label, url):
    tag = f"link_{url}"

    text.config(state="normal")

    start = text.index("end-1c")
    text.insert("end-1c", label)
    end = text.index("end-1c")

    text.tag_add(tag, start, end)
    text.tag_config(tag, foreground="blue", underline=True)

    text.tag_bind(tag, "<Button-1>", lambda event: webbrowser.open_new_tab(url))
    text.tag_bind(tag, "<Enter>", lambda event: text.config(cursor="hand2"))
    text.tag_bind(tag, "<Leave>", lambda event: text.config(cursor=""))

    text.config(state="disabled")


root = tk.Tk()

text = tk.Text(root, wrap="word", width=60, height=10, cursor="")
text.pack(padx=20, pady=20)

text.config(state="normal")
text.insert("end", "Go to ")
text.config(state="disabled")

insert_link(text, "Python.org", "https://www.python.org")

text.config(state="normal")
text.insert("end-1c", " for more info.")
text.config(state="disabled")

root.mainloop()
