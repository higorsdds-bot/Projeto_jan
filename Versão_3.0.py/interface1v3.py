import customtkinter as ctk
from tkinter import ttk, messagebox
from tkcalendar import Calendar
import pandas as pd
from datetime import datetime
import os
import sys

# Tenta importar o FPDF para gerar PDFs
try:
    from fpdf import FPDF
    HAS_FPDF = True
except ImportError:
    HAS_FPDF = False

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

# ===================================================================
# 1. GARANTIR QUE SALVE NA MÁQUINA (Funciona no .py e no .exe)
# ===================================================================
if getattr(sys, 'frozen', False):
    DIRETORIO_ATUAL = os.path.dirname(sys.executable)
else:
    DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))

ARQUIVO_DB = os.path.join(DIRETORIO_ATUAL, "banco_dados.csv")
# ===================================================================

agendamentos = []

# Cores modernas
COR_PRIMARIA = "#6366f1"      # Indigo
COR_SECUNDARIA = "#8b5cf6"    # Violet
COR_SUCESSO = "#10b981"       # Emerald
COR_PERIGO = "#ef4444"        # Red
COR_ALERTA = "#f59e0b"        # Amber
COR_FUNDO = "#0f172a"         # Slate 900
COR_CARTAO = "#1e293b"        # Slate 800
COR_TEXTO = "#f1f5f9"         # Slate 100
COR_SUBTEXTO = "#94a3b8"      # Slate 400

def carregar_dados():
    global agendamentos
    if os.path.exists(ARQUIVO_DB):
        try:
            df = pd.read_csv(ARQUIVO_DB)
            agendamentos = df.to_dict('records')
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar dados: {e}")

def salvar_dados():
    df = pd.DataFrame(agendamentos)
    df.to_csv(ARQUIVO_DB, index=False)

def registrar_imediato():
    cliente = entry_cliente_agora.get().strip()
    servico = entry_servico_agora.get().strip()
    valor = entry_valor_agora.get().strip()
    
    if not cliente or not servico or not valor:
        messagebox.showwarning("Atenção", "Preencha todos os campos para atendimento imediato!")
        return
    
    try:
        valor_float = float(valor.replace(',', '.'))
    except ValueError:
        messagebox.showerror("Erro", "Valor numérico inválido!")
        return
    
    agora = datetime.now()
    data_hora_str = agora.strftime("%d/%m/%Y %H:%M")
    
    agendamentos.append({
        "Data/Hora": data_hora_str,
        "Cliente": cliente,
        "Serviço": servico,
        "Valor (R$)": valor_float,
        "Status": "Concluído",
        "Dia": agora.day,
        "Mês": agora.month,
        "Ano": agora.year
    })
    
    salvar_dados()
    atualizar_tabela()
    limpar_campos_agora()
    mostrar_status("✅ Atendimento imediato registrado!", COR_SUCESSO)

def registrar_agendamento():
    cliente = entry_cliente_futuro.get().strip()
    servico = entry_servico_futuro.get().strip()
    valor = entry_valor_futuro.get().strip()
    data_ag = calendario.get_date()
    hora_ag = combo_hora.get()
    minuto_ag = combo_minuto.get()
    
    if not cliente or not servico:
        messagebox.showwarning("Atenção", "Preencha pelo menos Cliente e Serviço!")
        return
    
    if not valor:
        valor_float = 0.0
    else:
        try:
            valor_float = float(valor.replace(',', '.'))
        except ValueError:
            messagebox.showerror("Erro", "Valor numérico inválido!")
            return
    
    data_hora_str = f"{data_ag} {hora_ag}:{minuto_ag}"
    data_hora_obj = datetime.strptime(data_hora_str, "%d/%m/%Y %H:%M")
    
    eh_futuro = data_hora_obj > datetime.now()
    status = "Agendado" if eh_futuro else "Concluído"
    
    agendamentos.append({
        "Data/Hora": data_hora_str,
        "Cliente": cliente,
        "Serviço": servico,
        "Valor (R$)": valor_float,
        "Status": status,
        "Dia": data_hora_obj.day,
        "Mês": data_hora_obj.month,
        "Ano": data_hora_obj.year
    })
    
    salvar_dados()
    atualizar_tabela()
    limpar_campos_futuro()
    mostrar_status(f"📅 Agendamento salvo como {status}!", COR_SUCESSO if eh_futuro else COR_ALERTA)

