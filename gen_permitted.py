import argparse

parser = argparse.ArgumentParser(description='Generate allowed domain constraints')
parser.add_argument('domains', metavar='domains', type=str, nargs='+',
                    help='domains to allow')

if __name__ == '__main__':
    args = parser.parse_args()
    index = 0
    dns_index = 0
    email_str = ''
    dns_str = ''
    uri_str = ''
    for domain in args.domains:
        dns_str += f'permitted;DNS.{dns_index}={domain}\n'
        uri_str += f'''permitted;URI.{index}={domain}
permitted;URI.{index + 1}=.{domain}\n'''
        email_str += f'''permitted;email.{index}={domain}
permitted;email.{index + 1}=.{domain}\n'''
        dns_index += 1
        index += 2

    print('\n'.join([dns_str, uri_str, email_str]))

