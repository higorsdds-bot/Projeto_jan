import customtkinter as ctk
from tkinter import ttk, messagebox
import pandas as pd
from datetime import datetime
import os

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

ARQUIVO_DB = "banco_dados.csv"
agendamentos = []

def carregar_dados():
    global agendamentos
    if os.path.exists(ARQUIVO_DB):
        try:
            df = pd.read_csv(ARQUIVO_DB)
            agendamentos = df.to_dict('records')
        except Exception as e:
            messagebox.showerror("Erro", f"Erro: {e}")

def salvar_e_atualizar():
    df = pd.DataFrame(agendamentos)
    df.to_csv(ARQUIVO_DB, index=False)
    atualizar_tabela()

def adicionar_agendamento():
    c = entry_cliente.get()
    s = entry_servico.get()
    v = entry_valor.get()

    if not c or not s or not v:
        messagebox.showwarning("Atenção", "Preencha todos os campos!")
        return
    try:
        val = float(v.replace(',', '.'))
    except:
        messagebox.showerror("Erro", "Valor inválido.")
        return

    now = datetime.now()
    agendamentos.append({
        "Data/Hora": now.strftime("%d/%m/%Y %H:%M"),
        "Cliente": c, "Serviço": s, "Valor (R$)": val,
        "Dia": now.day, "Mês": now.month, "Ano": now.year
    })
    
    salvar_e_atualizar()
    entry_cliente.delete(0, 'end')
    entry_servico.delete(0, 'end')
    entry_valor.delete(0, 'end')
    entry_cliente.focus()
    lbl_status.configure(text=f"✅ {c} salvo com sucesso!", text_color="#2cc985")

def excluir_selecionado():
    selecionado = tree.selection()
    if not selecionado:
        messagebox.showwarning("Aviso", "Selecione um item na tabela.")
        return
    
    if not messagebox.askyesno("Confirmar", "Excluir este item?"): return

    index = tree.index(selecionado[0])
    try:
        item = agendamentos.pop(index)
        salvar_e_atualizar()
        lbl_status.configure(text=f"🗑️ Agendamento removido.", text_color="#ff5555")
    except: pass

def limpar_dados(periodo):
    if not agendamentos: return
    if not messagebox.askyesno("Cuidado", f"Apagar TUDO de {periodo}?"): return

    agora = datetime.now()
    nova_lista = []
    
    for item in agendamentos:
        try:
            dt = datetime.strptime(item["Data/Hora"], "%d/%m/%Y %H:%M")
            manter = True
            if periodo == "hoje" and dt.date() == agora.date(): manter = False
            elif periodo == "mes" and (dt.month == agora.month and dt.year == agora.year): manter = False
            if manter: nova_lista.append(item)
        except: nova_lista.append(item)

    agendamentos[:] = nova_lista
    salvar_e_atualizar()
    lbl_status.configure(text=f"🧹 Limpeza ({periodo}) concluída.", text_color="orange")

def exportar_excel():
    if not agendamentos: return
    try:
        df = pd.DataFrame(agendamentos)
        nome = f"Relatorio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        if "Dia" not in df.columns:
             dt = pd.to_datetime(df['Data/Hora'], format="%d/%m/%Y %H:%M")
             df['Dia'], df['Mês'], df['Ano'] = dt.dt.day, dt.dt.month, dt.dt.year
        
        cols = [c for c in ["Data/Hora", "Dia", "Mês", "Ano", "Cliente", "Serviço", "Valor (R$)"] if c in df.columns]
        df[cols].to_excel(nome, index=False)
        messagebox.showinfo("Excel", f"Arquivo Gerado: {nome}")
    except Exception as e:
        messagebox.showerror("Erro", str(e))

def atualizar_tabela():
    for i in tree.get_children(): tree.delete(i)
    total = sum(item['Valor (R$)'] for item in agendamentos)
    
    for item in reversed(agendamentos):
        tree.insert("", "end", values=(item["Data/Hora"], item["Cliente"], item["Serviço"], f"R$ {item['Valor (R$)']:.2f}"))
    
    lbl_total.configure(text=f"R$ {total:.2f}")

app = ctk.CTk()
app.title("Sistema Gestão VIP")
app.geometry("900x650")

app.grid_columnconfigure(0, weight=1)
app.grid_rowconfigure(2, weight=1)