def limpar_campos_agora():
    entry_cliente_agora.delete(0, 'end')
    entry_servico_agora.delete(0, 'end')
    entry_valor_agora.delete(0, 'end')
    entry_cliente_agora.focus()

def limpar_campos_futuro():
    entry_cliente_futuro.delete(0, 'end')
    entry_servico_futuro.delete(0, 'end')
    entry_valor_futuro.delete(0, 'end')
    entry_cliente_futuro.focus()

def mostrar_status(mensagem, cor):
    lbl_status.configure(text=mensagem, text_color=cor)
    app.after(3000, lambda: lbl_status.configure(text=""))

def excluir_selecionado():
    selecionado = tree.selection()
    if not selecionado:
        messagebox.showwarning("Aviso", "Selecione um item na tabela.")
        return
    
    if not messagebox.askyesno("Confirmar", "Deseja realmente excluir este registro?"):
        return
    
    # O identificador do item (iid) agora é o índice correto na memória
    index = int(selecionado[0])
    try:
        agendamentos.pop(index)
        salvar_dados()
        atualizar_tabela()
        mostrar_status("🗑️ Item removido", COR_PERIGO)
    except Exception as e:
        print(f"Erro ao excluir: {e}")

def marcar_concluido():
    selecionado = tree.selection()
    if not selecionado:
        messagebox.showwarning("Aviso", "Selecione um agendamento.")
        return
    
    # Pegamos o índice exato da lista através do identificador do item na tabela
    index = int(selecionado[0])
    
    if agendamentos[index]["Status"] == "Concluído":
        messagebox.showinfo("Aviso", "Este agendamento já está concluído!")
        return

    valor_atual = float(agendamentos[index].get("Valor (R$)", 0.0))
    if valor_atual <= 0.0:
        dialog = ctk.CTkInputDialog(text="O valor estava em branco.\nDigite o valor final cobrado (R$):", title="Valor do Serviço")
        valor_final = dialog.get_input()
        
        if valor_final:
            try:
                agendamentos[index]["Valor (R$)"] = float(valor_final.replace(',', '.'))
            except ValueError:
                messagebox.showerror("Erro", "Valor inválido! O agendamento não foi concluído.")
                return
        else:
            return # Cancelou o pop-up

    try:
        agendamentos[index]["Status"] = "Concluído"
        salvar_dados()
        atualizar_tabela()
        mostrar_status("✅ Marcado como concluído!", COR_SUCESSO)
    except Exception as e:
        print(f"Erro ao marcar como concluido: {e}")

def limpar_dados(periodo):
    if not agendamentos:
        return
    
    if not messagebox.askyesno("Cuidado", f"Apagar todos os registros de {periodo}?"):
        return
    
    agora = datetime.now()
    nova_lista = []
    
    for item in agendamentos:
        try:
            dt = datetime.strptime(item["Data/Hora"], "%d/%m/%Y %H:%M")
            manter = True
            if periodo == "hoje" and dt.date() == agora.date():
                manter = False
            elif periodo == "mes" and dt.month == agora.month and dt.year == agora.year:
                manter = False
            if manter:
                nova_lista.append(item)
        except:
            nova_lista.append(item)
    
    agendamentos[:] = nova_lista
    salvar_dados()
    atualizar_tabela()
    mostrar_status(f"🧹 Limpeza ({periodo}) concluída", COR_ALERTA)

