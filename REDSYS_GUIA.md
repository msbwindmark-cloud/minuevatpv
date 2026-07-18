# REDSYS - Guia de Integracion TPV Virtual (CaixaBank)

## Que es esto?

Integracion con **Redsys** (la pasarela de pago de CaixaBank y la mayoria de bancos espanoles) para cobrar con tarjeta real desde el TPV.

---

## Pasos para activar

### Paso 1: Obtener credenciales de CaixaBank

Contacta con CaixaBank y solicita el **TPV Virtual**. Te proporcionaran:

- **Codigo FUC** (Numero de Comercio) - Ej: `123456789`
- **Terminal** - Normalmente `1`
- **Clave de encriptacion** - Una cadena de 24 caracteres que usaremos para firmar las transacciones

> Si ya tienes TPV Virtual, accede al modulo de administracion de Redsys:
> https://portal.redsys.es > Consulta de datos del comercio > Ver clave

### Paso 2: Rellenar credenciales en `.env`

Abre el archivo `.env` y descomenta las lineas de Redsys:

```env
REDSYS_MERCHANT_CODE=123456789
REDSYS_TERMINAL=1
REDSYS_SHARED_SECRET=abcdef1234567890abcdef12
REDSYS_ENVIRONMENT=test
REDSYS_URL_OK=http://127.0.0.1:8000/redsys/ok/
REDSYS_URL_KO=http://127.0.0.1:8000/redsys/ko/
```

### Paso 3: Descomentar settings.py

En `cafe_tpv/settings.py`, descomenta las lineas de REDSYS:

```python
REDSYS_MERCHANT_CODE = os.getenv('REDSYS_MERCHANT_CODE', '')
REDSYS_TERMINAL = os.getenv('REDSYS_TERMINAL', '1')
REDSYS_SHARED_SECRET = os.getenv('REDSYS_SHARED_SECRET', '')
REDSYS_ENVIRONMENT = os.getenv('REDSYS_ENVIRONMENT', 'test')
REDSYS_URL_OK = os.getenv('REDSYS_URL_OK', 'http://127.0.0.1:8000/redsys/ok/')
REDSYS_URL_KO = os.getenv('REDSYS_URL_KO', 'http://127.0.0.1:8000/redsys/ko/')
```

### Paso 4: Descomentar URLs

En `cafe_tpv/urls.py`, descomenta las 4 URLs de Redsys al final del archivo:

```python
path('api/redsys/iniciar-pago/', views.api_redsys_iniciar_pago, name='redsys_iniciar_pago'),
path('redsys/callback/', views.redsys_callback, name='redsys_callback'),
path('redsys/ok/', views.redsys_ok, name='redsys_ok'),
path('redsys/ko/', views.redsys_ko, name='redsys_ko'),
```

### Paso 5: Descomentar views

En `tpv/views.py`, descomenta todo el bloque REDSYS al final del archivo (las funciones `api_redsys_iniciar_pago`, `redsys_callback`, `redsys_ok`, `redsys_ko`).

### Paso 6: Descomentar frontend

En `templates/pos_tactil.html`:

1. Busca la linea `// redsysPago(lista, total + propinaMonto, mesaActual);` y descomentala
2. Comenta la linea de `terminalAnimacion` que hay debajo
3. Busca el bloque `/* ... */` de la funcion `redsysPago` (busca `function redsysPago`) y elimina los `/*` y `*/` que lo envuelven

### Paso 7: Instalar dependencia

```bash
pip install cryptography
```

Y actualiza `requirements.txt` (ya esta incluido).

---

## Flujo del cobro con tarjeta (Redsys)

```
Cajero pulsa "COBRAR TARJETA"
        |
        v
POS envia items a /api/redsys/iniciar-pago/
        |
        v
Backend crea numero de orden unico + firma HMAC SHA256
        |
        v
Backend devuelve URL de Redsys + parametros firmados
        |
        v
Frontend abre nueva ventana con el formulario de Redsys
(el cliente introduce su tarjeta en la pagina segura de Redsys)
        |
        v
Redsys procesa el pago
        |
        v
Redsys redirige a /redsys/ok/ o /redsys/ko/
        |
        v
Cajero ve confirmacion y vuelve al TPV
```