frame_top = ctk.CTkFrame(app, fg_color="transparent")
frame_top.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))

ctk.CTkLabel(frame_top, text="Controle de Caixa", font=("Roboto", 24, "bold")).pack(side="left")

frame_total = ctk.CTkFrame(frame_top, fg_color="#2b2b2b", corner_radius=10)
frame_total.pack(side="right")
ctk.CTkLabel(frame_total, text="FATURAMENTO TOTAL", font=("Roboto", 10)).pack(padx=15, pady=(5,0))
lbl_total = ctk.CTkLabel(frame_total, text="R$ 0.00", font=("Roboto", 22, "bold"), text_color="#2cc985")
lbl_total.pack(padx=15, pady=(0,5))

frame_input = ctk.CTkFrame(app, corner_radius=15)
frame_input.grid(row=1, column=0, sticky="ew", padx=20, pady=10)

entry_cliente = ctk.CTkEntry(frame_input, placeholder_text="Nome do Cliente", width=250, height=40)
entry_cliente.grid(row=0, column=0, padx=10, pady=20)

entry_servico = ctk.CTkEntry(frame_input, placeholder_text="Serviço Realizado", width=250, height=40)
entry_servico.grid(row=0, column=1, padx=10, pady=20)

entry_valor = ctk.CTkEntry(frame_input, placeholder_text="Valor (Ex: 50.00)", width=120, height=40)
entry_valor.grid(row=0, column=2, padx=10, pady=20)

btn_salvar = ctk.CTkButton(frame_input, text="ADICIONAR +", command=adicionar_agendamento, 
                           width=120, height=40, fg_color="#2cc985", hover_color="#25a86e", 
                           font=("Roboto", 12, "bold"), text_color="#1a1a1a")
btn_salvar.grid(row=0, column=3, padx=10, pady=20)

lbl_status = ctk.CTkLabel(frame_input, text="", font=("Roboto", 12))
lbl_status.grid(row=1, column=0, columnspan=4, pady=(0, 10))

frame_tabela = ctk.CTkFrame(app, corner_radius=10)
frame_tabela.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)

style = ttk.Style()
style.theme_use("clam")
style.configure("Treeview", 
                background="#2b2b2b", 
                foreground="white", 
                fieldbackground="#2b2b2b", 
                rowheight=35, 
                borderwidth=0,
                font=("Roboto", 11))
style.configure("Treeview.Heading", 
                background="#1f1f1f", 
                foreground="white", 
                font=("Roboto", 12, "bold"),
                relief="flat")
style.map("Treeview", background=[('selected', '#1f538d')])

colunas = ("Data", "Cliente", "Serviço", "Valor")
tree = ttk.Treeview(frame_tabela, columns=colunas, show="headings", selectmode="browse")

tree.heading("Data", text="DATA")
tree.heading("Cliente", text="CLIENTE")
tree.heading("Serviço", text="SERVIÇO")
tree.heading("Valor", text="VALOR")

tree.column("Data", width=150, anchor="center")
tree.column("Cliente", width=250, anchor="w")
tree.column("Serviço", width=250, anchor="w")
tree.column("Valor", width=120, anchor="e")

scroll_y = ctk.CTkScrollbar(frame_tabela, command=tree.yview)
tree.configure(yscroll=scroll_y.set)

tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
scroll_y.pack(side="right", fill="y", padx=5, pady=5)

frame_acoes = ctk.CTkFrame(app, fg_color="transparent")
frame_acoes.grid(row=3, column=0, sticky="ew", padx=20, pady=20)

ctk.CTkButton(frame_acoes, text="Exportar Excel", command=exportar_excel, fg_color="#3B8ED0").pack(side="left", padx=5)

ctk.CTkButton(frame_acoes, text="Limpar Mês", command=lambda: limpar_dados("mes"), 
              fg_color="#C0392B", hover_color="#A93226").pack(side="right", padx=5)
ctk.CTkButton(frame_acoes, text="Limpar Dia", command=lambda: limpar_dados("hoje"), 
              fg_color="#E74C3C", hover_color="#C0392B").pack(side="right", padx=5)
ctk.CTkButton(frame_acoes, text="Apagar Selecionado", command=excluir_selecionado, 
              fg_color="#E67E22", hover_color="#D35400").pack(side="right", padx=5)

carregar_dados()
atualizar_tabela()
app.mainloop()