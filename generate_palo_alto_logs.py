import argparse
import datetime
import ipaddress
import random
import socket
import struct
import sys


def random_ip():
    return socket.inet_ntoa(struct.pack('>I', random.randint(1, 0xffffffff)))


def generate_log_entry(log_format):
    if log_format == 'CEF':
        log_entry = f"CEF:0|PaloAlto|Firewall|1.0|100|{datetime.datetime.utcnow().isoformat()}|"
        log_entry += f"APP ID|SEVERITY|"
        log_entry += f"act=Action |"
        log_entry += f"src={random_ip()} |"
        log_entry += f"spt={random.randint(1024, 65535)} |"
        log_entry += f"dst={random_ip()} |"
        log_entry += f"dpt={random.randint(1024, 65535)} |"
        log_entry += f"srcMac=aa:bb:cc:dd:ee:ff |"
        log_entry += f"dstMac=11:22:33:44:55:66 |"
        log_entry += f"request=Example request |"
        log_entry += f"proto=TCP |"
        log_entry += f"shost=Example source host |"
        log_entry += f"dhost=Example destination host |"
        log_entry += f"cs1Label=Custom String1 label |"
        log_entry += f"cs1=Custom String1 value\n"
    elif log_format == 'LEEF':
        log_entry = f"LEEF:1.0|PaloAlto|Firewall|1.0|100|{datetime.datetime.utcnow().isoformat()}|"
        log_entry += f"act=Action src={random_ip()} spt={random.randint(1024, 65535)} "
        log_entry += f"dst={random_ip()} dpt={random.randint(1024, 65535)} srcMac=aa:bb:cc:dd:ee:ff "
        log_entry += f"dstMac=11:22:33:44:55:66 request=Example request proto=TCP "
        log_entry += f"shost=Example source host dhost=Example destination host cs1=Custom String1 value\n"
    else:
        print("Invalid log format specified")
        sys.exit(1)

    return log_entry


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate Palo Alto Firewall logs')
    parser.add_argument('-f', '--format', choices=['CEF', 'LEEF'], help='the log format to generate')
    parser.add_argument('-l', '--lines', type=int, help='the number of log entries to generate')
    parser.add_argument('-o', '--output', type=str, help='the output file name')
    args = parser.parse_args()

    log_entries = []
    for i in range(args.lines):
        log_entry = generate_log_entry(args.format)
        log_entries.append(log_entry)

    if args.output:
        with open(args.output, 'w') as f:
            f.writelines(log_entries)
        print(f"Generated {args.lines} log entries in {args.output}")
    else:
        for log_entry in log_entries:
            print(log_entry)
