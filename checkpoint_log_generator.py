import argparse
import random
import socket
import struct
from datetime import datetime

def generate_ip_address():
    return socket.inet_ntoa(struct.pack('>I', random.randint(1, 0xffffffff)))

def generate_log_line(format):
    timestamp = datetime.utcnow().strftime('%b %d %H:%M:%S.%f')[:-3] + datetime.utcnow().strftime('%z')
    log_id = random.randint(10000000, 99999999)
    user = 'Alice'
    source_ip = generate_ip_address()
    destination_ip = generate_ip_address()
    source_port = random.randint(1024, 65535)
    destination_port = random.randint(1024, 65535)
    service = f'TCP/{destination_port}'
    action = random.choice(['Blocked', 'Allowed'])
    protocol = 'tcp'
    product = 'VPN-1 & FireWall-1'
    interface = 'eth0'
    policy_name = 'Internet Access Policy'
    origin = 'example.com'

    if format == 'CEF':
        device_vendor = 'Acme'
        device_product = 'Firewall'
        device_version = '1.0'
        signature_id = random.randint(1000, 9999)
        signature = 'Sample Signature'
        name = 'Sample Name'
        return f'CEF:0|{device_vendor}|{device_product}|{device_version}|{name}|6|' \
               f'sname={name} suser={user} destinationTranslatedAddress={destination_ip} ' \
               f'destinationTranslatedPort={destination_port} deviceSeverity=6 ' \
               f'deviceExternalId={log_id} deviceCustomString3={signature} ' \
               f'destinationServiceName={service} ' \
               f'destinationTranslatedPortContext=outside sourceTranslatedAddress={source_ip} ' \
               f'sourceTranslatedPort={source_port} cs2Label=Action cs2={action} ' \
               f'cs3Label=Interface cs3={interface} cs4Label=PolicyName cs4={policy_name} ' \
               f'cs5Label=Origin cs5={origin}'

    elif format == 'LEEF':
        log_format = f'LEEF:1.0|Acme|Firewall|1.0|{timestamp}|'
        return f'{log_format}fw security_alerts[{log_id}]: user_check: Log ID: {log_id}; User: {user}; ' \
               f'Source: {source_ip}; Destination: {destination_ip}; Service: {service}; Action: {action}; ' \
               f'Protocol: {protocol}; Product: {product}; Interface: {interface}; ' \
               f'Policy Name: {policy_name}; Origin: {origin};'

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate firewall logs')
    parser.add_argument('-f', '--format', choices=['CEF', 'LEEF'], default='CEF', help='Log format (CEF or LEEF)')
    parser.add_argument('-l', '--lines', type=int, default=10, help='Number of log lines to generate')
    parser.add_argument('-o', '--output', default='firewall_logs.txt', help='Output filename')
    args = parser.parse_args()

    with open(args.output, 'w') as f:
        for i in range(args.lines):
            log_line = generate_log_line(args.format)
            f.write(log_line + '\n')
            print(log_line)
