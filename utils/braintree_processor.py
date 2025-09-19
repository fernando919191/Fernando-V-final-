import re
import aiohttp
import asyncio
import logging
import random
import json
from datetime import datetime
from typing import Dict, Optional, Tuple, List
import time

logger = logging.getLogger(__name__)

class BraintreeProcessor:
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        # Respuestas más específicas y realistas
        self.responses = [
            {'code': 'three_d_secure', 'message': 'Your payment could not be taken. Please try again or use a different payment method. Gateway Rejected: three_d_secure'},
            {'code': 'processor_declined', 'message': 'Your payment could not be taken. Please try again or use a different payment method. Processor Declined'},
            {'code': 'no_account', 'message': 'Your payment could not be taken. Please try again or use a different payment method. No Account'},
            {'code': 'risk_threshold', 'message': 'Your payment could not be taken. Please try again or use a different payment method. Gateway Rejected: risk_threshold'},
            {'code': 'insufficient_funds', 'message': 'Your payment could not be taken. Please try again or use a different payment method. Insufficient Funds'},
            {'code': 'invalid_cvv', 'message': 'Your payment could not be taken. Please try again or use a different payment method. Invalid CVV'},
            {'code': 'card_expired', 'message': 'Your payment could not be taken. Please try again or use a different payment method. Card Expired'},
            {'code': 'success', 'message': 'Payment successful. Thank you for your purchase!'}
        ]
        
        # Códigos de error específicos por tipo de tarjeta
        self.card_errors = {
            'Visa': ['three_d_secure', 'risk_threshold', 'insufficient_funds'],
            'Mastercard': ['processor_declined', 'invalid_cvv', 'risk_threshold'],
            'American Express': ['no_account', 'card_expired', 'three_d_secure'],
            'Discover': ['processor_declined', 'insufficient_funds'],
            'Unknown': ['three_d_secure', 'processor_declined', 'risk_threshold']
        }
    
    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'application/json, text/plain, */*',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Content-Type': 'application/json',
                },
                timeout=aiohttp.ClientTimeout(total=15)
            )
        return self.session
    
    async def close_session(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    def parse_cc(self, cc_text: str) -> Optional[Dict]:
        """Parse credit card information from text con mejor manejo de errores"""
        try:
            patterns = [
                r'(\d{15,16})[\|\\\/\s](\d{1,2})[\|\\\/\s](\d{2,4})[\|\\\/\s](\d{3,4})',
                r'(\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{3,4})[\|\\\/\s](\d{1,2})[\|\\\/\s](\d{2,4})[\|\\\/\s](\d{3,4})',
                r'(\d{16})[\|\\\/\s](\d{2})[\|\\\/\s](\d{2,4})[\|\\\/\s](\d{3})'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, cc_text)
                if match:
                    cc, mes, ano, cvv = match.groups()
                    
                    # Clean CC number
                    cc = re.sub(r'[\s\-]', '', cc)
                    
                    # Validar longitud de tarjeta
                    if len(cc) not in [15, 16]:
                        return None
                    
                    # Format month to 2 digits
                    mes = mes.zfill(2)
                    
                    # Validar mes
                    if not (1 <= int(mes) <= 12):
                        return None
                    
                    # Format year to 4 digits if it's 2 digits
                    if len(ano) == 2:
                        ano = '20' + ano
                    elif len(ano) != 4:
                        return None
                    
                    # Validar CVV
                    if len(cvv) not in [3, 4]:
                        return None
                    
                    return {
                        'cc': cc,
                        'mes': mes,
                        'ano': ano,
                        'cvv': cvv,
                        'raw': cc_text
                    }
            return None
            
        except Exception as e:
            logger.error(f"Error parsing CC: {e}")
            return None
    
    def luhn_check(self, card_number: str) -> bool:
        """Luhn algorithm validation con mejor manejo de errores"""
        try:
            digits = [int(d) for d in str(card_number)]
            odd_digits = digits[-1::-2]
            even_digits = digits[-2::-2]
            total = sum(odd_digits)
            for d in even_digits:
                total += sum(divmod(d * 2, 10))
            return total % 10 == 0
        except:
            return False
    
    def check_cc_validity(self, cc_data: Dict) -> Tuple[bool, str]:
        """Basic credit card validation con mensajes específicos"""
        try:
            cc = cc_data['cc']
            
            # Check card length
            if len(cc) not in [15, 16]:
                return False, "❌ Longitud de tarjeta inválida (debe tener 15-16 dígitos)"
            
            # Luhn algorithm check
            if not self.luhn_check(cc):
                return False, "❌ Número de tarjeta inválido (algoritmo Luhn falló)"
            
            # Check expiration date
            current_year = datetime.now().year
            current_month = datetime.now().month
            
            exp_year = int(cc_data['ano'])
            exp_month = int(cc_data['mes'])
            
            if exp_year < current_year:
                return False, "❌ Tarjeta expirada (año vencido)"
            elif exp_year == current_year and exp_month < current_month:
                return False, "❌ Tarjeta expirada (mes vencido)"
                
            if not (1 <= exp_month <= 12):
                return False, "❌ Mes de expiración inválido (debe ser 1-12)"
            
            # Check CVV length based on card type
            cvv = cc_data['cvv']
            card_type = self.detect_card_type(cc)[0]
            
            if card_type == 'American Express' and len(cvv) != 4:
                return False, "❌ CVV inválido (Amex requiere 4 dígitos)"
            elif card_type != 'American Express' and len(cvv) != 3:
                return False, "❌ CVV inválido (requiere 3 dígitos)"
            
            return True, "✅ Tarjeta válida"
            
        except ValueError:
            return False, "❌ Error en formato de fecha"
        except Exception as e:
            logger.error(f"Error en validación: {e}")
            return False, "❌ Error en validación de tarjeta"
    
    async def get_bin_info(self, cc_number: str) -> Optional[Dict]:
        """Get BIN information asynchronously con reintentos"""
        bin_code = cc_number[:6]
        max_retries = 2
        
        for attempt in range(max_retries):
            try:
                session = await self.get_session()
                async with session.get(f'https://lookup.binlist.net/{bin_code}', timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    elif response.status == 429:
                        await asyncio.sleep(1)  # Esperar por rate limiting
            except asyncio.TimeoutError:
                if attempt == max_retries - 1:
                    logger.warning(f"Timeout getting BIN info for {bin_code}")
                await asyncio.sleep(0.5)
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Error getting BIN info: {e}")
                await asyncio.sleep(0.5)
        
        return None
    
    def detect_card_type(self, cc_number: str) -> Tuple[str, str]:
        """Detect card type based on BIN con más precisión"""
        first_digit = cc_number[0]
        first_two = cc_number[:2]
        first_four = cc_number[:4]
        
        if first_digit == '4':
            return 'Visa', 'Credit'
        elif first_two in ['51', '52', '53', '54', '55']:
            return 'Mastercard', 'Credit'
        elif first_two in ['34', '37']:
            return 'American Express', 'Credit'
        elif first_two in ['30', '36', '38'] or first_two in ['300', '301', '302', '303', '304', '305']:
            return 'Diners Club', 'Credit'
        elif first_four == '6011' or first_two == '65':
            return 'Discover', 'Credit'
        elif first_digit == '3':
            return 'JCB', 'Credit'
        else:
            return 'Unknown', 'Unknown'
    
    async def simulate_braintree_payment(self, cc_data: Dict) -> Tuple[bool, str, str]:
        """Simulate Braintree payment processing con errores específicos"""
        try:
            # Simulate API call delay (más realista)
            delay = random.uniform(2.0, 4.0)
            await asyncio.sleep(delay)
            
            # Detectar tipo de tarjeta para errores específicos
            card_type = self.detect_card_type(cc_data['cc'])[0]
            
            # Probabilidades basadas en tipo de tarjeta
            if card_type == 'American Express':
                weights = [20, 15, 25, 20, 10, 5, 0, 5]  # Amex tiene más probabilidad de "no_account"
            elif card_type == 'Visa':
                weights = [25, 20, 10, 25, 10, 5, 5, 0]  # Visa más 3D Secure
            else:
                weights = [20, 25, 15, 20, 10, 5, 5, 0]  # Distribución general
            
            # Ajustar probabilidades basado en CVV (si es débil)
            if cc_data['cvv'] in ['123', '000', '111', '999']:
                weights[5] += 15  # Aumentar probabilidad de invalid_cvv
            
            response_data = random.choices(self.responses, weights=weights, k=1)[0]
            
            success = response_data['code'] == 'success'
            return success, response_data['message'], response_data['code']
                
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"Error simulating payment: {e}")
            return False, "❌ Error interno en el procesamiento del pago", "internal_error"
    
    def format_response(self, cc_data: Dict, validity_result: Tuple[bool, str], 
                       bin_info: Optional[Dict], payment_result: Tuple[bool, str, str]) -> str:
        """Format the response message con más detalles"""
        valid, validity_msg = validity_result
        payment_success, payment_msg, error_code = payment_result
        
        card_brand, card_type = self.detect_card_type(cc_data['cc'])
        
        country = "N/A"
        bank = "N/A"
        if bin_info:
            country = bin_info.get('country', {}).get('name', 'N/A')
            bank = bin_info.get('bank', {}).get('name', 'N/A')
        
        # Formatear número de tarjeta para display
        if len(cc_data['cc']) == 16:
            cc_display = f"{cc_data['cc'][:4]} {cc_data['cc'][4:8]} {cc_data['cc'][8:12]} {cc_data['cc'][12:]}"
        else:
            cc_display = f"{cc_data['cc'][:4]} {cc_data['cc'][4:10]} {cc_data['cc'][10:15]}"
        
        status_emoji = "✅" if payment_success else "❌"
        status_text = "APROBADA" if payment_success else "RECHAZADA"
        
        response = f"""
💳 *SITE*: `https://www.londonstore.it/checkout`  
🛡️ *CAPTCHA*: `None`  
🔐 *SECURITY*: `Unknown`  
🏦 *GATEWAY*: `Braintree`  
⚙️ *TECHNOLOGY*: `Undetected`  

▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
✧ *TARJETA*: `{cc_display}`
✧ *FECHA*: `{cc_data['mes']}/{cc_data['ano']}`
✧ *CVV*: `{cc_data['cvv']}`
✧ *TIPO*: `{card_brand} {card_type}`
✧ *BANCO*: `{bank}`
✧ *PAÍS*: `{country}`
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
✧ *VALIDACIÓN*: {validity_msg}
✧ *PROCESAMIENTO*: {status_emoji} `{status_text}`
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
📩 *RESPONSE*: 
`{payment_msg}`
"""
        
        # Añadir código de error si existe
        if not payment_success and error_code != 'internal_error':
            response += f"\n🔍 *CÓDIGO ERROR*: `{error_code}`"
        
        return response

# Global processor instance
braintree_processor = BraintreeProcessor()