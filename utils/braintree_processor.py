import re
import aiohttp
import asyncio
import logging
import random
import json
from datetime import datetime
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

class BraintreeProcessor:
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.responses = [
            {'message': 'Your payment could not be taken. Please try again or use a different payment method. Gateway Rejected: three_d_secure'},
            {'message': 'Your payment could not be taken. Please try again or use a different payment method. Processor Declined'},
            {'message': 'Your payment could not be taken. Please try again or use a different payment method. No Account'},
            {'message': 'Your payment could not be taken. Please try again or use a different payment method. Gateway Rejected: risk_threshold'},
            {'message': 'Payment successful. Thank you for your purchase!'}
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
                timeout=aiohttp.ClientTimeout(total=10)
            )
        return self.session
    
    async def close_session(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    def parse_cc(self, cc_text: str) -> Optional[Dict]:
        """Parse credit card information from text"""
        patterns = [
            r'(\d{15,16})[\|\\\/](\d{1,2})[\|\\\/](\d{2,4})[\|\\\/](\d{3,4})',
            r'(\d{15,16})\s+(\d{1,2})\s+(\d{2,4})\s+(\d{3,4})',
            r'(\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4})[\|\\\/](\d{1,2})[\|\\\/](\d{2,4})[\|\\\/](\d{3,4})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, cc_text)
            if match:
                cc, mes, ano, cvv = match.groups()
                
                cc = re.sub(r'[\s\-]', '', cc)
                mes = mes.zfill(2)
                
                if len(ano) == 2:
                    ano = '20' + ano
                
                return {
                    'cc': cc,
                    'mes': mes,
                    'ano': ano,
                    'cvv': cvv,
                    'raw': cc_text
                }
        return None
    
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
        cc = cc_data['cc']
        
        if len(cc) not in [15, 16]:
            return False, "❌ Longitud de tarjeta inválida"
        
        if not self.luhn_check(cc):
            return False, "❌ Tarjeta inválida (algoritmo Luhn)"
        
        try:
            current_year = datetime.now().year
            current_month = datetime.now().month
            
            exp_year = int(cc_data['ano'])
            exp_month = int(cc_data['mes'])
            
            if exp_year < current_year or (exp_year == current_year and exp_month < current_month):
                return False, "❌ Tarjeta expirada"
                
            if not (1 <= exp_month <= 12):
                return False, "❌ Mes de expiración inválido"
                
        except ValueError:
            return False, "❌ Fecha de expiración inválida"
        
        cvv = cc_data['cvv']
        if len(cvv) not in [3, 4]:
            return False, "❌ CVV inválido"
        
        return True, "✅ Tarjeta válida"
    
    async def get_bin_info(self, cc_number: str) -> Optional[Dict]:
        """Get BIN information asynchronously"""
        bin_code = cc_number[:6]
        try:
            session = await self.get_session()
            async with session.get(f'https://lookup.binlist.net/{bin_code}', timeout=5) as response:
                if response.status == 200:
                    return await response.json()
        except asyncio.TimeoutError:
            logger.warning(f"Timeout getting BIN info for {bin_code}")
        except Exception as e:
            logger.error(f"Error getting BIN info: {e}")
        return None
    
    def detect_card_type(self, cc_number: str) -> Tuple[str, str]:
        """Detect card type based on BIN"""
        if cc_number.startswith('4'):
            return 'Visa', 'Credit'
        elif cc_number.startswith(('51', '52', '53', '54', '55')):
            return 'Mastercard', 'Credit'
        elif cc_number.startswith(('34', '37')):
            return 'American Express', 'Credit'
        elif cc_number.startswith(('300', '301', '302', '303', '304', '305')):
            return 'Diners Club', 'Credit'
        elif cc_number.startswith(('6011', '65')):
            return 'Discover', 'Credit'
        else:
            return 'Unknown', 'Unknown'
    
    async def simulate_braintree_payment(self, cc_data: Dict) -> Tuple[bool, str]:
        """Simulate Braintree payment processing asynchronously"""
        try:
            # Simulate API call delay
            await asyncio.sleep(2.5)
            
            # Weighted random response
            weights = [25, 25, 15, 20, 15]
            response = random.choices(self.responses, weights=weights, k=1)[0]
            
            success = 'successful' in response['message'].lower()
            return success, response['message']
                
        except Exception as e:
            logger.error(f"Error simulating payment: {e}")
            return False, "❌ Error en el procesamiento del pago"
    
    def format_response(self, cc_data: Dict, validity_result: Tuple[bool, str], 
                       bin_info: Optional[Dict], payment_result: Tuple[bool, str]) -> str:
        """Format the response message"""
        valid, validity_msg = validity_result
        payment_success, payment_msg = payment_result
        
        card_brand, card_type = self.detect_card_type(cc_data['cc'])
        
        country = "N/A"
        if bin_info and bin_info.get('country'):
            country = bin_info['country'].get('name', 'N/A')
        
        cc_display = f"{cc_data['cc'][:4]} XXXX XXXX {cc_data['cc'][-4:]}"
        status_emoji = "✅" if payment_success else "❌"
        
        response = f"""
💳 𝑺𝒊𝒕𝒆: https://www.londonstore.it/checkout  
🛡️ 𝑪𝒂𝒑𝒕𝒄𝒉𝒂: 𝑵𝒐𝒏𝒆  
🔐 𝑺𝒆𝒄𝒖𝒓𝒊𝒕𝒚: 𝑼𝒏𝒌𝒏𝒐𝒘𝒏  
🏦 𝑮𝒂𝒕𝒆𝒘𝒂𝒚: 𝑩𝒓𝒂𝒊𝒏𝒕𝒓𝒆𝒆  
⚙️ 𝑻𝒆𝒄𝒉𝒏𝒐𝒍𝒐𝒈𝒚: 𝑼𝒏𝒅𝒆𝒕𝒆𝒄𝒕𝒆𝒅  

- - - - - - - - - - - - - - -
⋄ 𝑻𝒂𝒓𝒋𝒆𝒕𝒂: {cc_display}
⋄ 𝑭𝒆𝒄𝒉𝒂: {cc_data['mes']}/{cc_data['ano']}
⋄ 𝑪𝑽𝑽: {cc_data['cvv']}
⋄ 𝑻𝒊𝒑𝒐: {card_brand} | {card_type}
⋄ 𝑷𝒂í𝒔: {country}
- - - - - - - - - - - - - - -
⋄ 𝑽𝒂𝒍𝒊𝒅𝒂𝒄𝒊ó𝒏: {validity_msg}
⋄ 𝑷𝒓𝒐𝒄𝒆𝒔𝒂𝒎𝒊𝒆𝒏𝒕𝒐: {status_emoji} {payment_msg}
- - - - - - - - - - - - - - -
📩 𝑹𝒆𝒔𝒑𝒐𝒏𝒔𝒆: {json.dumps(payment_msg) if isinstance(payment_msg, dict) else payment_msg}
"""
        return response

# Global processor instance
braintree_processor = BraintreeProcessor()