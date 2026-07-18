"""
=============================================================================
REDSYS - TPV Virtual (CaixaBank)
Integracion por Redireccion - HMAC SHA256
=============================================================================

 Este modulo implementa la integracion con Redsys (pasarela de pago de
 CaixaBank y otros bancos espanoles) usando el metodo "por Redireccion".

 FLUJO:
 1. El POS crea una venta pendiente de pago
 2. Este modulo genera los parametros firmados para Redsys
 3. El navegador del cliente se redirige a la pagina segura de Redsys
 4. El cliente introduce los datos de tarjeta en Redsys
 5. Redsys procesa el pago y redirige de vuelta a tu web
 6. Tu web valida la firma y confirma el pago

 PARA ACTIVAR:
 1. Obtener credenciales de CaixaBank (FUC, terminal, clave de encriptacion)
 2. Descomentar las lineas de REDSYS_ en settings.py
 3. Rellenar las credenciales en .env
 4. Descomentar las URLs y views relacionadas
 5. Descomentar el flujo frontend en pos_tactil.html

 DOCUMENTACION REDSYS: https://pagosonline.redsys.es/desarrolladores-inicio/
=============================================================================
"""

import hmac
import hashlib
import base64
import json
import os
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# URLs de Redsys
# ---------------------------------------------------------------------------
REDSYS_URL_TEST = 'https://sis-t.redsys.es:25443/sis/realizarPago'
REDSYS_URL_PROD = 'https://sis.redsys.es/sis/realizarPago'


class RedsysError(Exception):
    pass


