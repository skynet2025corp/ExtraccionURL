from flask import Flask, request, jsonify, render_template, send_from_directory
from urllib.parse import urlparse
import os
import threading
import uuid
import time

# Import functions from existing CLI module
from main import obtener_urls_directas, explorar_sitio, filtrar_urls_administrativas

app = Flask(__name__, static_folder="static", template_folder="templates")

# Simple in-memory job store. For production use persistent queue (Redis, RQ, Celery, etc.)
jobs = {}
jobs_lock = threading.Lock()


def process_job(job_id, url, depth):
    with jobs_lock:
        jobs[job_id]['status'] = 'running'
        jobs[job_id]['message'] = 'Connecting to target...'

    try:
        urls_directas = obtener_urls_directas(url)
        if not urls_directas:
            with jobs_lock:
                jobs[job_id].update({'status': 'error', 'message': 'Could not access target URL'})
            return

        url_base = next(iter(urls_directas))
        with jobs_lock:
            jobs[job_id].update({'message': f'Exploring {url_base}...', 'domain': urlparse(url_base).netloc.replace('www.', '')})

        urls_encontradas = explorar_sitio(url_base, profundidad_maxima=depth)

        is_peru = 'enperu.org' in url_base or 'peru' in url_base.lower()
        dominio = urlparse(url_base).netloc.replace('www.', '')

        if is_peru:
            urls_admin = filtrar_urls_administrativas(urls_encontradas)
            departamentos = set()
            provincias = set()
            distritos = set()
            otras = set()

            for u in urls_admin:
                u_low = u.lower()
                if any(u_low.endswith(f'/{d}') or u_low.endswith(f'/{d}/') for d in ['amazonas','ancash','apurimac','arequipa','ayacucho','cajamarca','cusco','callao','huancavelica','huanuco','ica','junin','la-libertad','lambayeque','lima','loreto','madre-de-dios','moquegua','pasco','piura','puno','san-martin','tacna','tumbes','ucayali']):
                    departamentos.add(u)
                elif 'informacion-' in u_low and '/distrito' in u_low:
                    distritos.add(u)
                elif '/provincia' in u_low:
                    provincias.add(u)
                else:
                    otras.add(u)

            filename = f"urls_administrativas_{dominio}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"=== RESULTADOS PARA {dominio} ===\n")
                f.write(f"Total de URLs encontradas: {len(urls_encontradas)}\n")
                f.write(f"URLs administrativas: {len(urls_admin)}\n\n")
                if departamentos:
                    f.write('=== DEPARTAMENTOS ===\n')
                    for x in sorted(departamentos):
                        f.write(x + '\n')
                    f.write('\n')
                if provincias:
                    f.write('=== PROVINCIAS ===\n')
                    for x in sorted(provincias):
                        f.write(x + '\n')
                    f.write('\n')
                if distritos:
                    f.write('=== DISTRITOS ===\n')
                    for x in sorted(distritos):
                        f.write(x + '\n')
                    f.write('\n')
                if otras:
                    f.write('=== OTRAS URLs ADMINISTRATIVAS ===\n')
                    for x in sorted(otras):
                        f.write(x + '\n')

            with jobs_lock:
                jobs[job_id].update({
                    'status': 'done',
                    'message': 'Completed',
                    'file': filename,
                    'domain': dominio,
                    'found': len(urls_encontradas),
                    'administrative': len(urls_admin),
                    'departamentos': sorted(departamentos),
                    'provincias': sorted(provincias),
                    'distritos': sorted(distritos),
                    'otras': sorted(otras),
                })
        else:
            filename = f"urls_{dominio}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"=== TODAS LAS URLs ENCONTRADAS EN {dominio} ===\n\n")
                for u in sorted(urls_encontradas):
                    f.write(u + '\n')

            with jobs_lock:
                jobs[job_id].update({
                    'status': 'done',
                    'message': 'Completed',
                    'file': filename,
                    'domain': dominio,
                    'found': len(urls_encontradas),
                    'urls': sorted(urls_encontradas),
                })

    except Exception as e:
        with jobs_lock:
            jobs[job_id].update({'status': 'error', 'message': str(e)})


@app.route('/')
def index():
    return render_template('index.html')


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

    job_id = uuid.uuid4().hex
    with jobs_lock:
        jobs[job_id] = {'status': 'queued', 'message': 'Queued', 'created_at': time.time()}

    thread = threading.Thread(target=process_job, args=(job_id, url, depth), daemon=True)
    thread.start()

    return jsonify({'job_id': job_id, 'status_url': f'/status/{job_id}', 'result_url': f'/result/{job_id}'}), 202


@app.route('/status/<job_id>')
def status(job_id):
    with jobs_lock:
        job = jobs.get(job_id)
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        return jsonify(job)


@app.route('/result/<job_id>')
def result(job_id):
    with jobs_lock:
        job = jobs.get(job_id)
        if not job:
            return "Not found", 404
        if job.get('status') != 'done' or 'file' not in job:
            return "Not ready", 409
        filename = job['file']
    directory = os.getcwd()
    return send_from_directory(directory, filename, as_attachment=True)


@app.route('/download/<path:filename>')
def download(filename):
    # Backwards-compatible download endpoint
    if not filename.startswith('urls'):
        return "Not allowed", 403
    directory = os.getcwd()
    return send_from_directory(directory, filename, as_attachment=True)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
