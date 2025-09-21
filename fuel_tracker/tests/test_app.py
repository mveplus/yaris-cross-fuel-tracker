import unittest
import json
import io
from flask import Flask
from app import app, calculate_mpg, calculate_total_fuel, calculate_predicted_mpg, save_data, load_data, DATA_FILE, BACKUP_FILE
import shutil

class TestFuelTracker(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        self.data = [
            {'date': '23-01-01 12:00', 'odometer': 1000.1, 'fuel': 10, 'fuel_price': 2.5, 'total_fuel_price': 25.0, 'mpg': 0, 'total_fuel': 10, 'predicted_mpg': 0},
            {'date': '23-02-01 12:00', 'odometer': 1500.5, 'fuel': 20, 'fuel_price': 2.5, 'total_fuel_price': 50.0, 'mpg': 0, 'total_fuel': 30, 'predicted_mpg': 0},
            {'date': '23-03-01 12:00', 'odometer': 2000.9, 'fuel': 15, 'fuel_price': 2.5, 'total_fuel_price': 37.5, 'mpg': 0, 'total_fuel': 45, 'predicted_mpg': 0},
        ]
        self.new_entry = {'date': '23-04-01 12:00', 'odometer': 2500.0, 'fuel': 25, 'fuel_price': 2.5, 'total_fuel_price': 62.5, 'mpg': 0, 'total_fuel': 70, 'predicted_mpg': 0}
        save_data(self.data)

    def test_calculate_mpg(self):
        last_entry = self.data[-1]
        mpg = calculate_mpg(last_entry, self.new_entry)
        self.assertEqual(mpg, 9.11)

    def test_calculate_total_fuel(self):
        total_fuel = calculate_total_fuel(self.data)
        self.assertEqual(total_fuel, 45)

    def test_calculate_predicted_mpg(self):
        predicted_mpg = calculate_predicted_mpg(self.data)
        self.assertEqual(predicted_mpg, 8.76)

    def test_save_and_load_data(self):
        save_data(self.data)
        loaded_data = load_data()
        self.assertEqual(self.data, loaded_data)

    def test_add_entry(self):
        response = self.app.post('/add', data={
            'date': '23-04-01 12:00',
            'odometer': '2500.0',
            'fuel_price': '2.5',
            'fuel': '25'
        })
        self.assertEqual(response.status_code, 200)
        data = load_data()
        self.assertEqual(len(data), 4)
        self.assertEqual(data[-1]['odometer'], 2500.0)

    def test_delete_entries(self):
        response = self.app.post('/delete', json={'indices': [0]})
        self.assertEqual(response.status_code, 200)
        loaded_data = load_data()
        self.assertEqual(len(loaded_data), 2)

    def test_edit_entry(self):
        response = self.app.post('/edit/1', data={
            'date': '23-05-01 12:00',
            'odometer': '2200.7',
            'fuel_price': '2.8',
            'fuel': '18'
        })
        self.assertEqual(response.status_code, 200)
        loaded_data = load_data()
        self.assertEqual(loaded_data[1]['odometer'], 2200.7)
        self.assertEqual(loaded_data[1]['fuel_price'], 2.8)

    def test_export_data(self):
        response = self.app.get('/export')
        self.assertEqual(response.status_code, 200)

    def test_import_data(self):
        csv_data = """date,odometer,fuel_price,fuel,total_fuel_price,mpg
23-01-01 12:00,1000.1,2.5,10,25.0,0
23-02-01 12:00,1500.5,2.5,20,50.0,0
23-03-01 12:00,2000.9,2.5,15,37.5,0
"""
        response = self.app.post('/import', data={'file': (io.BytesIO(csv_data.encode()), 'data.csv')})
        self.assertEqual(response.status_code, 200)
        loaded_data = load_data()
        self.assertEqual(len(loaded_data), 3)
        self.assertEqual(loaded_data[0]['odometer'], 1000.1)

    def test_restore_backup(self):
        save_data(self.data)
        shutil.copyfile(DATA_FILE, BACKUP_FILE)
        response = self.app.post('/add', data={
            'date': '23-04-01 12:00',
            'odometer': '2500.0',
            'fuel_price': '2.5',
            'fuel': '25'
        })
        self.assertEqual(response.status_code, 200)
        response = self.app.post('/restore')
        self.assertEqual(response.status_code, 200)
        loaded_data = load_data()
        self.assertEqual(len(loaded_data), 3)

    def test_get_summary(self):
        response = self.app.get('/summary')
        self.assertEqual(response.status_code, 200)
        summary = json.loads(response.data)
        self.assertEqual(summary['total_fuel_price'], 112.5)
        self.assertEqual(summary['latest_odometer'], 2000.9)
        self.assertEqual(summary['price_per_mile_ratio'], 0.12)

if __name__ == '__main__':
    unittest.main()
