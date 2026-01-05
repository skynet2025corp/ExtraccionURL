import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import time
import re

def es_url_administrativa(url):
    """
    Identifica si una URL corresponde a un departamento, provincia o distrito
    """
    # Lista de departamentos del Perú
    departamentos = [
        'amazonas', 'ancash', 'apurimac', 'arequipa', 'ayacucho', 'cajamarca',
        'cusco', 'callao', 'huancavelica', 'huanuco', 'ica', 'junin',
        'la-libertad', 'lambayeque', 'lima', 'loreto', 'madre-de-dios',
        'moquegua', 'pasco', 'piura', 'puno', 'san-martin', 'tacna',
        'tumbes', 'ucayali'
    ]
    
    # Convertir URL a minúsculas para comparación
    url_lower = url.lower()
    
    # Patrones para identificar URLs administrativas
    patrones = [
        # Departamentos: /departamento o /departamento/
        r'/(' + '|'.join(departamentos) + r')/?$',
        
        # Provincias: /departamento/provincia-xxx o /departamento/provincias/
        r'/(' + '|'.join(departamentos) + r')/provincia[s]?-',
        r'/(' + '|'.join(departamentos) + r')/provincia[s]/',
        
        # Distritos: /departamento/informacion-xxx/distrito-xxx o /departamento/informacion-xxx/distrito-de-xxx
        r'/(' + '|'.join(departamentos) + r')/informacion-[a-z]+/distrito',
        
        # Distritos alternativos: /departamento/distrito-xxx
        r'/(' + '|'.join(departamentos) + r')/distrito'
    ]
    
    # Verificar si la URL coincide con algún patrón
    for patron in patrones:
        if re.search(patron, url_lower):
            return True
    
    return False

def filtrar_urls_administrativas(urls):
    """
    Filtra un conjunto de URLs para quedarse solo con las administrativas
    """
    return {url for url in urls if es_url_administrativa(url)}

def obtener_urls_directas(url_objetivo):
    """
    Intenta acceder a la URL objetivo y devuelve la URL base accesible
    """
    urls_encontradas = set()
    
    # Asegurarse de que la URL tenga el esquema correcto
    if not url_objetivo.startswith(('http://', 'https://')):
        url_objetivo = 'https://' + url_objetivo
    
    # Intentar con y sin www
    variantes_url = [url_objetivo]
    if 'www.' not in url_objetivo:
        variantes_url.append(url_objetivo.replace('://', '://www.'))
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    print(f"Intentando acceder a: {url_objetivo}")
    
    for url in variantes_url:
        try:
            print(f"Probando: {url}")
            response = requests.head(url, headers=headers, timeout=10, allow_redirects=True)
            
            if response.status_code == 200:
                final_url = response.url.rstrip('/') + '/'  # Normalizar URL
                print(f"Acceso exitoso a: {final_url}")
                urls_encontradas.add(final_url)
                break
        except requests.exceptions.SSLError:
            # Intentar con HTTP si falla HTTPS
            try:
                http_url = url.replace('https://', 'http://')
                print(f"Error SSL, probando con HTTP: {http_url}")
                response = requests.head(http_url, headers=headers, timeout=10, allow_redirects=True)
                if response.status_code == 200:
                    final_url = response.url.rstrip('/') + '/'  # Normalizar URL
                    print(f"Acceso exitoso a: {final_url}")
                    urls_encontradas.add(final_url)
                    break
            except Exception as e:
                print(f"Error al acceder a {http_url}: {e}")
        except Exception as e:
            print(f"Error al acceder a {url}: {e}")
    
    return urls_encontradas

