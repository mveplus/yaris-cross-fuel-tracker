import os
from flask import Flask, request, jsonify, render_template, send_file
from werkzeug.utils import secure_filename
import json
import csv
from datetime import datetime
import shutil

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

DATA_FILE = os.path.join(BASE_DIR, 'data.json')

def load_data(file_path):
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_data(data, file_path):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

#@app.route('/')
#def index():
#    data = load_data(DATA_FILE)
#    current_datetime = datetime.now().strftime('%y-%m-%dT%H:%M')
#    return render_template('index.html', current_datetime=current_datetime, entries=data)

# Add your add_entry, delete_entries, edit_entry, export_data, import_data, restore_backup, get_summary functions here...

#if __name__ == '__main__':
#    app.run(debug=True)

def load_backup():
    try:
        with open(BACKUP_FILE, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return []

def calculate_total_fuel(data):
    return sum(entry['fuel'] for entry in data)

def calculate_mpg(last_entry, new_entry):
    distance = new_entry['odometer'] - last_entry['odometer']
    gallons = new_entry['fuel'] * 0.219969  # convert liters to imperial gallons
    mpg = distance / gallons if gallons != 0 else 0
    return round(mpg, 2)  # Round MPG to two decimal places

def calculate_predicted_mpg(data):
    if not data or len(data) < 2:
        return 0
    total_distance = 0
    total_gallons = 0
    for i in range(1, len(data)):
        distance = data[i]['odometer'] - data[i-1]['odometer']
        gallons = data[i]['fuel'] * 0.219969  # convert liters to imperial gallons
        total_distance += distance
        total_gallons += gallons
    predicted_mpg = total_distance / total_gallons if total_gallons != 0 else 0
    return round(predicted_mpg, 2)  # Round predicted MPG to two decimal places

@app.route('/')
def index():
    data = load_data(DATA_FILE)
    current_datetime = datetime.now().strftime('%y-%m-%dT%H:%M')
    return render_template('index.html', current_datetime=current_datetime, entries=data)

#@app.route('/')
#def index():
#    data = load_data()
#    current_datetime = datetime.now().strftime('%y-%m-%dT%H:%M')
#    return render_template('index.html', current_datetime=current_datetime, entries=data)

@app.route('/add', methods=['POST'])
def add_entry():
    data = load_data()
    date = request.form.get('date') or datetime.now().strftime('%y-%m-%d %H:%M')  # Auto fill with current date and time

    fuel_price = request.form['fuel_price']
    fuel_price = float(fuel_price) if '.' in fuel_price else int(fuel_price) / 1000  # Convert to decimal if needed

    new_entry = {
        'date': date,
        'odometer': round(float(request.form['odometer']), 1),  # Accept floating but round to 1 decimal digit
        'fuel_price': fuel_price,
        'fuel': float(request.form['fuel']),
        'total_fuel_price': round(fuel_price * float(request.form['fuel']), 2)
    }

    if data:
        last_entry = data[-1]
        new_entry['mpg'] = calculate_mpg(last_entry, new_entry)
    else:
        new_entry['mpg'] = 0

    data.append(new_entry)
    total_fuel = calculate_total_fuel(data)
    predicted_mpg = calculate_predicted_mpg(data)
    new_entry['total_fuel'] = total_fuel
    new_entry['predicted_mpg'] = predicted_mpg
    save_data(data)
    return jsonify(new_entry)

@app.route('/delete', methods=['POST'])
def delete_entries():
    data = load_data()
    indices = request.json.get('indices', [])
    if indices:
        for index in sorted(indices, reverse=True):
            if 0 <= index < len(data):
                del data[index]
        save_data(data)
        return jsonify({'success': True})
    return jsonify({'success': False}), 404

@app.route('/edit/<int:index>', methods=['POST'])
def edit_entry(index):
    data = load_data()
    if 0 <= index < len(data):
        date = request.form.get('date') or datetime.now().strftime('%y-%m-%d %H:%M')  # Auto fill with current date and time if not provided

        fuel_price = request.form['fuel_price']
        fuel_price = float(fuel_price) if '.' in fuel_price else int(fuel_price) / 1000  # Convert to decimal if needed

        entry = {
            'date': date,
            'odometer': round(float(request.form['odometer']), 1),  # Accept floating but round to 1 decimal digit
            'fuel_price': fuel_price,
            'fuel': float(request.form['fuel']),
            'total_fuel_price': round(fuel_price * float(request.form['fuel']), 2)
        }

        if index > 0:
            last_entry = data[index - 1]
            entry['mpg'] = calculate_mpg(last_entry, entry)
        else:
            entry['mpg'] = 0

        data[index] = entry
        total_fuel = calculate_total_fuel(data)
        predicted_mpg = calculate_predicted_mpg(data)
        entry['total_fuel'] = total_fuel
        entry['predicted_mpg'] = predicted_mpg
        save_data(data)
        return jsonify({'success': True})
    return jsonify({'success': False}), 404

@app.route('/export')
def export_data():
    data = load_data()
    csv_file = os.path.join(BASE_DIR, 'data.csv')
    with open(csv_file, 'w', newline='') as csvfile:
        fieldnames = ['date', 'odometer', 'fuel_price', 'fuel', 'total_fuel_price', 'mpg']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for entry in data:
            writer.writerow({
                'date': entry['date'],
                'odometer': entry['odometer'],
                'fuel_price': entry['fuel_price'],
                'fuel': entry['fuel'],
                'total_fuel_price': entry['total_fuel_price'],
                'mpg': entry['mpg']
            })

    return send_file(csv_file, as_attachment=True)

@app.route('/import', methods=['POST'])
def import_data():
    file = request.files['file']
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)  # Save the uploaded file to a secure location

        data = load_data()
        with open(filepath, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            imported_data = []
            for row in reader:
                entry = {
                    'date': row['date'],
                    'odometer': round(float(row['odometer']), 1),  # Accept floating but trim to 1 decimal digit if needed
                    'fuel_price': float(row['fuel_price']),
                    'fuel': float(row['fuel']),
                    'total_fuel_price': float(row['total_fuel_price']),
                    'mpg': round(float(row['mpg']), 2)  # Round MPG to two decimal places if needed
                }
                imported_data.append(entry)

        for i, entry in enumerate(imported_data):
            last_entry = imported_data[i - 1] if i > 0 else (data[-1] if data else None)
            entry['mpg'] = calculate_mpg(last_entry, entry) if last_entry else 0
            data.append(entry)

        total_fuel = calculate_total_fuel(data)
        predicted_mpg = calculate_predicted_mpg(data)
        for entry in data:
            entry['total_fuel'] = total_fuel
            entry['predicted_mpg'] = predicted_mpg

        save_data(data)
        return jsonify({'success': True})

    return jsonify({'success': False, 'error': 'Invalid file format or no file provided'})

@app.route('/restore', methods=['POST'])
def restore_backup():
    try:
        backup_data = load_backup()
        save_data(backup_data, backup=False)
        return jsonify({'success': True}), 200
    except Exception as e:
        print(f"Failed to restore backup: {str(e)}")
        return jsonify({'success': False}), 500

@app.route('/summary')
def get_summary():
    data = load_data()
    if not data:
        return jsonify({
            'total_fuel_price': 0,
            'latest_odometer': 0,
            'price_per_mile_ratio': 0
        })

    total_fuel_price = sum(entry['total_fuel_price'] for entry in data)
    latest_odometer = data[-1]['odometer']
    total_distance = latest_odometer - data[0]['odometer'] if len(data) > 1 else 0
    price_per_mile_ratio = total_fuel_price / total_distance if total_distance != 0 else 0

    return jsonify({
        'total_fuel_price': total_fuel_price,
        'latest_odometer': latest_odometer,
        'price_per_mile_ratio': round(price_per_mile_ratio, 2)
    })

if __name__ == '__main__':
    app.run(debug=True)

