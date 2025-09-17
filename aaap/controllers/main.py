from odoo import http
from odoo.http import request
import time
from datetime import datetime, timedelta

class AaapController(http.Controller):
    _recent_updates = {}
    _last_cleanup = time.time()
    MAX_CACHE_SIZE = 100

    def _cleanup_cache(self):
        """Ruim de cache op om geheugen problemen te voorkomen"""
        current_time = time.time()
        
        if current_time - self._last_cleanup < 60:
            return
            
        keys_to_remove = []
        for key, (timestamp, result) in self._recent_updates.items():
            if current_time - timestamp > 30:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self._recent_updates[key]
        
        if len(self._recent_updates) > self.MAX_CACHE_SIZE:
            sorted_items = sorted(self._recent_updates.items(), key=lambda x: x[1][0])
            items_to_remove = len(self._recent_updates) - self.MAX_CACHE_SIZE
            for i in range(items_to_remove):
                key = sorted_items[i][0]
                del self._recent_updates[key]
        
        self._last_cleanup = current_time

    @http.route('/aaap/clicker', auth='user', type='http')
    def aaap_clicker_game(self, **kw):
        self._cleanup_cache()
        
        # Haal alle apen op met hun game stats
        apen = request.env['aaap.plaats'].search_read([], [
            'id', 'name', 'aantal_reeds_gegeten_bananen', 'aantal_bots', 
            'click_multiplier', 'bananen_per_seconde', 'bot_level', 'multiplier_level'
        ])
        
        # Bereken kosten voor upgrades voor elke aap
        for aap in apen:
            aap_record = request.env['aaap.plaats'].browse(aap['id'])
            aap['bot_cost'] = aap_record.get_bot_cost()
            aap['multiplier_cost'] = aap_record.get_multiplier_upgrade_cost()
            aap['bot_upgrade_cost'] = aap_record.get_bot_upgrade_cost()
        
        return request.render('aaap.aaap_clicker_template', {
            'apen': apen
        })

    @http.route('/aaap/clicker/update', auth='user', type='json')
    def update_bananen(self, aap_id, bananen, request_id=None):
        """Update het aantal bananen voor een aap (met multiplier)"""
        self._cleanup_cache()
        
        if not aap_id:
            return {'success': False, 'error': 'Geen aap geselecteerd'}
        
        bananen = int(bananen)
        if bananen > 1000:  # Kleiner maximum voor veiligheid
            return {'success': False, 'error': 'Te veel bananen in één keer!'}
        
        if not request_id:
            request_id = str(time.time())
        
        cache_key = f"{request.env.user.id}_{aap_id}_{bananen}_{request_id}"
        current_time = time.time()
        
        if cache_key in self._recent_updates:
            timestamp, result = self._recent_updates[cache_key]
            if current_time - timestamp < 2:
                return result
        
        try:
            with request.env.registry.cursor() as new_cr:
                env = request.env(cr=new_cr)
                aap = env['aaap.plaats'].browse(int(aap_id))
                
                if not aap.exists():
                    return {'success': False, 'error': 'Aap niet gevonden'}
                
                # Pas eerst bot production toe
                self._apply_bot_production(aap, env)
                
                # Herlaad aap data na bot productie
                aap = env['aaap.plaats'].browse(int(aap_id))
                
                # Pas multiplier toe op clicked bananen
                bananen_with_multiplier = int(bananen * aap.click_multiplier)
                
                env.cr.execute("""
                    SELECT aantal_reeds_gegeten_bananen 
                    FROM aaap_plaats 
                    WHERE id = %s 
                    FOR UPDATE
                """, [int(aap_id)])
                
                huidige_bananen = env.cr.fetchone()[0] or 0
                nieuwe_totaal = huidige_bananen + bananen_with_multiplier
                
                env.cr.execute("""
                    UPDATE aaap_plaats 
                    SET aantal_reeds_gegeten_bananen = %s 
                    WHERE id = %s
                """, [nieuwe_totaal, int(aap_id)])
                
                new_cr.commit()
                
                result = {
                    'success': True, 
                    'nieuwe_waarde': nieuwe_totaal,
                    'bananen_toegevoegd': bananen_with_multiplier,
                    'multiplier': aap.click_multiplier,
                    'bananen_per_seconde': aap.bananen_per_seconde,
                    'debug_info': {
                        'voor_update': huidige_bananen,
                        'basis_bananen': bananen,
                        'met_multiplier': bananen_with_multiplier,
                        'verwacht_totaal': nieuwe_totaal
                    }
                }
                
                self._recent_updates[cache_key] = (current_time, result)
                return result
                
        except Exception as e:
            print(f"Fout bij updaten bananen: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}

    def _apply_bot_production(self, aap, env):
        """Pas bot productie toe gebaseerd op tijd sinds laatste update"""
        now = datetime.now()
        last_update = aap.laatste_bot_update or now
        
        # Bereken seconden sinds laatste update (max 1 uur om exploit te voorkomen)
        time_diff = min((now - last_update).total_seconds(), 3600)
        
        if time_diff > 0 and aap.aantal_bots > 0:
            # Gebruik bananen per minuut in plaats van per seconde voor betere waardes
            # 6 bananen per minuut per bot (0.1 per seconde)
            bpm = aap.aantal_bots * 6 * (1 + (aap.bot_level * 0.5))
            
            # Converteer minuten naar seconden voor de berekening
            bananen_per_seconde = bpm / 60.0
            
            # Bereken bananen
            bot_bananen = int(time_diff * bananen_per_seconde)
            
            # Sla bpm op voor weergave
            env.cr.execute("""
                UPDATE aaap_plaats 
                SET bananen_per_seconde = %s
                WHERE id = %s
            """, [bananen_per_seconde, aap.id])
            
            if bot_bananen > 0:
                env.cr.execute("""
                    UPDATE aaap_plaats 
                    SET aantal_reeds_gegeten_bananen = aantal_reeds_gegeten_bananen + %s,
                        laatste_bot_update = %s
                    WHERE id = %s
                """, [bot_bananen, now, aap.id])
            else:
                # Update alleen timestamp als er geen bananen zijn geproduceerd
                env.cr.execute("""
                    UPDATE aaap_plaats 
                    SET laatste_bot_update = %s
                    WHERE id = %s
                """, [now, aap.id])
    
    @http.route('/aaap/clicker/get-stats', auth='user', type='json')
    def get_aap_stats(self, aap_id, **kw):
        """Haal actuele stats op (voor real-time updates)"""
        self._cleanup_cache()
        
        try:
            aap = request.env['aaap.plaats'].browse(int(aap_id))
            
            if not aap.exists():
                return {'success': False, 'error': 'Aap niet gevonden'}
                
            # Pas bot production toe
            with request.env.registry.cursor() as new_cr:
                env = request.env(cr=new_cr)
                aap_copy = env['aaap.plaats'].browse(int(aap_id))
                self._apply_bot_production(aap_copy, env)
                new_cr.commit()
                
            # Refresh aap data
            aap = request.env['aaap.plaats'].browse(int(aap_id))
                
            return {
                'success': True,
                'bananen': aap.aantal_reeds_gegeten_bananen,
                'aantal_bots': aap.aantal_bots,
                'click_multiplier': aap.click_multiplier,
                'bananen_per_seconde': aap.bananen_per_seconde,
                'bot_level': aap.bot_level,
                'multiplier_level': aap.multiplier_level,
                'bot_cost': aap.get_bot_cost(),
                'bot_upgrade_cost': aap.get_bot_upgrade_cost(),
                'multiplier_cost': aap.get_multiplier_upgrade_cost()
            }
                
        except Exception as e:
            print(f"Fout bij ophalen stats: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}
        
    @http.route('/aaap/clicker/buy-bot', auth='user', type='json')
    def buy_bot(self, aap_id, **kw):
        """Koop een bot voor automatische bananen productie"""
        if not aap_id:
            return {'success': False, 'error': 'Geen aap geselecteerd'}
        
        try:
            with request.env.registry.cursor() as new_cr:
                env = request.env(cr=new_cr)
                aap = env['aaap.plaats'].browse(int(aap_id))
                
                if not aap.exists():
                    return {'success': False, 'error': 'Aap niet gevonden'}
                
                # Pas bot productie toe voordat we kosten berekenen
                self._apply_bot_production(aap, env)
                
                # Herlaad aap data na bot productie - gebruik fresh browse
                aap = env['aaap.plaats'].browse(int(aap_id))
                
                bot_cost = aap.get_bot_cost()
                
                if aap.aantal_reeds_gegeten_bananen < bot_cost:
                    return {
                        'success': False, 
                        'error': f'Niet genoeg bananen! Je hebt {aap.aantal_reeds_gegeten_bananen}, maar {bot_cost} zijn nodig.'
                    }
                
                # In de buy_bot functie:
                
                # Koop de bot
                nieuwe_bananen = aap.aantal_reeds_gegeten_bananen - bot_cost
                nieuwe_bots = aap.aantal_bots + 1
                
                # Bereken bananen per minuut (6 per bot)
                bot_efficiency = 6 * (1 + (aap.bot_level * 0.5))
                bananen_per_minuut = nieuwe_bots * bot_efficiency
                bananen_per_seconde = bananen_per_minuut / 60.0
                
                env.cr.execute("""
                    UPDATE aaap_plaats 
                    SET aantal_reeds_gegeten_bananen = %s,
                        aantal_bots = %s,
                        bananen_per_seconde = %s
                    WHERE id = %s
                """, [nieuwe_bananen, nieuwe_bots, bananen_per_seconde, aap.id])
                
                
                new_cr.commit()
                
                # Bereken nieuwe kosten en stats
                nieuwe_bot_cost = int(bot_cost * 1.5)
                bot_efficiency = 0.1 * (1 + (aap.bot_level * 0.5))
                nieuwe_bananen_per_seconde = nieuwe_bots * bot_efficiency
                
                return {
                    'success': True,
                    'nieuwe_bananen': nieuwe_bananen,
                    'aantal_bots': nieuwe_bots,
                    'nieuwe_bot_cost': nieuwe_bot_cost,
                    'bananen_per_seconde': nieuwe_bananen_per_seconde
                }
                
        except Exception as e:
            print(f"Fout bij kopen bot: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}
    
    @http.route('/aaap/clicker/upgrade-multiplier', auth='user', type='json')
    def upgrade_multiplier(self, aap_id, **kw):
        """Upgrade de click multiplier"""
        if not aap_id:
            return {'success': False, 'error': 'Geen aap geselecteerd'}
        
        try:
            with request.env.registry.cursor() as new_cr:
                env = request.env(cr=new_cr)
                aap = env['aaap.plaats'].browse(int(aap_id))
                
                if not aap.exists():
                    return {'success': False, 'error': 'Aap niet gevonden'}
                
                self._apply_bot_production(aap, env)
                # Herlaad aap data
                aap = env['aaap.plaats'].browse(int(aap_id))
                
                upgrade_cost = aap.get_multiplier_upgrade_cost()
                
                if aap.aantal_reeds_gegeten_bananen < upgrade_cost:
                    return {
                        'success': False, 
                        'error': f'Niet genoeg bananen! Je hebt {aap.aantal_reeds_gegeten_bananen}, maar {upgrade_cost} zijn nodig.'
                    }
                
                nieuwe_bananen = aap.aantal_reeds_gegeten_bananen - upgrade_cost
                nieuwe_level = aap.multiplier_level + 1
                nieuwe_multiplier = 1.0 + (nieuwe_level * 0.25)  # +25% per level
                
                env.cr.execute("""
                    UPDATE aaap_plaats 
                    SET aantal_reeds_gegeten_bananen = %s,
                        multiplier_level = %s,
                        click_multiplier = %s
                    WHERE id = %s
                """, [nieuwe_bananen, nieuwe_level, nieuwe_multiplier, aap.id])
                
                new_cr.commit()
                
                nieuwe_upgrade_cost = int(upgrade_cost * 2)
                
                return {
                    'success': True,
                    'nieuwe_bananen': nieuwe_bananen,
                    'multiplier_level': nieuwe_level,
                    'click_multiplier': nieuwe_multiplier,
                    'nieuwe_upgrade_cost': nieuwe_upgrade_cost
                }
                
        except Exception as e:
            print(f"Fout bij upgrade multiplier: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}
    
    @http.route('/aaap/clicker/upgrade-bots', auth='user', type='json')
    def upgrade_bots(self, aap_id, **kw):
        """Upgrade bot efficiency"""
        if not aap_id:
            return {'success': False, 'error': 'Geen aap geselecteerd'}
        
        try:
            with request.env.registry.cursor() as new_cr:
                env = request.env(cr=new_cr)
                aap = env['aaap.plaats'].browse(int(aap_id))
                
                if not aap.exists():
                    return {'success': False, 'error': 'Aap niet gevonden'}
                
                self._apply_bot_production(aap, env)
                # Herlaad aap data
                aap = env['aaap.plaats'].browse(int(aap_id))
                
                upgrade_cost = aap.get_bot_upgrade_cost()
                
                if aap.aantal_reeds_gegeten_bananen < upgrade_cost:
                    return {
                        'success': False, 
                        'error': f'Niet genoeg bananen! Je hebt {aap.aantal_reeds_gegeten_bananen}, maar {upgrade_cost} zijn nodig.'
                    }
                
                nieuwe_bananen = aap.aantal_reeds_gegeten_bananen - upgrade_cost
                nieuwe_bot_level = aap.bot_level + 1
                
                env.cr.execute("""
                    UPDATE aaap_plaats 
                    SET aantal_reeds_gegeten_bananen = %s,
                        bot_level = %s
                    WHERE id = %s
                """, [nieuwe_bananen, nieuwe_bot_level, aap.id])
                
                new_cr.commit()
                
                # Herbereken bananen per seconde
                bot_efficiency = 0.1 * (1 + (nieuwe_bot_level * 0.5))
                nieuwe_bananen_per_seconde = aap.aantal_bots * bot_efficiency
                
                return {
                    'success': True,
                    'nieuwe_bananen': nieuwe_bananen,
                    'bot_level': nieuwe_bot_level,
                    'bananen_per_seconde': nieuwe_bananen_per_seconde,
                    'nieuwe_upgrade_cost': int(upgrade_cost * 3)
                }
                
        except Exception as e:
            print(f"Fout bij upgrade bots: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}
