from flask import Flask, request, jsonify
from urllib.parse import urlparse
import os

# Import functions from existing CLI module
from main import obtener_urls_directas, explorar_sitio, filtrar_urls_administrativas

app = Flask(__name__)

@app.route('/extract', methods=['POST'])
def extract():
    data = request.get_json(silent=True) or {}
    url = data.get('url')
    try:
        depth = int(data.get('depth', 2))
    except Exception:
        depth = 2

    if not url:
        return jsonify({'error': "Missing 'url' parameter"}), 400

    # Obtener URL base accesible
    urls_directas = obtener_urls_directas(url)
    if not urls_directas:
        return jsonify({'error': 'Could not access target URL'}), 502

    url_base = next(iter(urls_directas))

    try:
        urls_encontradas = explorar_sitio(url_base, profundidad_maxima=depth)
    except Exception as e:
        return jsonify({'error': 'Error exploring site', 'details': str(e)}), 500

    is_peru = 'enperu.org' in url_base or 'peru' in url_base.lower()
    dominio = urlparse(url_base).netloc.replace('www.', '')

    if is_peru:
        urls_admin = filtrar_urls_administrativas(urls_encontradas)
        filename = f"urls_administrativas_{dominio}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"=== RESULTADOS PARA {dominio} ===\n")
            f.write(f"Total de URLs encontradas: {len(urls_encontradas)}\n")
            f.write(f"URLs administrativas: {len(urls_admin)}\n\n")
            for u in sorted(urls_admin):
                f.write(u + "\n")

        return jsonify({
            'status': 'ok',
            'domain': dominio,
            'found': len(urls_encontradas),
            'administrative': len(urls_admin),
            'file': filename
        }), 200

    else:
        filename = f"urls_{dominio}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"=== TODAS LAS URLs ENCONTRADAS EN {dominio} ===\n\n")
            for u in sorted(urls_encontradas):
                f.write(u + "\n")

        return jsonify({
            'status': 'ok',
            'domain': dominio,
            'found': len(urls_encontradas),
            'file': filename
        }), 200


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
