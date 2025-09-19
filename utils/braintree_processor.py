import re
import aiohttp
import asyncio
import logging
import random
import json
from datetime import datetime
from typing import Dict, Optional, Tuple, List
from enum import Enum

logger = logging.getLogger(__name__)

class ErrorType(Enum):
    CARD_DECLINED = "1. Tarjeta Declinada"
    CONNECTION_ERROR = "2. Error de Conexión ▲"
    API_ERROR = "3. Error de API ●"
    INVALID_FORMAT = "4. Formato Inválido ●"
    INTERNAL_ERROR = "5. Error Interno ●"

class BraintreeProcessor:
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.error_messages = {
            ErrorType.CARD_DECLINED: [
                "❌ Tarjeta declinada por el banco emisor",
                "❌ Fondos insuficientes",
                "❌ Transacción no permitida",
                "❌ Límite de crédito excedido",
                "❌ Tarjeta reportada como robada"
            ],
            ErrorType.CONNECTION_ERROR: [
                "❌ Timeout de conexión (15s)",
                "❌ Servidor no disponible",
                "❌ Error de red temporal"
            ],
            ErrorType.API_ERROR: [
                "❌ Error en gateway de pago",
                "❌ Respuesta inválida del servidor",
                "❌ Configuración de API incorrecta"
            ],
            ErrorType.INVALID_FORMAT: [
                "❌ Formato de tarjeta incorrecto",
                "❌ Número de tarjeta inválido",
                "❌ Fecha de expiración incorrecta",
                "❌ CVV inválido"
            ]
        }
        
        # Respuestas de la API
        self.api_responses = [
            {'status': 'approved', 'message': '✅ Pago aprobado exitosamente'},
            {'status': 'declined', 'message': '❌ Transacción declinada por el banco'},
            {'status': 'fraud', 'message': '❌ Transacción marcada como fraudulenta'},
            {'status': 'processor_error', 'message': '❌ Error en el procesador de pagos'},
            {'status': 'gateway_error', 'message': '❌ Error en el gateway de pago'}
        ]
    
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
                timeout=aiohttp.ClientTimeout(total=15)  # 15 segundos timeout
            )
        return self.session
    
    async def close_session(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    def validate_cc_format(self, cc_text: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """Validate credit card format with detailed error messages"""
        try:
            if not cc_text or len(cc_text.strip()) < 10:
                return False, None, "❌ Formato de entrada demasiado corto"
            
            patterns = [
                r'(\d{15,16})[\|\\\/\s](\d{1,2})[\|\\\/\s](\d{2,4})[\|\\\/\s](\d{3,4})',
                r'(\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{3,4})[\|\\\/\s](\d{1,2})[\|\\\/\s](\d{2,4})[\|\\\/\s](\d{3,4})'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, cc_text)
                if match:
                    cc, mes, ano, cvv = match.groups()
                    
                    # Clean and validate CC number
                    cc = re.sub(r'[\s\-]', '', cc)
                    if len(cc) not in [15, 16]:
                        return False, None, "❌ Número de tarjeta debe tener 15-16 dígitos"
                    
                    # Validate month
                    mes = mes.zfill(2)
                    if not mes.isdigit() or not (1 <= int(mes) <= 12):
                        return False, None, "❌ Mes de expiración inválido (1-12)"
                    
                    # Validate year
                    if len(ano) == 2:
                        ano = '20' + ano
                    elif len(ano) != 4:
                        return False, None, "❌ Año de expiración inválido (formato YY o YYYY)"
                    
                    if not ano.isdigit() or int(ano) < datetime.now().year:
                        return False, None, "❌ Año de expiración inválido"
                    
                    # Validate CVV
                    if not cvv.isdigit() or len(cvv) not in [3, 4]:
                        return False, None, "❌ CVV inválido (3-4 dígitos)"
                    
                    cc_data = {
                        'cc': cc,
                        'mes': mes,
                        'ano': ano,
                        'cvv': cvv,
                        'raw': cc_text
                    }
                    
                    return True, cc_data, None
            
            return False, None, "❌ Formato inválido. Use: CC|MM|YYYY|CVV"
            
        except Exception as e:
            logger.error(f"Error en validación de formato: {e}")
            return False, None, "❌ Error interno en validación"
    
    def luhn_check(self, card_number: str) -> bool:
        """Luhn algorithm validation"""
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
        """Basic credit card validation"""
        try:
            cc = cc_data['cc']
            
            if not self.luhn_check(cc):
                return False, "❌ Número de tarjeta inválido (algoritmo Luhn)"
            
            # Check expiration date
            current_year = datetime.now().year
            current_month = datetime.now().month
            
            exp_year = int(cc_data['ano'])
            exp_month = int(cc_data['mes'])
            
            if exp_year < current_year:
                return False, "❌ Tarjeta expirada"
            elif exp_year == current_year and exp_month < current_month:
                return False, "❌ Tarjeta expirada"
            
            return True, "✅ Tarjeta válida"
            
        except Exception as e:
            logger.error(f"Error en validación: {e}")
            return False, "❌ Error en validación"
    
    async def get_bin_info(self, cc_number: str) -> Tuple[Optional[Dict], Optional[str]]:
        """Get BIN information with error handling"""
        bin_code = cc_number[:6]
        
        try:
            session = await self.get_session()
            async with session.get(f'https://lookup.binlist.net/{bin_code}', timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    return data, None
                else:
                    return None, f"❌ Error API BIN: HTTP {response.status}"
                    
        except asyncio.TimeoutError:
            return None, "❌ Timeout obteniendo información BIN"
        except aiohttp.ClientError as e:
            return None, f"❌ Error de conexión BIN: {str(e)}"
        except Exception as e:
            logger.error(f"Error getting BIN info: {e}")
            return None, f"❌ Error interno BIN"
    
    def detect_card_type(self, cc_number: str) -> Tuple[str, str]:
        """Detect card type based on BIN"""
        first_digit = cc_number[0]
        first_two = cc_number[:2]
        first_four = cc_number[:4]
        
        if first_digit == '4':
            return 'Visa', 'Credit'
        elif first_two in ['51', '52', '53', '54', '55']:
            return 'Mastercard', 'Credit'
        elif first_two in ['34', '37']:
            return 'American Express', 'Credit'
        elif first_two in ['30', '36', '38']:
            return 'Diners Club', 'Credit'
        elif first_four == '6011' or first_two == '65':
            return 'Discover', 'Credit'
        else:
            return 'Unknown', 'Unknown'
    
    async def simulate_api_call(self, cc_data: Dict) -> Tuple[bool, str, Optional[ErrorType]]:
        """Simulate API call with realistic error scenarios"""
        try:
            # Simulate network delay
            delay = random.uniform(1.5, 3.5)
            await asyncio.sleep(delay)
            
            # Simulate different scenarios based on random factors
            scenario = random.choices(
                ['success', 'declined', 'connection_error', 'api_error'],
                weights=[40, 35, 15, 10],
                k=1
            )[0]
            
            if scenario == 'success':
                return True, "✅ Transacción aprobada exitosamente", None
                
            elif scenario == 'declined':
                decline_reason = random.choice(self.error_messages[ErrorType.CARD_DECLINED])
                return False, decline_reason, ErrorType.CARD_DECLINED
                
            elif scenario == 'connection_error':
                connection_error = random.choice(self.error_messages[ErrorType.CONNECTION_ERROR])
                return False, connection_error, ErrorType.CONNECTION_ERROR
                
            elif scenario == 'api_error':
                api_error = random.choice(self.error_messages[ErrorType.API_ERROR])
                return False, api_error, ErrorType.API_ERROR
                
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"Error in API simulation: {e}")
            return False, "❌ Error interno en simulación", ErrorType.INTERNAL_ERROR
    
    def format_error_response(self, cc_data: Dict, error_type: ErrorType, error_msg: str) -> str:
        """Format error response with specific styling"""
        error_emoji = "🔴" if error_type == ErrorType.CARD_DECLINED else "🟡"
        
        response = f"""
{error_emoji} *{error_type.value}*

▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
✧ *TARJETA*: `{cc_data['cc'][:4]} XXXX XXXX {cc_data['cc'][-4:]}`
✧ *FECHA*: `{cc_data['mes']}/{cc_data['ano']}`
✧ *CVV*: `{cc_data['cvv']}`
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
📝 *MENSAJE*: 
`{error_msg}`
"""
        return response
    
    def format_success_response(self, cc_data: Dict, bin_info: Optional[Dict], message: str) -> str:
        """Format success response"""
        card_brand, card_type = self.detect_card_type(cc_data['cc'])
        
        country = "N/A"
        bank = "N/A"
        if bin_info:
            country = bin_info.get('country', {}).get('name', 'N/A')
            bank = bin_info.get('bank', {}).get('name', 'N/A')
        
        response = f"""
✅ *TRANSACCIÓN APROBADA*

▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
✧ *TARJETA*: `{cc_data['cc'][:4]} XXXX XXXX {cc_data['cc'][-4:]}`
✧ *FECHA*: `{cc_data['mes']}/{cc_data['ano']}`
✧ *CVV*: `{cc_data['cvv']}`
✧ *TIPO*: `{card_brand} {card_type}`
✧ *BANCO*: `{bank}`
✧ *PAÍS*: `{country}`
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
📝 *RESPUESTA*: 
`{message}`
"""
        return response

# Global processor instance
braintree_processor = BraintreeProcessor()