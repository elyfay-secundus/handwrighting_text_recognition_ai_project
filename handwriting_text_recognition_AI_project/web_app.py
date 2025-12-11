import os
import sys
from pathlib import Path
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import base64
from io import BytesIO
from PIL import Image

src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from text_recognizer import recognize_text
from model_loader import model_loader
from multi_ocr import recognize_multi
from accuracy_metrics import get_detailed_metrics, compare_engines

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = Path(__file__).parent / 'uploads'
app.config['UPLOAD_FOLDER'].mkdir(exist_ok=True)

print("\n" + "="*60)
print("⏳ PRELOADING AI MODEL...")
print("="*60)
print("This takes ~90 seconds but makes ALL requests instant!")
print("Please wait...")
print()

import threading

def preload_model():
    try:
        model_loader.load()
        print("\n" + "="*60)
        print("✅ MODEL READY! All requests will now be INSTANT (<0.2s)")
        print("="*60 + "\n")
    except Exception as e:
        print(f"\n⚠️  Model preload failed: {e}")
        print("Model will load on first request instead.\n")

preload_thread = threading.Thread(target=preload_model, daemon=True)
preload_thread.start()

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'webp'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/recognize', methods=['POST'])
def recognize():
    try:
        if 'file' not in request.files:
            url = request.form.get('url', '').strip()
            if url:
                text = recognize_text(url)
                return jsonify({
                    'success': True,
                    'text': text,
                    'message': 'Text recognized successfully!'
                })
            return jsonify({
                'success': False,
                'error': 'No file or URL provided'
            }), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400

        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': f'Invalid file type. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400

        filename = secure_filename(file.filename)
        filepath = app.config['UPLOAD_FOLDER'] / filename
        file.save(filepath)

        try:
            text = recognize_text(str(filepath))

            with Image.open(filepath) as img:
                img.thumbnail((800, 600))
                buffered = BytesIO()
                img.save(buffered, format="PNG")
                img_str = base64.b64encode(buffered.getvalue()).decode()

            filepath.unlink()

            return jsonify({
                'success': True,
                'text': text,
                'image': f'data:image/png;base64,{img_str}',
                'message': 'Text recognized successfully!'
            })

        except Exception as e:
            if filepath.exists():
                filepath.unlink()
            raise e

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})


@app.route('/model_status')
def model_status():
    is_ready = model_loader.is_loaded()
    device = str(model_loader.get_device())
    return jsonify({
        'ready': is_ready,
        'device': device,
        'message': 'Model ready - requests will be instant!' if is_ready else 'Model loading... please wait'
    })


