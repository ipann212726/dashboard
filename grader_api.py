from flask import Flask, jsonify
import boto3
import json

app = Flask(__name__)

@app.route('/api/health-check', methods=['GET'])
def health_check():
    """
    Endpoint untuk automated assessment
    Verifikasi kesehatan semua komponen infrastruktur
    """
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'checks': {}
    }
    
    # Check 1: VPC Connectivity
    try:
        ec2 = boto3.client('ec2', region_name='us-east-1')
        vpcs = ec2.describe_vpcs(Filters=[
            {'Name': 'tag:Name', 'Values': ['LKS-VPC2026']}
        ])
        results['checks']['vpc'] = {
            'status': 'PASS' if len(vpcs['Vpcs']) > 0 else 'FAIL',
            'message': 'VPC found' if len(vpcs['Vpcs']) > 0 else 'VPC not found'
        }
    except Exception as e:
        results['checks']['vpc'] = {'status': 'ERROR', 'message': str(e)}
    
    # Check 2: DynamoDB Connectivity
    try:
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('Orders')
        response = table.scan(Limit=1)
        results['checks']['dynamodb'] = {
            'status': 'PASS',
            'message': f"Connected, {response['Count']} items scanned"
        }
    except Exception as e:
        results['checks']['dynamodb'] = {'status': 'ERROR', 'message': str(e)}
    
    # Check 3: S3 Connectivity
    try:
        s3 = boto3.client('s3', region_name='us-east-1')
        buckets = s3.list_buckets()
        lks_buckets = [b for b in buckets['Buckets'] if 'lks-orders' in b['Name']]
        results['checks']['s3'] = {
            'status': 'PASS' if len(lks_buckets) > 0 else 'FAIL',
            'message': f"Found {len(lks_buckets)} LKS bucket(s)"
        }
    except Exception as e:
        results['checks']['s3'] = {'status': 'ERROR', 'message': str(e)}
    
    # Check 4: SQS Connectivity
    try:
        sqs = boto3.client('sqs', region_name='us-east-1')
        queues = sqs.list_queues(QueueNamePrefix='Order')
        queue_count = len(queues.get('QueueUrls', []))
        results['checks']['sqs'] = {
            'status': 'PASS' if queue_count > 0 else 'FAIL',
            'message': f"Found {queue_count} queue(s)"
        }
    except Exception as e:
        results['checks']['sqs'] = {'status': 'ERROR', 'message': str(e)}
    
    # Check 5: Lambda Functions
    try:
        lambda_client = boto3.client('lambda', region_name='us-east-1')
        functions = lambda_client.list_functions()
        lks_functions = [f for f in functions['Functions'] if 'Order' in f['FunctionName']]
        results['checks']['lambda'] = {
            'status': 'PASS' if len(lks_functions) >= 2 else 'PARTIAL',
            'message': f"Found {len(lks_functions)} Lambda function(s)"
        }
    except Exception as e:
        results['checks']['lambda'] = {'status': 'ERROR', 'message': str(e)}
    
    # Overall Status
    all_pass = all(check['status'] == 'PASS' for check in results['checks'].values())
    results['overall_status'] = 'PASS' if all_pass else 'FAIL'
    
    return jsonify(results)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
