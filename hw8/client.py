import requests

url = 'http://35.243.255.103:5000'
response = requests.get(url)
print(url)

# extract and print the X-VM-Zone header

vm_zone = response.headers.get('X-VM-Zone')
print(response.headers)
print(f'The server is running in the zone: {vm_zone}')

# print the rest of the response if needed
print(response.text)