@app.route('/recognize_batch', methods=['POST'])
def recognize_batch_endpoint():
    try:
        if 'files' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No files provided'
            }), 400

        files = request.files.getlist('files')
        if not files or len(files) == 0:
            return jsonify({
                'success': False,
                'error': 'No files selected'
            }), 400

        results = []
        for file in files:
            if file.filename == '':
                continue

            if not allowed_file(file.filename):
                results.append({
                    'filename': file.filename,
                    'success': False,
                    'error': 'Invalid file type'
                })
                continue

            filename = secure_filename(file.filename)
            filepath = app.config['UPLOAD_FOLDER'] / filename

            try:
                file.save(filepath)
                text = recognize_text(str(filepath))

                with Image.open(filepath) as img:
                    img.thumbnail((400, 300))
                    buffered = BytesIO()
                    img.save(buffered, format="PNG")
                    img_str = base64.b64encode(buffered.getvalue()).decode()

                filepath.unlink()

                results.append({
                    'filename': file.filename,
                    'success': True,
                    'text': text,
                    'image': f'data:image/png;base64,{img_str}'
                })

            except Exception as e:
                if filepath.exists():
                    filepath.unlink()
                results.append({
                    'filename': file.filename,
                    'success': False,
                    'error': str(e)
                })

        return jsonify({
            'success': True,
            'results': results,
            'message': f'Processed {len(results)} images'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/recognize_multi', methods=['POST'])
def recognize_multi_endpoint():
    try:
        if 'file' not in request.files:
            url = request.form.get('url', '').strip()
            if url:
                results = recognize_multi(url, engines=['trocr', 'easyocr'])
                return jsonify({
                    'success': True,
                    'results': results,
                    'message': 'Processed with multiple engines'
                })
            return jsonify({
                'success': False,
                'error': 'No file or URL provided'
            }), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400

        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': f'Invalid file type'
            }), 400

        filename = secure_filename(file.filename)
        filepath = app.config['UPLOAD_FOLDER'] / filename
        file.save(filepath)

        try:
            results = recognize_multi(str(filepath), engines=['trocr', 'easyocr'])

            with Image.open(filepath) as img:
                img.thumbnail((800, 600))
                buffered = BytesIO()
                img.save(buffered, format="PNG")
                img_str = base64.b64encode(buffered.getvalue()).decode()

            filepath.unlink()

            return jsonify({
                'success': True,
                'results': results,
                'image': f'data:image/png;base64,{img_str}',
                'message': 'Processed with multiple engines'
            })

        except Exception as e:
            if filepath.exists():
                filepath.unlink()
            raise e

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/calculate_accuracy', methods=['POST'])
def calculate_accuracy_endpoint():
    """
    Calculate accuracy metrics by comparing OCR result with ground truth.
    Expects JSON: { "ground_truth": "...", "predicted": "..." }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400

        ground_truth = data.get('ground_truth', '').strip()
        predicted = data.get('predicted', '').strip()

        if not ground_truth:
            return jsonify({
                'success': False,
                'error': 'Ground truth text is required'
            }), 400

        metrics = get_detailed_metrics(ground_truth, predicted)

        return jsonify({
            'success': True,
            'metrics': metrics,
            'message': 'Accuracy calculated successfully'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/recognize_with_accuracy', methods=['POST'])
def recognize_with_accuracy():
    """
    Recognize text and optionally calculate accuracy if ground truth is provided.
    """
    try:
        ground_truth = request.form.get('ground_truth', '').strip()

        if 'file' not in request.files:
            url = request.form.get('url', '').strip()
            if url:
                text = recognize_text(url)
                response_data = {
                    'success': True,
                    'text': text,
                    'message': 'Text recognized successfully!'
                }

                if ground_truth:
                    metrics = get_detailed_metrics(ground_truth, text)
                    response_data['accuracy_metrics'] = metrics

                return jsonify(response_data)

            return jsonify({
                'success': False,
                'error': 'No file or URL provided'
            }), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400

        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': f'Invalid file type. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400

        filename = secure_filename(file.filename)
        filepath = app.config['UPLOAD_FOLDER'] / filename
        file.save(filepath)

        try:
            text = recognize_text(str(filepath))

            with Image.open(filepath) as img:
                img.thumbnail((800, 600))
                buffered = BytesIO()
                img.save(buffered, format="PNG")
                img_str = base64.b64encode(buffered.getvalue()).decode()

            filepath.unlink()

            response_data = {
                'success': True,
                'text': text,
                'image': f'data:image/png;base64,{img_str}',
                'message': 'Text recognized successfully!'
            }

            if ground_truth:
                metrics = get_detailed_metrics(ground_truth, text)
                response_data['accuracy_metrics'] = metrics

            return jsonify(response_data)

        except Exception as e:
            if filepath.exists():
                filepath.unlink()
            raise e

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/recognize_multi_with_accuracy', methods=['POST'])
def recognize_multi_with_accuracy():
    """
    Recognize text with multiple engines and calculate accuracy if ground truth is provided.
    """
    try:
        ground_truth = request.form.get('ground_truth', '').strip()

        if 'file' not in request.files:
            url = request.form.get('url', '').strip()
            if url:
                results = recognize_multi(url, engines=['trocr', 'easyocr'])

                if ground_truth:
                    results = compare_engines(ground_truth, results)

                return jsonify({
                    'success': True,
                    'results': results,
                    'ground_truth': ground_truth if ground_truth else None,
                    'message': 'Processed with multiple engines'
                })

            return jsonify({
                'success': False,
                'error': 'No file or URL provided'
            }), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400

        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': f'Invalid file type'
            }), 400

        filename = secure_filename(file.filename)
        filepath = app.config['UPLOAD_FOLDER'] / filename
        file.save(filepath)

        try:
            results = recognize_multi(str(filepath), engines=['trocr', 'easyocr'])

            if ground_truth:
                results = compare_engines(ground_truth, results)

            with Image.open(filepath) as img:
                img.thumbnail((800, 600))
                buffered = BytesIO()
                img.save(buffered, format="PNG")
                img_str = base64.b64encode(buffered.getvalue()).decode()

            filepath.unlink()

            return jsonify({
                'success': True,
                'results': results,
                'ground_truth': ground_truth if ground_truth else None,
                'image': f'data:image/png;base64,{img_str}',
                'message': 'Processed with multiple engines'
            })

        except Exception as e:
            if filepath.exists():
                filepath.unlink()
            raise e

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    print("\n" + "="*60)
    print("   HANDWRITTEN TEXT RECOGNITION - WEB APP")
    print("="*60)
    print("\n🌐 Starting web server...")
    print("📱 Open your browser and go to:")
    print("\n   http://localhost:5002")
    print("\n💡 Press Ctrl+C to stop the server")
    print("="*60 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5002)
