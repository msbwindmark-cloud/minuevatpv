import os, sys, urllib.request, http.cookiejar, re, urllib.parse

os.environ['DJANGO_SETTINGS_MODULE'] = 'cafe_tpv.settings'
os.chdir(r'C:\practicarVB\nuevacafe')
sys.path.insert(0, r'C:\practicarVB\nuevacafe')
import django; django.setup()

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

def login(user, pwd):
    resp = opener.open('http://127.0.0.1:8080/accounts/login/')
    html = resp.read().decode('utf-8')
    m = re.search(r'csrfmiddlewaretoken.*?value="([^"]+)"', html)
    csrf = m.group(1)
    data = urllib.parse.urlencode({'csrfmiddlewaretoken': csrf, 'username': user, 'password': pwd}).encode()
    opener.open(urllib.request.Request('http://127.0.0.1:8080/accounts/login/', data=data, headers={'Referer': 'http://127.0.0.1:8080/accounts/login/'}))

# Test as cajero
login('cajero1', 'cajero1234')
print('=== CAJERO - Protected pages ===')
for url, name in [('/api/dashboard-gerencia/', 'Dashboard'), ('/reservas/', 'Reservas'), ('/bitacora/', 'Bitacora')]:
    r = opener.open('http://127.0.0.1:8080' + url)
    c = r.read().decode('utf-8')
    is_login = 'TPV Cafeteria Pro' in c or 'credenciales' in c
    print(f'  {name}: {"BLOCKED (redirected to login)" if is_login else "VISIBLE - PROBLEM!"}')

# Superuser
login('admin', 'admin1234')
print('\n=== SUPERUSER - Protected pages ===')
for url, name in [('/api/dashboard-gerencia/', 'Dashboard'), ('/reservas/', 'Reservas'), ('/bitacora/', 'Bitacora'), ('/cierre-caja/', 'Caja')]:
    r = opener.open('http://127.0.0.1:8080' + url)
    c = r.read().decode('utf-8')
    is_login = 'TPV Cafeteria Pro' in c or 'credenciales' in c
    print(f'  {name}: {"BLOCKED" if is_login else "VISIBLE"}')
