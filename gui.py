import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from urllib.parse import urlparse
import threading
import os

class URLExtractorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Extractor de URLs")
        self.root.geometry("600x400")
        self.root.resizable(True, True)
        
        # Variables
        self.url_var = tk.StringVar()
        self.progress_var = tk.DoubleVar()
        self.status_var = tk.StringVar(value="Listo")
        self.download_button_state = tk.StringVar(value="disabled")
        self.output_file = ""
        
        # Configurar el estilo
        self.setup_styles()
        
        # Crear widgets
        self.create_widgets()
    
    def setup_styles(self):
        style = ttk.Style()
        style.configure("TLabel", padding=5)
        style.configure("TButton", padding=5)
        style.configure("TEntry", padding=5)
        
    def create_widgets(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        title_label = ttk.Label(
            main_frame, 
            text="Extractor de URLs", 
            font=("Helvetica", 16, "bold")
        )
        title_label.pack(pady=10)
        
        # Frame de entrada
        input_frame = ttk.LabelFrame(main_frame, text="Configuración", padding=10)
        input_frame.pack(fill=tk.X, pady=10)
        
        # Campo de URL
        url_frame = ttk.Frame(input_frame)
        url_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(url_frame, text="URL del sitio:").pack(side=tk.LEFT)
        
        self.url_entry = ttk.Entry(
            url_frame, 
            textvariable=self.url_var, 
            width=50
        )
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Profundidad
        depth_frame = ttk.Frame(input_frame)
        depth_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(depth_frame, text="Profundidad (1-5):").pack(side=tk.LEFT)
        
        self.depth_spinbox = ttk.Spinbox(
            depth_frame, 
            from_=1, 
            to=5, 
            width=5
        )
        self.depth_spinbox.set("2")
        self.depth_spinbox.pack(side=tk.LEFT, padx=5)
        
        # Botones
        button_frame = ttk.Frame(input_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        self.start_button = ttk.Button(
            button_frame, 
            text="Iniciar Extracción", 
            command=self.start_extraction,
            style="Accent.TButton"
        )
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.download_button = ttk.Button(
            button_frame, 
            text="Descargar Resultados", 
            command=self.download_results,
            state="disabled"
        )
        self.download_button.pack(side=tk.LEFT, padx=5)
        
        # Barra de progreso
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=10)
        
        self.progress = ttk.Progressbar(
            progress_frame, 
            variable=self.progress_var, 
            maximum=100,
            mode='determinate'
        )
        self.progress.pack(fill=tk.X, pady=5)
        
        # Estado
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(status_frame, text="Estado:").pack(side=tk.LEFT)
        
        self.status_label = ttk.Label(
            status_frame, 
            textvariable=self.status_var,
            foreground="blue"
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Consola de salida
        console_frame = ttk.LabelFrame(main_frame, text="Registro", padding=5)
        console_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.console = tk.Text(
            console_frame, 
            height=10, 
            wrap=tk.WORD,
            state='disabled'
        )
        
        scrollbar = ttk.Scrollbar(console_frame, command=self.console.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.console.configure(yscrollcommand=scrollbar.set)
        self.console.pack(fill=tk.BOTH, expand=True)
    
    def log(self, message):
        """Agrega un mensaje a la consola de manera segura para hilos"""
        def _log():
            self.console.configure(state='normal')
            self.console.insert(tk.END, message + "\n")
            self.console.see(tk.END)
            self.console.configure(state='disabled')
        self.root.after(0, _log)
    
    def update_progress(self, value):
        """Actualiza la barra de progreso de manera segura para hilos"""
        def _update():
            self.progress_var.set(value)
        self.root.after(0, _update)
    
    def update_status(self, message, color="black"):
        """Actualiza el mensaje de estado de manera segura para hilos"""
        def _update():
            self.status_var.set(message)
            self.status_label.config(foreground=color)
        self.root.after(0, _update)
    
    def toggle_ui(self, extracting):
        """Habilita/deshabilita controles durante la extracción"""
        def _toggle():
            state = "disabled" if extracting else "normal"
            self.url_entry.config(state=state)
            self.depth_spinbox.config(state=state)
            self.start_button.config(state=state)
        self.root.after(0, _toggle)
    
    def start_extraction(self):
        """Inicia el proceso de extracción en un hilo separado"""
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Error", "Por favor ingrese una URL válida")
            return
        
        try:
            depth = int(self.depth_spinbox.get())
            if depth < 1 or depth > 5:
                raise ValueError("La profundidad debe estar entre 1 y 5")
        except ValueError as e:
            messagebox.showerror("Error", "La profundidad debe ser un número entre 1 y 5")
            return
        
        # Limpiar consola
        self.console.configure(state='normal')
        self.console.delete(1.0, tk.END)
        self.console.configure(state='disabled')
        
        # Actualizar UI
        self.toggle_ui(True)
        self.update_progress(0)
        self.update_status("Iniciando extracción...", "blue")
        self.download_button.config(state="disabled")
        
        # Iniciar extracción en un hilo separado
        self.extraction_thread = threading.Thread(
            target=self.run_extraction,
            args=(url, depth),
            daemon=True
        )
        self.extraction_thread.start()
        
        # Verificar el estado del hilo periódicamente
        self.check_thread_status()
    
    def check_thread_status(self):
        """Verifica el estado del hilo de extracción"""
        if self.extraction_thread.is_alive():
            # Programar la próxima verificación
            self.root.after(100, self.check_thread_status)
        else:
            # La extracción ha terminado
            self.toggle_ui(False)
            self.update_status("Extracción completada", "green")
            
            # Habilitar botón de descarga si hay resultados
            if hasattr(self, 'output_file') and self.output_file:
                self.download_button.config(state="normal")
    
    def run_extraction(self, url, depth):
        """Ejecuta la extracción de URLs"""
        try:
            # Importar aquí para evitar problemas de importación circular
            from urllib.parse import urlparse
            import time
            from main import explorar_sitio, filtrar_urls_administrativas
            
            self.log(f"Iniciando extracción de: {url}")
            self.log(f"Profundidad de búsqueda: {depth}")
            
            # Actualizar estado inicial
            self.update_status("Conectando al sitio...", "blue")
            self.update_progress(10)
            
            # Obtener URLs directas
            from main import obtener_urls_directas
            urls_directas = obtener_urls_directas(url)
            
            if not urls_directas:
                self.update_status("No se pudo conectar al sitio", "red")
                self.log("Error: No se pudo conectar al sitio")
                return
                
            url_base = next(iter(urls_directas))
            self.log(f"Conexión exitosa a: {url_base}")
            self.update_status("Explorando el sitio...", "blue")
            self.update_progress(30)
            
            # Realizar la exploración del sitio
            self.log("\nIniciando exploración del sitio...")
            urls_encontradas = explorar_sitio(url_base, profundidad_maxima=depth)
            
            if not urls_encontradas:
                self.update_status("No se encontraron URLs", "orange")
                self.log("No se encontraron URLs en el sitio")
                return
                
            self.log(f"\nTotal de URLs encontradas: {len(urls_encontradas)}")
            
            # Filtrar URLs administrativas si es un sitio peruano
            if 'enperu.org' in url or 'peru' in url.lower():
                self.log("\nFiltrando URLs administrativas...")
                urls_administrativas = filtrar_urls_administrativas(urls_encontradas)
                self.log(f"URLs administrativas encontradas: {len(urls_administrativas)}")
                
                # Guardar resultados
                dominio = urlparse(url_base).netloc.replace('www.', '')
                self.output_file = f"urls_administrativas_{dominio}.txt"
                
                with open(self.output_file, 'w', encoding='utf-8') as f:
                    f.write(f"=== RESULTADOS PARA {dominio} ===\n")
                    f.write(f"Total de URLs encontradas: {len(urls_encontradas)}\n")
                    f.write(f"URLs administrativas: {len(urls_administrativas)}\n\n")
                    
                    # Escribir todas las URLs administrativas
                    for url in sorted(urls_administrativas):
                        f.write(f"{url}\n")
            else:
                # Para sitios que no son de Perú, guardar todas las URLs encontradas
                dominio = urlparse(url_base).netloc.replace('www.', '')
                self.output_file = f"urls_{dominio}.txt"
                
                with open(self.output_file, 'w', encoding='utf-8') as f:
                    f.write(f"=== TODAS LAS URLs ENCONTRADAS EN {dominio} ===\n\n")
                    for url in sorted(urls_encontradas):
                        f.write(f"{url}\n")
            
            # Actualizar interfaz
            self.update_status("Extracción completada", "green")
            self.update_progress(100)
            self.log(f"\n¡Extracción completada con éxito!")
            self.log(f"Resultados guardados en: {self.output_file}")
            
        except Exception as e:
            import traceback
            error_msg = f"Error durante la extracción: {str(e)}\n\n{traceback.format_exc()}"
            self.log(f"\n{error_msg}")
            self.update_status(f"Error: {str(e)}", "red")
    
    def download_results(self):
        """Permite al usuario guardar los resultados en una ubicación específica"""
        if not hasattr(self, 'output_file') or not self.output_file:
            self.root.after(0, lambda: messagebox.showinfo("Información", "No hay resultados para guardar"))
            return
        
        # Obtener el nombre del archivo base
        base_name = os.path.basename(self.output_file)
        
        # Mostrar diálogo para guardar archivo
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")],
            initialfile=base_name
        )
        
        if file_path:
            def _save_file():
                try:
                    import shutil
                    shutil.copy2(self.output_file, file_path)
                    messagebox.showinfo("Éxito", f"Archivo guardado en:\n{file_path}")
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo guardar el archivo:\n{str(e)}")
            
            # Ejecutar en el hilo principal
            self.root.after(0, _save_file)

def main():
    # Crear la ventana principal
    try:
        from ttkthemes import ThemedTk
        root = ThemedTk(theme="arc")
    except ImportError:
        # Si no está instalado ttkthemes, usar Tk normal
        root = tk.Tk()
    
    # Configuración básica de la ventana
    root.title("Extractor de URLs")
    
    # Configurar el ícono (opcional)
    try:
        root.iconbitmap("icon.ico")  # Asegúrate de tener un archivo icon.ico en el mismo directorio
    except:
        pass
    
    # Configurar tamaño y posición de la ventana
    window_width = 800
    window_height = 600
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    # Configurar el estilo
    style = ttk.Style()
    style.configure("TLabel", padding=5)
    style.configure("TButton", padding=5)
    
    # Crear la aplicación
    app = URLExtractorApp(root)
    
    # Manejar el cierre de la ventana
    def on_closing():
        if messagebox.askokcancel("Salir", "¿Estás seguro de que quieres salir?"):
            root.quit()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Iniciar el bucle principal
    try:
        root.mainloop()
    except KeyboardInterrupt:
        root.quit()

if __name__ == "__main__":
    main()
