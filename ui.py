# ui.py
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import threading
from pathlib import Path

# Reutilize sua função existente
from sistema_de_download_nf_ce.distribuicao.soap import distribuicao_dfe_por_chave
from sistema_de_download_nf_ce.distribuicao.utils import salvar_xml

class NFeDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Download NF-e por Chave")
        self.root.geometry("600x500")
        
        # Variáveis
        self.cert_path = tk.StringVar()
        self.cnpj = tk.StringVar()
        self.cert_password = tk.StringVar()
        
        self.create_widgets()
    
    def create_widgets(self):
        # Certificado
        tk.Label(self.root, text="Certificado (.pfx):").pack(anchor="w", padx=10, pady=(10,0))
        cert_frame = tk.Frame(self.root)
        cert_frame.pack(fill="x", padx=10)
        tk.Entry(cert_frame, textvariable=self.cert_path, state="readonly").pack(side="left", fill="x", expand=True)
        tk.Button(cert_frame, text="Selecionar", command=self.select_cert).pack(side="right")
        
        # Senha do certificado
        tk.Label(self.root, text="Senha do Certificado:").pack(anchor="w", padx=10, pady=(10,0))
        tk.Entry(self.root, textvariable=self.cert_password, show="*").pack(fill="x", padx=10)
        
        # CNPJ
        tk.Label(self.root, text="CNPJ Interessado:").pack(anchor="w", padx=10, pady=(10,0))
        tk.Entry(self.root, textvariable=self.cnpj).pack(fill="x", padx=10)
        
        # Chaves
        tk.Label(self.root, text="Chaves de Acesso (uma por linha):").pack(anchor="w", padx=10, pady=(10,0))
        self.chaves_text = scrolledtext.ScrolledText(self.root, height=8)
        self.chaves_text.pack(fill="both", padx=10, pady=(0,10), expand=True)
        
        # Botão
        tk.Button(self.root, text="Baixar XMLs", command=self.start_download, bg="#007bff", fg="white").pack(pady=10)
    
    def select_cert(self):
        path = filedialog.askopenfilename(filetypes=[("Arquivos PFX", "*.pfx")])
        if path:
            self.cert_path.set(path)
    
    def start_download(self):
        if not all([self.cert_path.get(), self.cert_password.get(), self.cnpj.get().strip()]):
            messagebox.showerror("Erro", "Preencha todos os campos!")
            return
        
        chaves = self.chaves_text.get("1.0", tk.END).strip().splitlines()
        chaves = [c.strip() for c in chaves if c.strip()]
        
        if not chaves:
            messagebox.showerror("Erro", "Insira pelo menos uma chave!")
            return
        
        # Executa em segundo plano para não travar a UI
        threading.Thread(target=self.download_files, args=(chaves,), daemon=True).start()
    
    def download_files(self, chaves):
        self.root.after(0, lambda: messagebox.showinfo("Iniciado", f"Iniciando download de {len(chaves)} chaves..."))
        
        sucesso = 0
        for i, chave in enumerate(chaves, 1):
            if len(chave) != 44 or not chave.isdigit():
                print(f"⚠️ Chave inválida: {chave}")
                continue
            
            xml_bytes = distribuicao_dfe_por_chave(
                chave=chave,
                cnpj_interessado=self.cnpj.get().strip(),
                cert_pfx=self.cert_path.get(),
                cert_password=self.cert_password.get()
            )
            
            if xml_bytes:
                salvar_xml(chave, xml_bytes, "xmls_baixados")
                sucesso += 1
                print(f"✅ {chave}.xml salvo")
            else:
                print(f"❌ Falha ao baixar {chave}")
            
            # Respeita limite da SEFAZ
            if i < len(chaves):
                import time
                time.sleep(6)
        
        self.root.after(0, lambda: messagebox.showinfo("Concluído", f"Download concluído! {sucesso}/{len(chaves)} arquivos salvos em 'xmls_baixados'"))

if __name__ == "__main__":
    root = tk.Tk()
    app = NFeDownloaderApp(root)
    root.mainloop()