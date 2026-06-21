import tkinter as tk
from tkinter import scrolledtext
import re

def process_assembly():
    input_text = text_area.get("1.0", tk.END).strip()
    lines = input_text.splitlines()

    # Define the comment mapping
    opcode_comments = {
        "LDA": "; A = Value → NZ",
        "LDX": "; X = Value → NZ",
        "LDY": "; Y = Value → NZ",
        "TAX": "; X = A",
        "TAY": "; Y = A",
        "TXA": "; A = X",
        "TYA": "; A = Y",
        "STA": "; A → RAM $Address",
        "STX": "; X → RAM $Address",
        "STY": "; Y → RAM $Address",
        "PHA": "; A → Stack",
        "PLA": "; A ← Stack → NZ",
        "INC": "; A++ → NZ",
        "INX": "; X++ → NZ",
        "INY": "; Y++ → NZ",
        "ASL": "; x2, Rightmost = 0, C = Leftmost, → NZC",
        "ROL": "; Rightmost = C, C = Leftmost, → NZC",
        "CMP": "; Memory - A → NZC",
        "CPX": "; Memory - X → NZC",
        "CPY": "; Memory - Y → NZC",
        "BPL": "; JMP if Negative == 0",
        "BMI": "; JMP if Negative == 1",
        "BNE": "; JMP if Zero == 0",
        "BEQ": "; JMP if Zero == 1",
        "BCC": "; JMP if Carry == 0",
        "BCS": "; JMP if Carry == 1",
        "BVC": "; JMP if oVerflow == 0",
        "BVS": "; JMP if oVerflow == 1",
        "ORA": "; Enable bits → NZ",
        "AND": "; Disable bits → NZ"
    }

    parsed_lines = []
    for line in lines:
        if ":" in line:
            parts = line.split(":", 2)
            try:
                addr = int(parts[1].strip(), 16)
                raw_cmd = parts[2].strip()
                parsed_lines.append({'addr': addr, 'raw': raw_cmd})
            except (ValueError, IndexError): continue

    addr_to_idx = {item['addr']: i for i, item in enumerate(parsed_lines)}
    jump_targets = {int(line.split(":", 2)[2].split('$')[-1].split('=')[0].strip(), 16) 
                    for line in lines if any(b in line for b in ['BPL', 'BMI', 'BNE', 'BEQ', 'BCC', 'BCS', 'BVC', 'BVS', 'JMP'])}

    final_output = []
    remove_opcodes = remove_opcodes_var.get()

    for i, item in enumerate(parsed_lines):
        if item['addr'] in jump_targets:
            final_output.append(":")

        raw_cmd = item['raw']
        
        # 1. Clean Opcode if requested
        if remove_opcodes:
            tokens = raw_cmd.split()
            filtered = [t for t in tokens if not (len(t) <= 2 and all(c in '0123456789ABCDEFabcdef' for c in t))]
            cmd = " ".join(filtered)
        else:
            cmd = raw_cmd

        # 2. Strip assignments (=) and Indexing (@)
        # Removes anything from '=' or '@' onwards
        cmd = re.split(r'[=@]', cmd)[0].strip()
        
        # 3. Convert Hex immediate (#$xx) to Binary (#%xxxxxxxx)
        if "#$" in cmd:
            match = re.search(r'#\$([0-9A-Fa-f]+)', cmd)
            if match:
                hex_val = match.group(1)
                binary_val = bin(int(hex_val, 16))[2:].zfill(8)
                cmd = cmd.replace(f"#${hex_val}", f"#%{binary_val}")

        # 4. Handle Branching (Logic)
        branch_mnemonic = ""
        if any(b in cmd for b in ['BPL', 'BMI', 'BNE', 'BEQ', 'BCC', 'BCS', 'BVC', 'BVS', 'JMP']):
            try:
                branch_mnemonic = next((b for b in ['BPL', 'BMI', 'BNE', 'BEQ', 'BCC', 'BCS', 'BVC', 'BVS', 'JMP'] if b in cmd), "")
                target_addr = int(cmd.split('$')[-1].split('=')[0].strip(), 16)
                target_idx = addr_to_idx.get(target_addr)
                if target_idx is not None:
                    direction = "forward" if target_idx > i else "backward"
                    markers = 0
                    r = range(i + 1, target_idx + 1) if direction == "forward" else range(target_idx, i)
                    for idx in r:
                        if parsed_lines[idx]['addr'] in jump_targets:
                            markers += 1
                    symbol = "+" if direction == "forward" else "-"
                    cmd = f"{cmd.split('$')[0].strip()} :{symbol * markers}"
            except (ValueError, IndexError): pass

        # 5. Append Documentation Comment
        current_op = branch_mnemonic if branch_mnemonic else cmd.split()[0] if cmd.split() else ""
        if current_op in opcode_comments:
            cmd = f"{cmd.ljust(20)} {opcode_comments[current_op]}"
        final_output.append(cmd)

    text_area.delete("1.0", tk.END)
    text_area.insert("1.0", "\n".join(final_output))
    
def copy_to_clipboard():
    root.clipboard_clear()
    root.clipboard_append(text_area.get("1.0", tk.END))
    copy_btn.config(text="Copied!")
    root.after(2000, lambda: copy_btn.config(text="Copy to Clipboard"))

def paste_from_clipboard():
    try:
        clipboard_text = root.clipboard_get()
        text_area.delete("1.0", tk.END)
        text_area.insert("1.0", clipboard_text)
    except tk.TclError:
        pass

# GUI Setup
root = tk.Tk()
root.title("6502 Assembly Formatter")

text_area = scrolledtext.ScrolledText(root, width=60, height=20)
text_area.pack(pady=10)

remove_opcodes_var = tk.BooleanVar()
tk.Checkbutton(root, text="Remove Opcodes", variable=remove_opcodes_var).pack()

btn_frame = tk.Frame(root)
btn_frame.pack(pady=5)

process_btn = tk.Button(btn_frame, text="Format Assembly", command=process_assembly)
process_btn.pack(side=tk.LEFT, padx=5)

paste_btn = tk.Button(btn_frame, text="Paste", command=paste_from_clipboard)
paste_btn.pack(side=tk.LEFT, padx=5)

copy_btn = tk.Button(btn_frame, text="Copy to Clipboard", command=copy_to_clipboard)
copy_btn.pack(side=tk.LEFT, padx=5)

root.mainloop()