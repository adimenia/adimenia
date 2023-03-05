import argparse
import random
import socket
import struct
from datetime import datetime, timezone, timedelta

def generate_ip_address():
    return socket.inet_ntoa(struct.pack('>I', random.randint(1, 0xffffffff)))

def generate_log_line(format):
    timestamp = datetime.utcnow().replace(microsecond=0).replace(tzinfo=timezone.utc)
    timestamp_str = timestamp.isoformat()
    hostname = 'fw'
    appname = 'security_alerts'
    process_id = random.randint(10000, 99999)
    message_id = random.randint(10000000, 99999999)
    user = 'Alice'
    source_ip = generate_ip_address()
    destination_ip = generate_ip_address()
    source_port = random.randint(1024, 65535)
    destination_port = random.randint(1024, 65535)
    protocol = 'TCP'
    action = random.choice(['Blocked', 'Allowed'])
    product = 'FortiGate'
    interface = 'eth0'
    policy_name = 'Internet Access Policy'
    origin = 'example.com'
    if format == 'CEF':
        return f'CEF:0|{product}|{appname}|1.0|{message_id}|security_alert|{action}|' \
               f'sname={appname} suser={user} deviceHostName={hostname} deviceCustomDate1={timestamp_str} ' \
               f'destinationTranslatedAddress={destination_ip} destinationTranslatedPort={destination_port} ' \
               f'deviceCustomString4={protocol} deviceCustomString1={interface} deviceCustomString2={policy_name} ' \
               f'deviceCustomString3={origin} cn1Label=User cn1={user}'

    elif format == 'LEEF':
        return f'LEEF:1.0|{product}|{appname}|1.0|security_alert|' \
               f'severity={action} deviceExternalId={message_id} deviceCustomDate1={timestamp_str} ' \
               f'destinationTranslatedAddress={destination_ip} destinationTranslatedPort={destination_port} ' \
               f'deviceCustomString4={protocol} deviceCustomString1={interface} deviceCustomString2={policy_name} ' \
               f'deviceCustomString3={origin} cn1Label=User cn1={user}'

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate firewall logs')
    parser.add_argument('-f', '--format', choices=['CEF', 'LEEF'], default='CEF', help='Log format (CEF or LEEF)')
    parser.add_argument('-l', '--lines', type=int, default=10, help='Number of log lines to generate')
    parser.add_argument('-o', '--output', help='Output filename')
    args = parser.parse_args()

    log_lines = [generate_log_line(args.format) for _ in range(args.lines)]

    if args.output:
        with open(args.output, 'w') as f:
            f.write('\n'.join(log_lines))
    else:
        print('\n'.join(log_lines))