def exportar_excel():
    if not agendamentos:
        messagebox.showwarning("Aviso", "Nenhum dado para exportar!")
        return
    
    try:
        df = pd.DataFrame(agendamentos)
        nome = os.path.join(DIRETORIO_ATUAL, f"Relatorio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
        
        cols = [c for c in ["Data/Hora", "Dia", "Mês", "Ano", "Cliente", "Serviço", "Valor (R$)", "Status"] if c in df.columns]
        df[cols].to_excel(nome, index=False)
        messagebox.showinfo("Sucesso", f"Excel gerado em:\n{nome}")
    except Exception as e:
        messagebox.showerror("Erro", str(e))

def exportar_pdf():
    if not HAS_FPDF:
        messagebox.showerror("Erro", "A biblioteca 'fpdf' não está instalada.\nAbra o terminal e digite: pip install fpdf")
        return

    if not agendamentos:
        messagebox.showwarning("Aviso", "Nenhum dado para exportar!")
        return

    agora = datetime.now()
    hoje_str = agora.strftime("%d/%m/%Y")
    mes_atual = agora.month
    ano_atual = agora.year
    
    lucro_dia = 0.0
    lucro_mes = 0.0
    
    for item in agendamentos:
        if item.get("Status") == "Concluído":
            try:
                dt = datetime.strptime(item["Data/Hora"], "%d/%m/%Y %H:%M")
                val = float(item.get("Valor (R$)", 0.0))
                
                if dt.month == mes_atual and dt.year == ano_atual:
                    lucro_mes += val
                    if dt.date() == agora.date():
                        lucro_dia += val
            except:
                pass

    try:
        pdf = FPDF()
        pdf.add_page()
        
        pdf.set_font("Arial", 'B', 20)
        pdf.cell(200, 10, txt="Relatório Financeiro - Barbearia", ln=True, align='C')
        pdf.ln(5)
        
        pdf.set_font("Arial", '', 12)
        pdf.cell(200, 10, txt=f"Data de Emissão: {hoje_str}", ln=True, align='C')
        pdf.ln(15)
        
        pdf.set_font("Arial", 'B', 14)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(0, 15, txt=f" Lucro Bruto de Hoje ({hoje_str}): R$ {lucro_dia:.2f}", ln=True, fill=True)
        pdf.ln(5)
        pdf.cell(0, 15, txt=f" Lucro Bruto do Mês ({mes_atual:02d}/{ano_atual}): R$ {lucro_mes:.2f}", ln=True, fill=True)
        
        pdf.ln(20)
        pdf.set_font("Arial", 'I', 10)
        pdf.cell(200, 10, txt="* Este relatório soma apenas serviços marcados como 'Concluído'.", ln=True)

        nome_arquivo = os.path.join(DIRETORIO_ATUAL, f"Balanco_Lucro_{agora.strftime('%Y%m%d_%H%M%S')}.pdf")
        pdf.output(nome_arquivo)
        
        messagebox.showinfo("Sucesso", f"PDF gerado com sucesso!\nSalvo em: {nome_arquivo}")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao gerar o PDF:\n{e}")

def atualizar_tabela(filtro=None):
    if filtro is None:
        filtro = combo_filtro.get()
        
    for item in tree.get_children():
        tree.delete(item)
    
    agora = datetime.now()
    total = 0
    qtd_hoje = 0
    qtd_futuros = 0
    
    # 1. Atrelar o índice da lista (0, 1, 2...) aos itens antes de ordenar
    agendamentos_com_indice = list(enumerate(agendamentos))
    
    # 2. Ordenar pela data, mas carregando o índice junto!
    agendamentos_ordenados = sorted(agendamentos_com_indice, 
                                     key=lambda x: datetime.strptime(x[1]["Data/Hora"], "%d/%m/%Y %H:%M"), 
                                     reverse=True)
    
    for idx, item in agendamentos_ordenados:
        try:
            dt = datetime.strptime(item["Data/Hora"], "%d/%m/%Y %H:%M")
            
            if filtro == "Hoje" and dt.date() != agora.date():
                continue
            elif filtro == "Futuros" and dt <= agora:
                continue
            elif filtro == "Concluídos" and item.get("Status") != "Concluído":
                continue
            elif filtro == "Agendados" and item.get("Status") != "Agendado":
                continue
            
            if dt.date() == agora.date():
                qtd_hoje += 1
            if dt > agora and item.get("Status") == "Agendado":
                qtd_futuros += 1
            
            valor_bruto = item.get("Valor (R$)", 0.0)
            try:
                valor_float = float(str(valor_bruto).replace(',', '.'))
            except ValueError:
                valor_float = 0.0
                
            if item.get("Status") == "Concluído":
                total += valor_float
            
            tag = ""
            if item.get("Status") == "Agendado":
                if dt > agora:
                    tag = "futuro"
                else:
                    tag = "atrasado"
            else:
                tag = "concluido"
            
            valor_display = f"R$ {valor_float:.2f}" if valor_float > 0 else "A definir"
            
            # O "iid=str(idx)" garante que a linha sabe sua posição exata na lista real
            tree.insert("", "end", iid=str(idx), values=(
                item["Data/Hora"],
                item["Cliente"],
                item["Serviço"],
                valor_display,
                item.get("Status", "-")
            ), tags=(tag,))
            
        except Exception as e:
            continue
    
    lbl_total.configure(text=f"R$ {total:.2f}")
    lbl_hoje.configure(text=str(qtd_hoje))
    lbl_futuros.configure(text=str(qtd_futuros))

# ============ INTERFACE ============
app = ctk.CTk()
app.title("Cortes & Barbas ")
app.geometry("1150x800")
app.configure(fg_color=COR_FUNDO)

app.grid_columnconfigure(0, weight=1)
app.grid_rowconfigure(4, weight=1)

# ============ HEADER COM CARDS ============
frame_header = ctk.CTkFrame(app, fg_color="transparent")
frame_header.grid(row=0, column=0, sticky="ew", padx=25, pady=(20, 10))
frame_header.grid_columnconfigure((0, 1, 2, 3), weight=1)

frame_titulo = ctk.CTkFrame(frame_header, fg_color="transparent")
frame_titulo.grid(row=0, column=0, sticky="w")
ctk.CTkLabel(frame_titulo, text="💈 Salão ", font=("Inter", 26, "bold"), text_color=COR_TEXTO).pack(anchor="w")
ctk.CTkLabel(frame_titulo, text="Controle de Barbearia", font=("Inter", 12), text_color=COR_SUBTEXTO).pack(anchor="w")

card_faturamento = ctk.CTkFrame(frame_header, fg_color=COR_CARTAO, corner_radius=15)
card_faturamento.grid(row=0, column=1, padx=10, pady=5, sticky="e")
ctk.CTkLabel(card_faturamento, text="💰 Faturamento (Concluídos)", font=("Inter", 11), text_color=COR_SUBTEXTO).pack(padx=20, pady=(10, 0))
lbl_total = ctk.CTkLabel(card_faturamento, text="R$ 0.00", font=("Inter", 22, "bold"), text_color=COR_SUCESSO)
lbl_total.pack(padx=20, pady=(0, 10))

card_hoje = ctk.CTkFrame(frame_header, fg_color=COR_CARTAO, corner_radius=15)
card_hoje.grid(row=0, column=2, padx=10, pady=5)
ctk.CTkLabel(card_hoje, text="📅 Registros de Hoje", font=("Inter", 11), text_color=COR_SUBTEXTO).pack(padx=20, pady=(10, 0))
lbl_hoje = ctk.CTkLabel(card_hoje, text="0", font=("Inter", 22, "bold"), text_color=COR_PRIMARIA)
lbl_hoje.pack(padx=20, pady=(0, 10))

card_futuros = ctk.CTkFrame(frame_header, fg_color=COR_CARTAO, corner_radius=15)
card_futuros.grid(row=0, column=3, padx=10, pady=5, sticky="e")
ctk.CTkLabel(card_futuros, text="⏰ Pendentes/Agendados", font=("Inter", 11), text_color=COR_SUBTEXTO).pack(padx=20, pady=(10, 0))
lbl_futuros = ctk.CTkLabel(card_futuros, text="0", font=("Inter", 22, "bold"), text_color=COR_SECUNDARIA)
lbl_futuros.pack(padx=20, pady=(0, 10))


# ============ TABVIEW ============
tabview = ctk.CTkTabview(app, fg_color=COR_CARTAO, segmented_button_selected_color=COR_PRIMARIA, segmented_button_selected_hover_color=COR_SECUNDARIA, height=120)
tabview.grid(row=1, column=0, sticky="ew", padx=25, pady=5)

aba_agora = tabview.add("⚡ Atendimento na Hora")
aba_futuro = tabview.add("📅 Agendamento Futuro")

# Aba Agora
aba_agora.grid_columnconfigure((0,1,2,3), weight=1)
ctk.CTkLabel(aba_agora, text="Cliente:", font=("Inter", 12), text_color=COR_SUBTEXTO).grid(row=0, column=0, padx=5, pady=5, sticky="w")
entry_cliente_agora = ctk.CTkEntry(aba_agora, placeholder_text="Nome do cliente", width=250, height=38)
entry_cliente_agora.grid(row=1, column=0, padx=10, pady=(0, 5), sticky="w")

ctk.CTkLabel(aba_agora, text="Serviço:", font=("Inter", 12), text_color=COR_SUBTEXTO).grid(row=0, column=1, padx=5, pady=5, sticky="w")
entry_servico_agora = ctk.CTkEntry(aba_agora, placeholder_text="Ex: Corte + Barba", width=250, height=38)
entry_servico_agora.grid(row=1, column=1, padx=10, pady=(0, 5), sticky="w")

ctk.CTkLabel(aba_agora, text="Valor (R$):", font=("Inter", 12), text_color=COR_SUBTEXTO).grid(row=0, column=2, padx=5, pady=5, sticky="w")
entry_valor_agora = ctk.CTkEntry(aba_agora, placeholder_text="0,00", width=150, height=38)
entry_valor_agora.grid(row=1, column=2, padx=10, pady=(0, 5), sticky="w")

btn_add_agora = ctk.CTkButton(aba_agora, text="✅ REGISTRAR CONCLUÍDO", command=registrar_imediato,
                              height=40, fg_color=COR_SUCESSO, hover_color="#059669", font=("Inter", 13, "bold"))
btn_add_agora.grid(row=1, column=3, padx=10, pady=(0, 5), sticky="e")

# Aba Futuro
aba_futuro.grid_columnconfigure((0,1,2,3,4,5), weight=0)
ctk.CTkLabel(aba_futuro, text="Cliente:", font=("Inter", 12)).grid(row=0, column=0, padx=5, pady=5, sticky="w")
entry_cliente_futuro = ctk.CTkEntry(aba_futuro, placeholder_text="Nome", width=180, height=38)
entry_cliente_futuro.grid(row=1, column=0, padx=5, pady=(0, 5))

ctk.CTkLabel(aba_futuro, text="Serviço:", font=("Inter", 12)).grid(row=0, column=1, padx=5, pady=5, sticky="w")
entry_servico_futuro = ctk.CTkEntry(aba_futuro, placeholder_text="Serviço", width=180, height=38)
entry_servico_futuro.grid(row=1, column=1, padx=5, pady=(0, 5))

ctk.CTkLabel(aba_futuro, text="Valor (Opcional):", font=("Inter", 12)).grid(row=0, column=2, padx=5, pady=5, sticky="w")
entry_valor_futuro = ctk.CTkEntry(aba_futuro, placeholder_text="Deixe vazio se n/s", width=130, height=38)
entry_valor_futuro.grid(row=1, column=2, padx=5, pady=(0, 5))

ctk.CTkLabel(aba_futuro, text="Data:", font=("Inter", 12)).grid(row=0, column=3, padx=5, pady=5, sticky="w")
calendario = Calendar(aba_futuro, selectmode='day', date_pattern='dd/mm/yyyy', width=10)
calendario.grid(row=1, column=3, padx=5, pady=(0, 5))

ctk.CTkLabel(aba_futuro, text="Hora:", font=("Inter", 12)).grid(row=0, column=4, padx=5, pady=5, sticky="w")
frame_hora = ctk.CTkFrame(aba_futuro, fg_color="transparent")
frame_hora.grid(row=1, column=4, padx=5, pady=(0, 5))

combo_hora = ctk.CTkComboBox(frame_hora, values=[f"{h:02d}" for h in range(8, 21)], width=60, height=35)
combo_hora.set("09")
combo_hora.pack(side="left")
ctk.CTkLabel(frame_hora, text=":", font=("Inter", 14, "bold")).pack(side="left", padx=2)
combo_minuto = ctk.CTkComboBox(frame_hora, values=["00", "15", "30", "45"], width=60, height=35)
combo_minuto.set("00")
combo_minuto.pack(side="left")

btn_add_futuro = ctk.CTkButton(aba_futuro, text="⏰ AGENDAR", command=registrar_agendamento,
                               width=120, height=40, fg_color=COR_PRIMARIA, hover_color=COR_SECUNDARIA, font=("Inter", 13, "bold"))
btn_add_futuro.grid(row=1, column=5, padx=10, pady=(0, 5))

# Status Global
lbl_status = ctk.CTkLabel(app, text="", font=("Inter", 12))
lbl_status.grid(row=2, column=0, pady=(0, 5))

# ============ FILTROS ============
frame_filtros = ctk.CTkFrame(app, fg_color="transparent")
frame_filtros.grid(row=3, column=0, sticky="ew", padx=25, pady=(0, 5))

ctk.CTkLabel(frame_filtros, text="📊 Filtrar Tabela:", font=("Inter", 12), text_color=COR_SUBTEXTO).pack(side="left", padx=(0, 10))
combo_filtro = ctk.CTkComboBox(frame_filtros, values=["Todos", "Hoje", "Futuros", "Agendados", "Concluídos"],
                                width=150, height=32, command=lambda x: atualizar_tabela())
combo_filtro.set("Todos")
combo_filtro.pack(side="left")

# ============ TABELA ============
frame_tabela = ctk.CTkFrame(app, fg_color=COR_CARTAO, corner_radius=20)
frame_tabela.grid(row=4, column=0, sticky="nsew", padx=25, pady=5)
frame_tabela.grid_rowconfigure(0, weight=1)
frame_tabela.grid_columnconfigure(0, weight=1)

style = ttk.Style()
style.theme_use("clam")
style.configure("Treeview", background=COR_CARTAO, foreground=COR_TEXTO, fieldbackground=COR_CARTAO, 
                rowheight=40, borderwidth=0, font=("Inter", 11))
style.configure("Treeview.Heading", background=COR_PRIMARIA, foreground="white", 
                font=("Inter", 12, "bold"), relief="flat", padding=10)
style.map("Treeview", background=[('selected', COR_SECUNDARIA)], foreground=[('selected', 'white')])

colunas = ("Data/Hora", "Cliente", "Serviço", "Valor", "Status")
tree = ttk.Treeview(frame_tabela, columns=colunas, show="headings", selectmode="browse")

for col in colunas:
    tree.heading(col, text=col.upper())

tree.column("Data/Hora", width=140, anchor="center")
tree.column("Cliente", width=200, anchor="w")
tree.column("Serviço", width=200, anchor="w")
tree.column("Valor", width=100, anchor="e")
tree.column("Status", width=100, anchor="center")

tree.tag_configure("futuro", background="#312e81", foreground="#c7d2fe")
tree.tag_configure("atrasado", background="#7f1d1d", foreground="#fecaca")
tree.tag_configure("concluido", background=COR_CARTAO, foreground=COR_TEXTO)

scroll = ctk.CTkScrollbar(frame_tabela, command=tree.yview, fg_color=COR_CARTAO)
tree.configure(yscrollcommand=scroll.set)

tree.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
scroll.grid(row=0, column=1, sticky="ns", pady=10)

# ============ BOTÕES DE AÇÃO ============
frame_botoes = ctk.CTkFrame(app, fg_color="transparent")
frame_botoes.grid(row=5, column=0, sticky="ew", padx=25, pady=(5, 20))

btn_exportar = ctk.CTkButton(frame_botoes, text="📊 Excel", command=exportar_excel, width=100, height=38, fg_color=COR_PRIMARIA)
btn_exportar.pack(side="left", padx=5)

btn_pdf = ctk.CTkButton(frame_botoes, text="📄 Gerar PDF (Lucro)", command=exportar_pdf, width=150, height=38, fg_color="#4f46e5")
btn_pdf.pack(side="left", padx=5)

btn_concluir = ctk.CTkButton(frame_botoes, text="✅ Marcar Concluído", command=marcar_concluido, width=160, height=38, fg_color=COR_SUCESSO)
btn_concluir.pack(side="left", padx=5)

btn_excluir = ctk.CTkButton(frame_botoes, text="🗑️ Excluir", command=excluir_selecionado, width=120, height=38, fg_color=COR_PERIGO)
btn_excluir.pack(side="right", padx=5)

btn_limpar_mes = ctk.CTkButton(frame_botoes, text="🧹 Limpar Mês", command=lambda: limpar_dados("mes"), width=130, height=38, fg_color=COR_ALERTA)
btn_limpar_mes.pack(side="right", padx=5)

btn_limpar_dia = ctk.CTkButton(frame_botoes, text="🧹 Limpar Dia", command=lambda: limpar_dados("hoje"), width=130, height=38, fg_color="#f97316")
btn_limpar_dia.pack(side="right", padx=5)

carregar_dados()
atualizar_tabela()

app.mainloop()