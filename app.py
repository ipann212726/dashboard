from flask import Flask, render_template, jsonify
import boto3
from decimal import Decimal
import json

app = Flask(__name__)

# DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('Orders')

# Custom JSON encoder untuk Decimal
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj)
        return super(DecimalEncoder, self).default(obj)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/orders')
def get_orders():
    try:
        response = table.scan(Limit=50)
        items = response['Items']
        
        # Sort by timestamp descending
        items.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        
        return jsonify({
            'success': True,
            'count': len(items),
            'orders': json.loads(json.dumps(items, cls=DecimalEncoder))
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health')
def health_check():
    try:
        # Test DynamoDB connection
        table.get_item(Key={'orderId': 'TEST', 'timestamp': 0})
        
        return jsonify({
            'status': 'healthy',
            'service': 'monitoring-dashboard',
            'dynamodb': 'connected'
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=False)