def explorar_sitio(url_base, profundidad_maxima=2):
    """
    Explora recursivamente un sitio web a partir de una URL base
    y devuelve todas las URLs encontradas hasta la profundidad especificada
    """
    urls_encontradas = set()
    urls_por_visitar = set([url_base])
    urls_visitadas = set()
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    while urls_por_visitar and len(urls_visitadas) < 1000:  # Límite de seguridad
        url_actual = urls_por_visitar.pop()
        
        # Evitar visitar la misma URL múltiples veces
        if url_actual in urls_visitadas:
            continue
            
        urls_visitadas.add(url_actual)
        print(f"Explorando: {url_actual} (nivel {len(urls_visitadas)})")
        
        try:
            # Usar HEAD primero para verificar si la URL es accesible
            try:
                head_response = requests.head(url_actual, headers=headers, timeout=10, allow_redirects=True)
                if head_response.status_code != 200:
                    print(f"  Error: Código {head_response.status_code} para {url_actual}")
                    continue
            except Exception as e:
                print(f"  Error en HEAD para {url_actual}: {e}")
                continue
            
            # Si es un archivo (ej: .pdf, .jpg, etc.), saltar
            if any(url_actual.lower().endswith(ext) for ext in ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.zip', '.doc', '.docx', '.xls', '.xlsx']):
                print(f"  Saltando archivo: {url_actual}")
                continue
                
            # Obtener el contenido completo de la página
            response = requests.get(url_actual, headers=headers, timeout=15)
            
            if response.status_code == 200:
                # Agregar la URL a las encontradas
                urls_encontradas.add(url_actual)
                
                # Analizar el contenido HTML
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Obtener todas las URLs de la página
                for link in soup.find_all(['a', 'link'], href=True):
                    href = link['href'].strip()
                    if not href or href.startswith(('javascript:', 'mailto:', 'tel:', '#')):
                        continue
                        
                    # Construir URL completa
                    full_url = urljoin(url_actual, href)
                    parsed_url = urlparse(full_url)
                    
                    # Normalizar la URL (eliminar fragmentos y parámetros de seguimiento comunes)
                    clean_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
                    clean_url = clean_url.rstrip('/')
                    
                    # Verificar si es una URL del mismo dominio
                    if parsed_url.netloc == urlparse(url_base).netloc:
                        # Si no la hemos visitado ni está en la lista por visitar
                        if clean_url not in urls_visitadas and clean_url not in urls_por_visitar:
                            # Si no hemos alcanzado la profundidad máxima
                            if len(urls_visitadas) + len(urls_por_visitar) < (100 * (profundidad_maxima + 1)):
                                urls_por_visitar.add(clean_url)
                
                # Pequeña pausa para no saturar el servidor
                time.sleep(0.5)
                
        except Exception as e:
            print(f"  Error al procesar {url_actual}: {e}")
    
    print(f"\nExploración completada. URLs encontradas: {len(urls_encontradas)}")
    return urls_encontradas

def main():
    # Configuración
    print("=== EXTRACTOR DE SUBDIRECCIONES WEB ===\n")
    
    # Solicitar URL al usuario
    url_objetivo = input("Ingrese la URL del sitio web a analizar (ej: ejemplo.com o https://www.ejemplo.com): ")
    if not url_objetivo:
        url_objetivo = "enperu.org"  # Valor por defecto
    
    profundidad = input("Profundidad de búsqueda (1-5, predeterminado 2): ")
    try:
        profundidad = min(max(int(profundidad), 1), 5) if profundidad.strip() else 2
    except ValueError:
        profundidad = 2
    
    print("\n=== INICIANDO BÚSQUEDA ===")
    
    # Obtener URL base accesible
    urls_directas = obtener_urls_directas(url_objetivo)
    
    if not urls_directas:
        print("\nNo se pudo acceder a la URL proporcionada. Verifique la URL e intente nuevamente.")
        return
    
    url_base = next(iter(urls_directas))  # Tomar la primera URL accesible
    print(f"\nURL base accesible: {url_base}")
    
    print("\n=== EXPLORANDO SITIO WEB ===")
    print(f"Esto puede tomar varios minutos. Profundidad de búsqueda: {profundidad}")
    
    # Explorar el sitio web
    try:
        urls_encontradas = explorar_sitio(url_base, profundidad_maxima=profundidad)
        print(f"\nTotal de URLs encontradas: {len(urls_encontradas)}")
        
        # Filtrar URLs administrativas si el sitio es de Perú
        if 'enperu.org' in url_base or 'peru' in url_base.lower():
            print("\n=== FILTRANDO URLs ADMINISTRATIVAS ===")
            urls_administrativas = filtrar_urls_administrativas(urls_encontradas)
            print(f"URLs administrativas encontradas: {len(urls_administrativas)}")
            
            # Categorizar las URLs administrativas
            departamentos = set()
            provincias = set()
            distritos = set()
            otras = set()
            
            for url in urls_administrativas:
                url_lower = url.lower()
                if re.search(r'/(amazonas|ancash|apurimac|arequipa|ayacucho|cajamarca|cusco|callao|huancavelica|huanuco|ica|junin|la-libertad|lambayeque|lima|loreto|madre-de-dios|moquegua|pasco|piura|puno|san-martin|tacna|tumbes|ucayali)/?$', url_lower):
                    departamentos.add(url)
                elif re.search(r'/informacion-[a-z]+/distrito', url_lower):
                    distritos.add(url)
                elif re.search(r'/provincia', url_lower):
                    provincias.add(url)
                else:
                    otras.add(url)
            
            # Guardar resultados
            dominio = urlparse(url_base).netloc.replace('www.', '')
            archivo_salida = f"urls_{dominio}.txt"
            
            with open(archivo_salida, "w", encoding="utf-8") as f:
                f.write(f"=== RESULTADOS PARA {dominio} ===\n")
                f.write(f"Total de URLs encontradas: {len(urls_encontradas)}\n")
                f.write(f"URLs administrativas: {len(urls_administrativas)}\n\n")
                
                if departamentos:
                    f.write("=== DEPARTAMENTOS ===\n")
                    for url in sorted(departamentos):
                        f.write(f"{url}\n")
                    f.write("\n")
                
                if provincias:
                    f.write("=== PROVINCIAS ===\n")
                    for url in sorted(provincias):
                        f.write(f"{url}\n")
                    f.write("\n")
                
                if distritos:
                    f.write("=== DISTRITOS ===\n")
                    for url in sorted(distritos):
                        f.write(f"{url}\n")
                    f.write("\n")
                
                if otras:
                    f.write("=== OTRAS URLs ADMINISTRATIVAS ===\n")
                    for url in sorted(otras):
                        f.write(f"{url}\n")
        else:
            # Para sitios que no son de Perú, guardar todas las URLs encontradas
            dominio = urlparse(url_base).netloc.replace('www.', '')
            archivo_salida = f"urls_{dominio}.txt"
            
            with open(archivo_salida, "w", encoding="utf-8") as f:
                f.write(f"=== TODAS LAS URLs ENCONTRADAS EN {dominio} ===\n\n")
                for url in sorted(urls_encontradas):
                    f.write(f"{url}\n")
        
        print(f"\n=== RESULTADOS GUARDADOS ===")
        print(f"Los resultados se han guardado en: {archivo_salida}")
        
    except KeyboardInterrupt:
        print("\n\nBúsqueda interrumpida por el usuario.")
    except Exception as e:
        print(f"\nError durante la exploración: {e}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nPrograma interrumpido por el usuario.")
    except Exception as e:
        print(f"\nError inesperado: {e}")
    
    input("\nPresione Enter para salir...")