---

## Entorno de pruebas

Redsys tiene un entorno sandbox para pruebas. Usa estas tarjetas para testear:

| Tarjeta         | Numero              | CVV  | Resultado esperado |
|----------------|---------------------|------|-------------------|
| Visa (pago OK) | `4548812049400004`  | `123`| Autorizado        |
| Visa (rechazo) | `4548812049400004`  | `999`| Denegado          |

- Caducidad: cualquier fecha futura
- Importe a pagar: el que aparece en el TPV

> **IMPORTANTE**: Cuando pases a produccion, cambia `REDSYS_ENVIRONMENT` de `test` a `real`.
> Si dejas `test` en produccion, los clientes podrian usar tarjetas de prueba.

---

## URLs de Redsys

| Entorno  | URL de pago                          |
|----------|--------------------------------------|
| Test     | `https://sis-t.redsys.es:25443/sis/realizarPago` |
| Produccion | `https://sis.redsys.es/sis/realizarPago`      |

---

## Produccion (PythonAnywhere)

Cuando pases a produccion, actualiza las URLs en `.env`:

```env
REDSYS_ENVIRONMENT=real
REDSYS_URL_OK=https://minuevatpv.pythonanywhere.com/redsys/ok/
REDSYS_URL_KO=https://minuevatpv.pythonanywhere.com/redsys/ko/
```

---

## Codigo de los archivos modificados

| Archivo              | Que hacer                                                    |
|----------------------|--------------------------------------------------------------|
| `tpv/redsys.py`      | No tocar - listo para usar                                    |
| `tpv/views.py`       | Descomentar bloque REDSYS al final                            |
| `cafe_tpv/urls.py`   | Descomentar 4 URLs al final                                   |
| `cafe_tpv/settings.py` | Descomentar settings REDSYS                                 |
| `.env`               | Rellenar credenciales                                         |
| `templates/pos_tactil.html` | Descomentar `redsysPago()` y el bloque JS               |
| `templates/redsys/resultado.html` | No tocar - ya creado                            |
| `requirements.txt`   | Ya incluye `cryptography`                                     |

---

## Troubleshooting

### "Firma no valida" (error 400)
- La `REDSYS_SHARED_SECRET` no coincide con la del modulo de administracion de Redsys
- Verifica que no hay espacios extra en `.env`

### "Error en el comercio" (codigo -3)
- El `REDSYS_MERCHANT_CODE` (FUC) es incorrecto
- El `REDSYS_TERMINAL` no esta activo en Redsys

### "URL no valida" (codigo -902)
- Las URLs de OK/KO no son accesibles desde internet
- En produccion, usa HTTPS y un dominio real

### Pago funciona en test pero no en real
- Cambia `REDSYS_ENVIRONMENT` a `real`
- Verifica que la URL de callback (`REDSYS_MERCHANTURL`) apunta a tu dominio real con HTTPS
- Las URLs de OK/KO deben ser HTTPS en produccion

---

## Seguridad

- **NUNCA** guardes datos de tarjeta en tu base de datos
- La transaccion con tarjeta ocurre enteramente en la pagina segura de Redsys
- Tu solo recibes un codigo de respuesta (autorizado/no autorizado)
- La firma HMAC SHA256 garantiza que nadie ha manipulado los datos
- En produccion, siempre usa HTTPS

---

## Documentacion oficial

- Portal de desarrollo: https://pagosonline.redsys.es/desarrolladores-inicio/
- Guia de integracion por Redireccion: https://pagosonline.redsys.es/desarrolladores-inicio/integrate-con-nosotros/integracion-por-redireccion/
- Tarjetas de prueba: https://pagosonline.redsys.es/desarrolladores-inicio/integrate-con-nosotros/tarjetas-y-entornos-de-prueba/