class RedsysClient:
    """
    Cliente para integracion con Redsys por Redireccion.

    Uso:
        client = RedsysClient(
            merchant_code='TU_FUC',
            terminal='1',
            shared_secret='TU_CLAVE_FIRMA',
            environment='test'
        )

        form_data = client.crear_pago(
            order_number='00001234',
            amount_cents=1520,  # 15.20 EUR
            titular='Cliente',
            descripcion='Pedido #1234',
            ok_url='https://tudominio.com/pago/ok/',
            ko_url='https://tudominio.com/pago/ko/',
            callback_url='https://tudominio.com/redsys/callback/',
        )
    """

    def __init__(self, merchant_code=None, terminal='1', shared_secret=None, environment='test'):
        self.merchant_code = merchant_code or os.getenv('REDSYS_MERCHANT_CODE', '')
        self.terminal = terminal or os.getenv('REDSYS_TERMINAL', '1')
        self.shared_secret = shared_secret or os.getenv('REDSYS_SHARED_SECRET', '')
        self.environment = environment or os.getenv('REDSYS_ENVIRONMENT', 'test')
        self.url_base = REDSYS_URL_TEST if self.environment == 'test' else REDSYS_URL_PROD

    def _calcular_firma(self, merchant_data_b64, order_number):
        """
        Calcula la firma HMAC SHA256.

        Proceso segun la documentacion de Redsys:
        1. Clave 3DES: encryptar order_number (8 bytes) con shared_secret (24 bytes)
        2. HMAC SHA256 de los parametros Base64 con esa clave
        """
        if not self.shared_secret:
            raise RedsysError('Falta REDSYS_SHARED_SECRET en .env')

        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

        # Clave 3DES: primeros 24 bytes de la shared_secret
        key_3des = self.shared_secret.encode('utf-8')[:24].ljust(24, b'\x00')

        # Order number: rellenar a 8 bytes (bloque DES)
        order_bytes = order_number.encode('utf-8')[:8].ljust(8, b'\x00')

        # Encriptar order_number con 3DES-ECB
        cipher = Cipher(algorithms.TripleDES(key_3des), modes.ECB())
        encryptor = cipher.encryptor()
        hmac_key = encryptor.update(order_bytes) + encryptor.finalize()

        # HMAC SHA256 de los parametros con la clave calculada
        signature = hmac.new(
            hmac_key,
            merchant_data_b64.encode('utf-8'),
            hashlib.sha256
        ).digest()

        return base64.b64encode(signature).decode('utf-8')

    def crear_pago(self, order_number, amount_cents, titular='Cliente',
                   descripcion='', idioma='1', ok_url='', ko_url='',
                   callback_url='', datos_extras=''):
        """
        Genera los datos para redirigir al TPV Virtual de Redsys.

        Parametros:
            order_number (str): Numero de orden unico (4-12 caracteres)
            amount_cents (int): Importe en centimos (1520 = 15.20 EUR)
            titular (str): Nombre del titular
            descripcion (str): Descripcion de la compra
            idioma (str): '1' espanol, '2' catalan, '3' ingles
            ok_url (str): URL si el pago es correcto
            ko_url (str): URL si el pago falla
            callback_url (str): URL de notificacion online ( webhook )
            datos_extras (str): Datos adicionales

        Retorna:
            dict con 'url' y campos del formulario
        """
        if not self.merchant_code:
            raise RedsysError('Falta REDSYS_MERCHANT_CODE en .env')

        merchant_params = {
            'DS_MERCHANT_AMOUNT': str(amount_cents),
            'DS_MERCHANT_MERCHANTCODE': self.merchant_code,
            'DS_MERCHANT_CURRENCY': '978',
            'DS_MERCHANT_MERCHANTURL': callback_url,
            'DS_MERCHANT_ORDER': order_number,
            'DS_MERCHANT_TERMINAL': self.terminal,
            'DS_MERCHANT_TITULAR': titular,
            'DS_MERCHANT_TRANSACTIONTYPE': '0',
            'DS_MERCHANT_URLOK': ok_url,
            'DS_MERCHANT_URLKO': ko_url,
            'DS_MERCHANT_PRODUCTDESCRIPTION': descripcion,
            'DS_MERCHANT_LANGUAGE': idioma,
        }

        if datos_extras:
            merchant_params['DS_MERCHANT_EXTRADATA'] = datos_extras

        params_json = json.dumps(merchant_params, separators=(',', ':'))
        params_b64 = base64.b64encode(params_json.encode('utf-8')).decode('utf-8')

        signature = self._calcular_firma(params_b64, order_number)

        return {
            'url': self.url_base,
            'Ds_SignatureVersion': 'HMAC_SHA256_V1',
            'Ds_MerchantData': params_b64,
            'Ds_Signature': signature,
        }

    @staticmethod
    def validar_respuesta(response_params, shared_secret):
        """
        Valida la firma de la respuesta de Redsys.

        Parametros:
            response_params (dict): Parametros Ds_* recibidos de Redsys
            shared_secret (str): Clave de encriptacion

        Retorna:
            True si la firma es valida
        """
        try:
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

            order = response_params.get('Ds_Order', '')
            signature_received = response_params.get('Ds_Signature', '')

            if not order or not signature_received:
                logger.warning('Redsys: Faltan parametros en la respuesta')
                return False

            # Reconstruir la firma
            key_3des = shared_secret.encode('utf-8')[:24].ljust(24, b'\x00')
            order_bytes = order.encode('utf-8')[:8].ljust(8, b'\x00')

            cipher = Cipher(algorithms.TripleDES(key_3des), modes.ECB())
            encryptor = cipher.encryptor()
            hmac_key = encryptor.update(order_bytes) + encryptor.finalize()

            # Concatenar todos los campos Ds_* excepto Ds_Signature
            sign_fields = []
            for k in sorted(response_params.keys()):
                if k.startswith('Ds_') and k != 'Ds_Signature':
                    sign_fields.append(response_params[k])
            sign_data = ''.join(sign_fields)

            signature_calc = hmac.new(
                hmac_key,
                sign_data.encode('utf-8'),
                hashlib.sha256
            ).digest()
            signature_b64 = base64.b64encode(signature_calc).decode('utf-8')

            return hmac.compare_digest(signature_b64, signature_received)

        except Exception as e:
            logger.error(f'Redsys: Error validando respuesta: {e}')
            return False

    @staticmethod
    def interpretar_respuesta(ds_response):
        """
        Interpreta el codigo de respuesta de Redsys.

        Retorna:
            tuple (bool, str): (exito, descripcion)
        """
        try:
            code = int(ds_response)
        except (TypeError, ValueError):
            return False, 'Respuesta no valida'

        if 0 <= code < 100:
            return True, 'Pago autorizado'
        elif 100 <= code < 200:
            return False, 'Pago pendiente de confirmacion'
        elif 200 <= code < 300:
            return False, 'Pago no autorizado'
        elif code == -1:
            return False, 'Cancelado por el cliente'
        elif code == -2:
            return False, 'Pago no encontrado'
        elif code == -3:
            return False, 'Error en el comercio'
        elif code == -4:
            return False, 'Pago rechazado por el banco'
        elif code == -5:
            return False, 'Error en la URL de retorno'
        elif code == -6:
            return False, 'Pago en proceso'
        elif code == -7:
            return False, 'Pago rechazado - CVV incorrecto'
        elif code == -9:
            return False, 'Tarjeta no soportada'
        elif code == -101:
            return False, 'Tarjeta no soportada por el comercio'
        elif code == -102:
            return False, 'Tarjeta no soportada'
        elif code == -902:
            return False, 'Error en la URL de notificacion'
        elif code == -904:
            return False, 'Error en la firma del comercio'
        elif code == -906:
            return False, 'Error en la clave de cifrado'
        elif code == -909:
            return False, 'Error en el proceso de pago'
        elif code == -999:
            return False, 'Error interno de Redsys'
        else:
            return False, f'Error desconocido (codigo: {code})'


def crear_cliente_redsys():
    """
    Crea un cliente Redsys con la configuracion de settings.py.
    """
    from django.conf import settings
    return RedsysClient(
        merchant_code=getattr(settings, 'REDSYS_MERCHANT_CODE', ''),
        terminal=getattr(settings, 'REDSYS_TERMINAL', '1'),
        shared_secret=getattr(settings, 'REDSYS_SHARED_SECRET', ''),
        environment=getattr(settings, 'REDSYS_ENVIRONMENT', 'test'),
    )
