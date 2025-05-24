from flask import Flask, render_template, request, jsonify
import yfinance as yf
import pandas as pd
from datetime import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
from flask import send_file
import io
import csv

app = Flask(__name__)

def get_bitcoin_data(start_date, end_date):
    btc = yf.Ticker("BTC-USD")
    hist = btc.history(start=start_date, end=end_date)
    return hist

def get_stock_data(symbol, start_date, end_date):
    stock = yf.Ticker(symbol)
    hist = stock.history(start=start_date, end=end_date)
    return hist

def calculate_returns(initial_amount, start_price, end_price):
    return (end_price / start_price) * initial_amount

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/compare', methods=['POST'])
def compare():
    data = request.json
    amount = float(data['amount'])
    start_date = data['start_date']
    end_date = data['end_date']
    stock_symbol = data['stock_symbol']

    btc_data = get_bitcoin_data(start_date, end_date)
    stock_data = get_stock_data(stock_symbol, start_date, end_date)

    if len(btc_data) == 0 or len(stock_data) == 0:
        return jsonify({'error': 'No data available for the selected date range'})

    btc_start_price = btc_data['Close'].iloc[0]
    btc_end_price = btc_data['Close'].iloc[-1]
    stock_start_price = stock_data['Close'].iloc[0]
    stock_end_price = stock_data['Close'].iloc[-1]

    btc_final_amount = calculate_returns(amount, btc_start_price, btc_end_price)
    stock_final_amount = calculate_returns(amount, stock_start_price, stock_end_price)

    # Save data for external plotting if needed
    btc_data[['Close']].to_csv('btc_data.csv')
    stock_data[['Close']].to_csv(f'{stock_symbol}_data.csv')

    # --- Generate MATLAB-style chart ---
    # Calculate investment value over time
    btc_investment = amount * (btc_data['Close'] / btc_data['Close'].iloc[0])
    stock_investment = amount * (stock_data['Close'] / stock_data['Close'].iloc[0])
    
    plt.style.use('classic')  # MATLAB-like style
    plt.figure(figsize=(10, 6))
    plt.plot(btc_data.index, btc_investment, label='Bitcoin (BTC-USD)', color='orange')
    plt.plot(stock_data.index, stock_investment, label=f'{stock_symbol}', color='blue')
    plt.xlabel('Date')
    plt.ylabel('Investment Value (USD)')
    plt.title('Value of Your Investment Over Time')
    plt.legend()
    plt.grid(True)
    
    # Save the plot to static directory
    if not os.path.exists('static'):
        os.makedirs('static')
    chart_filename = f'static/chart_{stock_symbol}_{start_date}_{end_date}.png'
    plt.savefig(chart_filename, bbox_inches='tight')
    plt.close()

    #print("BTC index sample:", btc_data.index[:5])
    #print("Stock index sample:", stock_data.index[:5])

    return jsonify({
        'bitcoin_return': btc_final_amount,
        'stock_return': stock_final_amount,
        'bitcoin_gain_loss': btc_final_amount - amount,
        'stock_gain_loss': stock_final_amount - amount,
        'chart_url': '/' + chart_filename.replace('\\', '/')
    })

@app.route('/download-request', methods=['POST'])
def download_request():
    data = request.json
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['amount', 'start_date', 'end_date', 'stock_symbol'])
    writer.writerow([data['amount'], data['start_date'], data['end_date'], data['stock_symbol']])
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name='investment_request.csv'
    )

@app.route('/upload-request', methods=['POST'])
def upload_request():
    file = request.files['file']
    df = pd.read_csv(file)
    # Assume only one row per upload
    row = df.iloc[0]
    amount = float(row['amount'])
    start_date = row['start_date']
    end_date = row['end_date']
    stock_symbol = row['stock_symbol']

    # Reuse your compare logic:
    btc_data = get_bitcoin_data(start_date, end_date)
    stock_data = get_stock_data(stock_symbol, start_date, end_date)

    if len(btc_data) == 0 or len(stock_data) == 0:
        return jsonify({'error': 'No data available for the selected date range'})

    btc_start_price = btc_data['Close'].iloc[0]
    btc_end_price = btc_data['Close'].iloc[-1]
    stock_start_price = stock_data['Close'].iloc[0]
    stock_end_price = stock_data['Close'].iloc[-1]

    btc_final_amount = calculate_returns(amount, btc_start_price, btc_end_price)
    stock_final_amount = calculate_returns(amount, stock_start_price, stock_end_price)

    # Calculate investment value over time
    btc_investment = amount * (btc_data['Close'] / btc_data['Close'].iloc[0])
    stock_investment = amount * (stock_data['Close'] / stock_data['Close'].iloc[0])

    plt.style.use('classic')
    plt.figure(figsize=(10, 6))
    plt.plot(btc_data.index, btc_investment, label='Bitcoin (BTC-USD)', color='orange')
    plt.plot(stock_data.index, stock_investment, label=f'{stock_symbol}', color='blue')
    plt.xlabel('Date')
    plt.ylabel('Investment Value (USD)')
    plt.title('Value of Your Investment Over Time')
    plt.legend()
    plt.grid(True)

    if not os.path.exists('static'):
        os.makedirs('static')
    chart_filename = f'static/chart_{stock_symbol}_{start_date}_{end_date}.png'
    plt.savefig(chart_filename, bbox_inches='tight')
    plt.close()

    return jsonify({
        'bitcoin_return': btc_final_amount,
        'stock_return': stock_final_amount,
        'bitcoin_gain_loss': btc_final_amount - amount,
        'stock_gain_loss': stock_final_amount - amount,
        'chart_url': '/' + chart_filename.replace('\\', '/')
    })

if __name__ == '__main__':
    app.run(debug=True)