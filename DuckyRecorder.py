"""
Gravador de eventos para automação com Arduino Leonardo ATmega32u4
Versão corrigida com exportação robusta e menu colorido
"""
import json
import threading
import time
import os
import sys
import random
from datetime import datetime
from pynput import keyboard, mouse
from pynput.keyboard import Key, KeyCode
from pynput.mouse import Button

# ============================================================================
# CROSS-PLATFORM COLOR SUPPORT (Linux, Windows, macOS)
# ============================================================================
class Colors:
    """Cores ANSI compatíveis com Linux, macOS e Windows 10+"""
    # Reset
    RESET = '\033[0m'
    
    # Cores básicas
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Bright colors
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'
    
    # Estilos
    BOLD = '\033[1m'
    DIM = '\033[2m'
    UNDERLINE = '\033[4m'
    BLINK = '\033[5m'
    REVERSE = '\033[7m'
    
    # Background colors
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'

# Para Windows, tentamos inicializar colorama se disponível
if sys.platform == 'win32':
    try:
        import colorama
        colorama.init()
        # Sobrescrevemos as cores com colorama
        Colors.RESET = colorama.Style.RESET_ALL
        Colors.BOLD = colorama.Style.BRIGHT
    except ImportError:
        # Colorama não instalado, usamos ANSI padrão (Windows 10+ suporta)
        pass

# Funções auxiliares de cor
def color_text(text, color_code):
    """Retorna texto colorido"""
    return f"{color_code}{text}{Colors.RESET}"

def print_color(text, color_code):
    """Imprime texto colorido"""
    print(color_text(text, color_code))

# ============================================================================
# EVENT RECORDER CLASS
# ============================================================================
class EventRecorder:
    def __init__(self):
        self.events = []
        self.start_time = None
        self.is_recording = False
        self.paused = False
        self.filename = None
        self.last_mouse_pos = (0, 0)
        self.current_modifiers = set()
        
        # Estado dos modificadores durante gravação
        self.active_modifiers = {
            'SHIFT': False,
            'CTRL': False,
            'ALT': False,
            'GUI': False
        }
        
        # Configurações
        self.record_mouse_moves = True
        self.min_mouse_move = 5
        self.mouse_move_interval = 50
        self.last_move_time = 0
        
        # Informações da tela
        try:
            import screeninfo
            monitors = screeninfo.get_monitors()
            if monitors:
                self.screen_width = monitors[0].width
                self.screen_height = monitors[0].height
            else:
                self.screen_width = 1920
                self.screen_height = 1080
        except ImportError:
            self.screen_width = 1920
            self.screen_height = 1080
        
        # Listeners
        self.keyboard_listener = None
        self.mouse_listener = None
    
    def clear_events(self):
        """Limpa todos os eventos"""
        self.events.clear()
        self.last_mouse_pos = (0, 0)
        self.current_modifiers.clear()
        self.active_modifiers = {k: False for k in self.active_modifiers}
        print_color("✓ Eventos limpos", Colors.GREEN)
    
    def start_recording(self, filename=None):
        """Inicia a gravação"""
        if self.is_recording:
            print_color("⚠ Já está gravando!", Colors.YELLOW)
            return False
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"recording_{timestamp}.json"
        
        self.filename = filename
        self.start_time = time.time()
        self.is_recording = True
        self.paused = False
        self.last_move_time = 0
        self.current_modifiers.clear()
        self.active_modifiers = {k: False for k in self.active_modifiers}
        
        # Inicia listeners
        self.keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )
        self.mouse_listener = mouse.Listener(
            on_click=self._on_click,
            on_move=self._on_move,
            on_scroll=self._on_scroll
        )
        
        self.keyboard_listener.start()
        self.mouse_listener.start()
        
        # Evento inicial
        self._add_event({
            "type": "start",
            "t": 0,
            "timestamp": datetime.now().isoformat(),
            "screen_width": self.screen_width,
            "screen_height": self.screen_height,
            "info": "Início da gravação"
        })
        
        print_color(f"🎥 Gravação iniciada: {filename}", Colors.CYAN)
        print_color("   Pressione F1 para pausar/continuar", Colors.BRIGHT_BLUE)
        print_color("   Pressione ESC para parar", Colors.BRIGHT_BLUE)
        return True
    
    def pause_recording(self):
        """Pausa/Continua a gravação"""
        if not self.is_recording:
            return
        
        self.paused = not self.paused
        if self.paused:
            self._add_event({
                "type": "pause",
                "t": self._get_elapsed_ms(),
                "info": "Gravação pausada"
            })
            print_color("⏸ Gravação pausada", Colors.YELLOW)
        else:
            self._add_event({
                "type": "resume",
                "t": self._get_elapsed_ms(),
                "info": "Gravação continuada"
            })
            print_color("▶ Gravação continuada", Colors.GREEN)
    
    def stop_recording(self):
        """Para a gravação"""
        if not self.is_recording:
            return
        
        # Libera modificadores se ainda estiverem pressionados
        for modifier in list(self.current_modifiers):
            self._add_key_event("up", modifier, None)
        
        self._add_event({
            "type": "stop",
            "t": self._get_elapsed_ms(),
            "duration": self._get_elapsed_ms(),
            "info": "Fim da gravação"
        })
        
        self.is_recording = False
        self.paused = False
        
        if self.keyboard_listener:
            self.keyboard_listener.stop()
        if self.mouse_listener:
            self.mouse_listener.stop()
        
        duration = self._get_elapsed_ms() / 1000
        print_color(f"⏹ Gravação finalizada. Duração: {duration:.1f}s", Colors.GREEN)
        print_color(f"   Total de eventos: {len(self.events)}", Colors.BRIGHT_BLUE)
        
        return True
    
    def _get_elapsed_ms(self):
        """Retorna tempo em ms desde o início"""
        if not self.start_time:
            return 0
        return int((time.time() - self.start_time) * 1000)
    
    def _add_event(self, event):
        """Adiciona evento à lista"""
        if self.is_recording and not self.paused:
            self.events.append(event)
    
    def _add_key_event(self, event_type, key_str, key_obj=None):
        """Adiciona evento de teclado"""
        event = {
            "type": f"key_{event_type}",
            "key": key_str,
            "t": self._get_elapsed_ms()
        }
        
        if key_obj:
            event["modifier"] = self._is_modifier(key_obj)
            event["scan_code"] = getattr(key_obj, 'vk', None) if hasattr(key_obj, 'vk') else None
        
        self._add_event(event)
    
    def _is_modifier(self, key):
        """Verifica se é uma tecla modificadora"""
        modifiers = {
            Key.shift, Key.shift_r, Key.shift_l,
            Key.ctrl, Key.ctrl_l, Key.ctrl_r,
            Key.alt, Key.alt_l, Key.alt_r,
            Key.cmd, Key.cmd_l, Key.cmd_r
        }
        return key in modifiers
    
    def _update_modifier_state(self, key_str, pressed):
        """Atualiza estado dos modificadores"""
        key_upper = key_str.upper()
        if 'SHIFT' in key_upper:
            self.active_modifiers['SHIFT'] = pressed
        elif 'CTRL' in key_upper:
            self.active_modifiers['CTRL'] = pressed
        elif 'ALT' in key_upper:
            self.active_modifiers['ALT'] = pressed
        elif 'GUI' in key_upper or 'CMD' in key_upper:
            self.active_modifiers['GUI'] = pressed
    
    def _key_to_str(self, key):
        """Converte tecla para string padronizada"""
        if isinstance(key, KeyCode):
            if key.char:
                special_chars = {
                    '\t': 'TAB',
                    '\n': 'ENTER',
                    '\r': 'ENTER',
                    ' ': 'SPACE',
                    '\x1b': 'ESC',
                    '\x08': 'BACKSPACE',
                    '\x7f': 'DELETE'
                }
                return special_chars.get(key.char, key.char)
            return f"KEYCODE_{key.vk}" if hasattr(key, 'vk') else str(key)
        
        if isinstance(key, Key):
            name = str(key).replace("Key.", "")
            arduino_map = {
                'esc': 'ESC',
                'enter': 'ENTER',
                'tab': 'TAB',
                'space': 'SPACE',
                'backspace': 'BACKSPACE',
                'delete': 'DELETE',
                'shift': 'SHIFT_LEFT',
                'shift_r': 'SHIFT_RIGHT',
                'shift_l': 'SHIFT_LEFT',
                'ctrl': 'CTRL_LEFT',
                'ctrl_r': 'CTRL_RIGHT',
                'ctrl_l': 'CTRL_LEFT',
                'alt': 'ALT_LEFT',
                'alt_r': 'ALT_RIGHT',
                'alt_l': 'ALT_LEFT',
                'cmd': 'GUI_LEFT',
                'cmd_r': 'GUI_RIGHT',
                'cmd_l': 'GUI_LEFT',
                'up': 'UP_ARROW',
                'down': 'DOWN_ARROW',
                'left': 'LEFT_ARROW',
                'right': 'RIGHT_ARROW',
                'f1': 'F1',
                'f2': 'F2',
                'f3': 'F3',
                'f4': 'F4',
                'f5': 'F5',
                'f6': 'F6',
                'f7': 'F7',
                'f8': 'F8',
                'f9': 'F9',
                'f10': 'F10',
                'f11': 'F11',
                'f12': 'F12',
                'home': 'HOME',
                'end': 'END',
                'page_up': 'PAGE_UP',
                'page_down': 'PAGE_DOWN',
                'caps_lock': 'CAPS_LOCK',
                'num_lock': 'NUM_LOCK',
                'print_screen': 'PRINT_SCREEN',
                'scroll_lock': 'SCROLL_LOCK',
                'pause': 'PAUSE',
                'insert': 'INSERT',
                'menu': 'MENU'
            }
            return arduino_map.get(name, name.upper())
        
        return str(key)
    
    def _on_key_press(self, key):
        """Callback para tecla pressionada"""
        if not self.is_recording or self.paused:
            return
        
        key_str = self._key_to_str(key)
        
        if key == Key.esc:
            self.stop_recording()
            return False
        
        if key == Key.f1:
            self.pause_recording()
            return
        
        if self._is_modifier(key):
            if key_str not in self.current_modifiers:
                self.current_modifiers.add(key_str)
                self._update_modifier_state(key_str, True)
                self._add_key_event("down", key_str, key)
            return
        
        # Para caracteres normais, aplica estado dos modificadores
        if isinstance(key, KeyCode) and key.char:
            if self.active_modifiers['SHIFT'] and key.char.isalpha():
                key_str = key.char.upper()
            elif self.active_modifiers['SHIFT']:
                # Mapeia caracteres especiais com Shift
                shift_map = {
                    '`': '~', '1': '!', '2': '@', '3': '#', '4': '$',
                    '5': '%', '6': '^', '7': '&', '8': '*', '9': '(',
                    '0': ')', '-': '_', '=': '+', '[': '{', ']': '}',
                    '\\': '|', ';': ':', "'": '"', ',': '<', '.': '>',
                    '/': '?'
                }
                key_str = shift_map.get(key.char, key.char)
            else:
                key_str = key.char
        
        self._add_key_event("down", key_str, key)
    
    def _on_key_release(self, key):
        """Callback para tecla liberada"""
        if not self.is_recording or self.paused:
            return
        
        key_str = self._key_to_str(key)
        
        if self._is_modifier(key):
            if key_str in self.current_modifiers:
                self.current_modifiers.remove(key_str)
                self._update_modifier_state(key_str, False)
                self._add_key_event("up", key_str, key)
            return
        
        self._add_key_event("up", key_str, key)
    
    def _on_click(self, x, y, button, pressed):
        """Callback para clique do mouse"""
        if not self.is_recording or self.paused:
            return
        
        button_map = {
            Button.left: "LEFT",
            Button.right: "RIGHT",
            Button.middle: "MIDDLE"
        }
        
        button_str = button_map.get(button, str(button))
        event_type = "down" if pressed else "up"
        
        self._add_event({
            "type": f"mouse_{event_type}",
            "button": button_str,
            "x": x,
            "y": y,
            "norm_x": x / self.screen_width if self.screen_width > 0 else 0,
            "norm_y": y / self.screen_height if self.screen_height > 0 else 0,
            "t": self._get_elapsed_ms()
        })
        
        self.last_mouse_pos = (x, y)
    
    def _on_move(self, x, y):
        """Callback para movimento do mouse"""
        if not self.is_recording or self.paused or not self.record_mouse_moves:
            return
        
        current_time = time.time()
        elapsed = (current_time - self.last_move_time) * 1000
        
        if elapsed < self.mouse_move_interval:
            return
        
        last_x, last_y = self.last_mouse_pos
        dx, dy = x - last_x, y - last_y
        
        if abs(dx) < self.min_mouse_move and abs(dy) < self.min_mouse_move:
            return
        
        self.last_move_time = current_time
        self.last_mouse_pos = (x, y)
        
        self._add_event({
            "type": "mouse_move",
            "x": x,
            "y": y,
            "dx": dx,
            "dy": dy,
            "norm_x": x / self.screen_width if self.screen_width > 0 else 0,
            "norm_y": y / self.screen_height if self.screen_height > 0 else 0,
            "t": self._get_elapsed_ms()
        })
    
    def _on_scroll(self, x, y, dx, dy):
        """Callback para scroll do mouse"""
        if not self.is_recording or self.paused:
            return
        
        self._add_event({
            "type": "mouse_scroll",
            "x": x,
            "y": y,
            "dx": dx,
            "dy": dy,
            "t": self._get_elapsed_ms()
        })
    
    def save_recording(self, filename=None, ask_confirmation=True):
        """Salva gravação em arquivo JSON"""
        if not self.events:
            print_color("⚠ Nenhum evento para salvar!", Colors.YELLOW)
            return False
        
        filename = filename or self.filename
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"recording_{timestamp}.json"
        
        # Se o arquivo já existe e ask_confirmation é True, pergunta
        if ask_confirmation and os.path.exists(filename):
            overwrite = input(f"Arquivo '{filename}' já existe. Sobrescrever? (s/n): ").strip().lower()
            if overwrite != 's':
                new_name = input("Novo nome do arquivo: ").strip()
                if new_name:
                    if not new_name.endswith('.json'):
                        new_name += '.json'
                    filename = new_name
        
        # Calcula delays entre eventos
        events_with_delays = []
        last_time = 0
        
        for event in self.events:
            current_time = event["t"]
            delay = current_time - last_time
            event_copy = event.copy()
            event_copy["delay"] = delay
            events_with_delays.append(event_copy)
            last_time = current_time
        
        metadata = {
            "created": datetime.now().isoformat(),
            "total_events": len(self.events),
            "duration_ms": last_time,
            "arduino_target": "Leonardo ATmega32u4",
            "format_version": "1.2",
            "screen_width": self.screen_width,
            "screen_height": self.screen_height,
            "platform": sys.platform
        }
        
        output = {
            "metadata": metadata,
            "events": events_with_delays
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(output, f, indent=2, ensure_ascii=False)
            print_color(f"✓ Gravação salva em: {filename}", Colors.GREEN)
            self.filename = filename
            return True
        except Exception as e:
            print_color(f"✗ Erro ao salvar: {e}", Colors.RED)
            return False
    
    def load_recording(self, filename):
        """Carrega gravação de arquivo"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.events = data.get("events", [])
            self.filename = filename
            
            # Carrega metadados se disponíveis
            if "metadata" in data:
                meta = data["metadata"]
                print_color(f"✓ Gravação carregada: {filename}", Colors.GREEN)
                print_color(f"   Eventos: {len(self.events)}", Colors.BRIGHT_BLUE)
                duration_sec = meta.get('duration_ms', 0) / 1000
                print_color(f"   Duração: {duration_sec:.1f}s", Colors.BRIGHT_BLUE)
                if 'screen_width' in meta and 'screen_height' in meta:
                    self.screen_width = meta['screen_width']
                    self.screen_height = meta['screen_height']
            return True
        except Exception as e:
            print_color(f"✗ Erro ao carregar: {e}", Colors.RED)
            return False
    
    # ============================================================================
    # FUNÇÕES DE EXPORTAÇÃO CORRIGIDAS (VERSÃO ROBUSTA)
    # ============================================================================
    
    def export_for_arduino(self, output_filename=None):
        """Exporta para formato Arduino (.json + .ino) — versão corrigida"""
        if not self.events:
            print_color("⚠ Nenhum evento para exportar!", Colors.YELLOW)
            return False

        arduino_events = []
        # Usa delays gravados (campo 'delay' que você já produz em save_recording)
        for event in self.events:
            delay = int(event.get("delay", 0))
            etype = event.get("type", "")

            if etype in ("key_down", "key_up"):
                key = event.get("key", "")
                arduino_key = self._to_arduino_keycode(key)
                if not arduino_key:
                    # caractere não mapeado: tenta usar literal se for 1-char
                    if len(key) == 1:
                        arduino_key = f"'{self._escape_char(key)}'"
                    else:
                        # não mapeado, ignora
                        print_color(f"⚠ Aviso: tecla não mapeada ignorada: {key}", Colors.YELLOW)
                        continue
                evt = {"delay": delay, "type": "KEY_PRESS" if etype=="key_down" else "KEY_RELEASE", "key": arduino_key}
                arduino_events.append(evt)

            elif etype.startswith("mouse_"):
                if etype == "mouse_move":
                    dx = int(event.get("dx", 0))
                    dy = int(event.get("dy", 0))
                    moves = self._split_mouse_move(dx, dy, max_step=127)
                    # primeiro sub-movimento mantém o delay, os seguintes têm delay 0
                    first = True
                    for m in moves:
                        evt = {"delay": delay if first else 0, "type": "MOUSE_MOVE", "dx": m["dx"], "dy": m["dy"]}
                        arduino_events.append(evt)
                        first = False
                        delay = 0
                elif etype in ("mouse_down","mouse_up"):
                    button_map = {"LEFT":"MOUSE_LEFT","RIGHT":"MOUSE_RIGHT","MIDDLE":"MOUSE_MIDDLE"}
                    button = button_map.get(event.get("button","LEFT"), "MOUSE_LEFT")
                    typ = "MOUSE_PRESS" if etype=="mouse_down" else "MOUSE_RELEASE"
                    arduino_events.append({"delay": delay, "type": typ, "button": button})
                elif etype == "mouse_scroll":
                    dy = int(event.get("dy", 0))
                    # mapeia dy para wheel amount (ajuste sensibilidade)
                    if dy != 0:
                        arduino_events.append({"delay": delay, "type": "MOUSE_SCROLL", "amount": int(dy * 3)})
            elif etype in ("start","stop","pause","resume"):
                # ignora controle
                continue
            else:
                # evento desconhecido
                print_color(f"⚠ Evento desconhecido ignorado: {etype}", Colors.YELLOW)

        # Otimiza delays: converte delays muito pequenos para 0
        for ev in arduino_events:
            if ev.get("delay", 0) < 10:  # menos de 10ms
                ev["delay"] = 0
        
        # Salva arquivos
        base = os.path.splitext(self.filename)[0] if self.filename else f"recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        out_json = output_filename or f"{base}_arduino.json"
        
        try:
            with open(out_json, 'w', encoding='utf-8') as f:
                json.dump({
                    "metadata": {
                        "exported": datetime.now().isoformat(), 
                        "events": len(arduino_events),
                        "arduino_type": "Leonardo ATmega32u4"
                    }, 
                    "events": arduino_events
                }, f, indent=2)
            
            # gera .ino
            ino_name = out_json.replace('.json', '.ino')
            self._generate_arduino_example(ino_name, arduino_events)
            
            print_color(f"✓ Exportado para Arduino: {out_json}  (-> {ino_name})", Colors.GREEN)
            return True
        except Exception as e:
            print_color(f"✗ Erro ao exportar: {e}", Colors.RED)
            return False

    def _generate_arduino_example(self, filename, events):
        """Gera um .ino robusto a partir da lista de events"""
        template_top = """/*
 * Código gerado automaticamente pelo gravador
 * Arduino Leonardo ATmega32u4
 */
#include <Keyboard.h>
#include <Mouse.h>

void setup() {
  // espere tempo pra você selecionar a janela/VM (ajuste se precisar)
  delay(3000);
  Keyboard.begin();
  Mouse.begin();
  executeEvents();
  // garante liberar tudo para evitar teclas travadas
  Keyboard.releaseAll();
  Mouse.release(MOUSE_LEFT);
  Mouse.release(MOUSE_RIGHT);
  Mouse.release(MOUSE_MIDDLE);
}

void loop() {
  while(1); // faz uma execução única
}

void executeEvents() {
"""
        template_bottom = """
} // executeEvents
"""

        def c_escape_char(ch):
            esc = self._escape_char(ch)
            return esc

        lines = [template_top]

        for ev in events:
            d = int(ev.get("delay", 0))
            if d > 0:
                lines.append(f"  delay({d});")
            typ = ev.get("type")
            if typ == "KEY_PRESS":
                k = ev.get("key", "")
                if isinstance(k, str) and k.startswith("'") and k.endswith("'") and len(k) >= 3:
                    ch = k.strip("'")
                    esc = c_escape_char(ch)
                    lines.append(f"  Keyboard.write('{esc}');")
                else:
                    lines.append(f"  Keyboard.press({k});")
            elif typ == "KEY_RELEASE":
                k = ev.get("key", "")
                # só release se for tecla especial (não char)
                if not (isinstance(k, str) and k.startswith("'") and k.endswith("'")):
                    lines.append(f"  Keyboard.release({k});")
            elif typ == "MOUSE_MOVE":
                dx = int(ev.get("dx", 0))
                dy = int(ev.get("dy", 0))
                lines.append(f"  Mouse.move({dx}, {dy}, 0);")
            elif typ == "MOUSE_PRESS":
                btn = ev.get("button", "MOUSE_LEFT")
                lines.append(f"  Mouse.press({btn});")
            elif typ == "MOUSE_RELEASE":
                btn = ev.get("button", "MOUSE_LEFT")
                lines.append(f"  Mouse.release({btn});")
            elif typ == "MOUSE_SCROLL":
                amt = int(ev.get("amount", 0))
                # utiliza o terceiro argumento (wheel)
                lines.append(f"  Mouse.move(0, 0, {amt});")
            else:
                lines.append(f"  // Evento desconhecido: {typ}")

        lines.append(template_bottom)

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("\n".join(lines))
            print_color(f"✓ Exemplo Arduino gerado: {filename}", Colors.GREEN)
        except Exception as e:
            print_color(f"✗ Erro ao gerar exemplo: {e}", Colors.RED)

    def _to_arduino_keycode(self, key):
        """Converte string de tecla para código Arduino"""
        key_map = {
            'ESC': 'KEY_ESC',
            'ENTER': 'KEY_RETURN',
            'TAB': 'KEY_TAB',
            'SPACE': 'KEY_SPACE',
            'BACKSPACE': 'KEY_BACKSPACE',
            'DELETE': 'KEY_DELETE',
            'SHIFT_LEFT': 'KEY_LEFT_SHIFT',
            'SHIFT_RIGHT': 'KEY_RIGHT_SHIFT',
            'CTRL_LEFT': 'KEY_LEFT_CTRL',
            'CTRL_RIGHT': 'KEY_RIGHT_CTRL',
            'ALT_LEFT': 'KEY_LEFT_ALT',
            'ALT_RIGHT': 'KEY_RIGHT_ALT',
            'GUI_LEFT': 'KEY_LEFT_GUI',
            'GUI_RIGHT': 'KEY_RIGHT_GUI',
            'UP_ARROW': 'KEY_UP_ARROW',
            'DOWN_ARROW': 'KEY_DOWN_ARROW',
            'LEFT_ARROW': 'KEY_LEFT_ARROW',
            'RIGHT_ARROW': 'KEY_RIGHT_ARROW',
            'F1': 'KEY_F1',
            'F2': 'KEY_F2',
            'F3': 'KEY_F3',
            'F4': 'KEY_F4',
            'F5': 'KEY_F5',
            'F6': 'KEY_F6',
            'F7': 'KEY_F7',
            'F8': 'KEY_F8',
            'F9': 'KEY_F9',
            'F10': 'KEY_F10',
            'F11': 'KEY_F11',
            'F12': 'KEY_F12',
            'HOME': 'KEY_HOME',
            'END': 'KEY_END',
            'PAGE_UP': 'KEY_PAGE_UP',
            'PAGE_DOWN': 'KEY_PAGE_DOWN',
            'CAPS_LOCK': 'KEY_CAPS_LOCK',
            'NUM_LOCK': 'KEY_NUM_LOCK',
            'PRINT_SCREEN': 'KEY_PRINT_SCREEN',
            'SCROLL_LOCK': 'KEY_SCROLL_LOCK',
            'PAUSE': 'KEY_PAUSE',
            'INSERT': 'KEY_INSERT',
            'MENU': 'KEY_MENU',
            'TAB': 'KEY_TAB'
        }
        
        if len(key) == 1:
            return f"'{self._escape_char(key)}'"
        
        return key_map.get(key, None)
    
    def _escape_char(self, char):
        """Escapa caracteres especiais para C++"""
        escapes = {
            '\n': '\\n',
            '\r': '\\r',
            '\t': '\\t',
            '\'': '\\\'',
            '"': '\\"',
            '\\': '\\\\',
            '\a': '\\a',
            '\b': '\\b',
            '\f': '\\f',
            '\v': '\\v'
        }
        return escapes.get(char, char)
    
    def _split_mouse_move(self, dx, dy, max_step=127):
        """Divide movimento grande em passos menores"""
        moves = []
        
        # Calcula número de passos necessários para cada eixo
        steps_x = self._calculate_steps(dx, max_step)
        steps_y = self._calculate_steps(dy, max_step)
        
        # Combina os passos
        max_steps = max(len(steps_x), len(steps_y))
        for i in range(max_steps):
            step_x = steps_x[i] if i < len(steps_x) else 0
            step_y = steps_y[i] if i < len(steps_y) else 0
            moves.append({"dx": step_x, "dy": step_y})
        
        return moves
    
    def _calculate_steps(self, value, max_step):
        """Calcula passos para um valor"""
        if value == 0:
            return []
        
        steps = []
        remaining = abs(value)
        direction = 1 if value > 0 else -1
        
        while remaining > 0:
            step = min(remaining, max_step)
            steps.append(step * direction)
            remaining -= step
        
        return steps

# ============================================================================
# INTERACTIVE MENU WITH COLORS
# ============================================================================
class Menu:
    def __init__(self):
        self.recorder = EventRecorder()
        self.current_file = None
        self.auto_save = True
    
    def clear_screen(self):
        """Limpa a tela de forma cross-platform"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def display_header(self, title):
        """Exibe cabeçalho colorido"""
        print(color_text("=" * 60, Colors.CYAN + Colors.BOLD))
        print(color_text(f"  {title}", Colors.CYAN + Colors.BOLD))
        print(color_text("=" * 60, Colors.CYAN + Colors.BOLD))
        print()
    
    def display_menu(self):
        """Exibe o menu principal"""
        self.clear_screen()
        self.display_header("GRAVADOR PARA ARDUINO LEONARDO - Menu Principal")
        
        # Status
        if self.recorder.is_recording:
            status_icon = color_text("🎥", Colors.GREEN)
            status_text = color_text("GRAVANDO", Colors.GREEN + Colors.BOLD)
            if self.recorder.paused:
                status_icon = color_text("⏸", Colors.YELLOW)
                status_text = color_text("PAUSADO", Colors.YELLOW + Colors.BOLD)
            
            print(f"Status: {status_icon} {status_text}")
            print(f"Eventos: {color_text(str(len(self.recorder.events)), Colors.BRIGHT_BLUE)}")
            elapsed = self.recorder._get_elapsed_ms() / 1000
            print(f"Duração: {color_text(f'{elapsed:.1f}s', Colors.BRIGHT_BLUE)}")
        else:
            print(f"Status: {color_text('Pronto', Colors.BRIGHT_GREEN)}")
            if self.current_file:
                print(f"Arquivo atual: {color_text(self.current_file, Colors.BRIGHT_CYAN)}")
        
        print()
        print(color_text("Opções:", Colors.BOLD + Colors.WHITE))
        
        # Opções do menu com cores e ícones
        options = [
            ("1", "▶", "Iniciar nova gravação", Colors.GREEN),
            ("2", "⏸", "Pausar/Continuar gravação (F1 durante gravação)", Colors.YELLOW),
            ("3", "⏹", "Parar gravação", Colors.RED),
            ("4", "💾", "Salvar gravação atual", Colors.BLUE),
            ("5", "📂", "Carregar gravação", Colors.MAGENTA),
            ("6", "🔄", "Exportar para Arduino", Colors.CYAN),
            ("7", "📊", "Visualizar eventos", Colors.BRIGHT_WHITE),
            ("8", "🗑", "Limpar eventos", Colors.BRIGHT_RED),
            ("9", "⚙️", "Configurações", Colors.BRIGHT_YELLOW),
            ("0", "❌", "Sair", Colors.BRIGHT_RED + Colors.BOLD)
        ]
        
        for num, icon, text, color in options:
            print(f"  {color_text(num, color)} {icon}  {color_text(text, color)}")
        
        print()
        print(color_text("=" * 60, Colors.CYAN))
    
    def get_choice(self):
        """Obtém escolha do usuário"""
        try:
            choice = input(color_text("\nEscolha uma opção (0-9): ", Colors.BRIGHT_WHITE)).strip()
            return choice
        except (EOFError, KeyboardInterrupt):
            return '0'
    
    def handle_choice(self, choice):
        """Processa a escolha do menu"""
        if choice == '1':
            self.start_recording()
        elif choice == '2':
            self.recorder.pause_recording()
            if self.recorder.paused:
                input(color_text("\nGravação pausada. Pressione Enter para continuar...", Colors.YELLOW))
        elif choice == '3':
            self.stop_recording()
        elif choice == '4':
            self.save_recording()
        elif choice == '5':
            self.load_recording()
        elif choice == '6':
            self.export_for_arduino()
        elif choice == '7':
            self.view_events()
        elif choice == '8':
            self.clear_events()
        elif choice == '9':
            self.settings()
        elif choice == '0':
            return False
        else:
            print_color("Opção inválida!", Colors.RED)
            time.sleep(1)
            return True
        
        return True
    
    def start_recording(self):
        """Inicia nova gravação"""
        if self.recorder.is_recording:
            print_color("Já existe uma gravação em andamento!", Colors.YELLOW)
            return
        
        print()
        filename = input(color_text("Nome do arquivo (deixe em branco para automático): ", Colors.BRIGHT_CYAN)).strip()
        if not filename:
            filename = None
        
        print()
        print_color("📝 Dicas:", Colors.BRIGHT_WHITE)
        print_color("  • Durante a gravação, use F1 para pausar/continuar", Colors.BRIGHT_BLUE)
        print_color("  • Use ESC para parar a gravação", Colors.BRIGHT_BLUE)
        print_color("  • Movimentos do mouse são gravados a cada 50ms", Colors.BRIGHT_BLUE)
        print()
        print_color("Iniciando gravação em 3 segundos...", Colors.YELLOW)
        
        for i in range(3, 0, -1):
            print(f"\r{i}...", end='', flush=True)
            time.sleep(1)
        print("\rIniciando...", end='', flush=True)
        time.sleep(0.5)
        print()
        
        if self.recorder.start_recording(filename):
            self.current_file = self.recorder.filename
    
    def stop_recording(self):
        """Para a gravação atual"""
        if not self.recorder.is_recording:
            print_color("Nenhuma gravação em andamento!", Colors.YELLOW)
            return
        
        self.recorder.stop_recording()
        
        # Pergunta se quer salvar automaticamente
        if self.recorder.events:
            if self.auto_save:
                save = 's'
            else:
                save = input(color_text("\nDeseja salvar a gravação? (s/n): ", Colors.CYAN)).strip().lower()
            
            if save == 's':
                self.save_recording()
    
    def save_recording(self):
        """Salva gravação atual"""
        if not self.recorder.events:
            print_color("Nenhum evento para salvar!", Colors.YELLOW)
            return
        
        if self.current_file and self.recorder.filename:
            use_current = input(color_text(f"Salvar como '{self.current_file}'? (s/n): ", Colors.CYAN)).lower()
            if use_current == 's':
                filename = self.current_file
            else:
                filename = input(color_text("Nome do arquivo: ", Colors.BRIGHT_CYAN)).strip()
        else:
            filename = input(color_text("Nome do arquivo: ", Colors.BRIGHT_CYAN)).strip()
        
        if filename:
            if not filename.endswith('.json'):
                filename += '.json'
            
            if self.recorder.save_recording(filename):
                self.current_file = filename
    
    def load_recording(self):
        """Carrega gravação do arquivo"""
        print()
        filename = input(color_text("Nome do arquivo para carregar: ", Colors.BRIGHT_CYAN)).strip()
        if not filename:
            print_color("Nome inválido!", Colors.RED)
            return
        
        # Adiciona extensão .json se não tiver
        if not filename.endswith('.json'):
            filename += '.json'
        
        if not os.path.exists(filename):
            print_color("Arquivo não encontrado!", Colors.RED)
            return
        
        if self.recorder.load_recording(filename):
            self.current_file = filename
    
    def export_for_arduino(self):
        """Exporta para formato Arduino"""
        if not self.recorder.events:
            print_color("Nenhum evento para exportar!", Colors.YELLOW)
            return
        
        print()
        output_file = input(color_text("Nome do arquivo de saída (deixe em branco para automático): ", Colors.BRIGHT_CYAN)).strip()
        if not output_file:
            output_file = None
        
        self.recorder.export_for_arduino(output_file)
    
    def view_events(self):
        """Visualiza eventos gravados"""
        if not self.recorder.events:
            print_color("Nenhum evento gravado!", Colors.YELLOW)
            input(color_text("\nPressione Enter para continuar...", Colors.DIM))
            return
        
        self.clear_screen()
        self.display_header("VISUALIZAÇÃO DE EVENTOS")
        
        print(f"Total de eventos: {color_text(str(len(self.recorder.events)), Colors.BRIGHT_BLUE)}")
        
        # Corrigido: sem f-string aninhada problemática
        if self.recorder.events:
            last_time = self.recorder.events[-1].get("t", 0)
            duration_sec = last_time / 1000
            duration_str = f"{duration_sec:.1f}s"
            print(f"Duração total: {color_text(duration_str, Colors.BRIGHT_BLUE)}")
        else:
            print(f"Duração total: {color_text('0.0s', Colors.BRIGHT_BLUE)}")
        
        print()
        print(color_text("-" * 100, Colors.CYAN))
        
        # Mostra primeiros e últimos 10 eventos
        sample_size = 10
        if len(self.recorder.events) <= sample_size * 2:
            events_to_show = self.recorder.events
        else:
            events_to_show = (self.recorder.events[:sample_size] + 
                            [{"type": "...", "info": f"{len(self.recorder.events) - sample_size * 2} eventos omitidos"}] + 
                            self.recorder.events[-sample_size:])
        
        for i, event in enumerate(events_to_show):
            time_str = f"{event.get('t', 0):6d}ms"
            delay = event.get('delay', 0)
            if delay:
                delay_str = color_text(f"(+{delay:4d}ms)", Colors.GREEN)
            else:
                delay_str = ""
            
            # Determina cor baseada no tipo de evento
            if "key" in event["type"]:
                if "down" in event["type"]:
                    event_color = Colors.BRIGHT_GREEN
                else:
                    event_color = Colors.BRIGHT_CYAN
                key = event.get('key', '')
                # Formata o tipo de evento com largura fixa
                event_type = event['type']
                event_type_formatted = f"{event_type:<12}"
                print(f"{i:3d}. {time_str} {delay_str} {color_text(event_type_formatted, event_color)} {color_text(key, Colors.WHITE)}")
            
            elif "mouse" in event["type"]:
                event_color = Colors.BRIGHT_MAGENTA
                event_type = event['type']
                event_type_formatted = f"{event_type:<12}"
                if "move" in event["type"]:
                    dx = event.get('dx', 0)
                    dy = event.get('dy', 0)
                    print(f"{i:3d}. {time_str} {delay_str} {color_text(event_type_formatted, event_color)} dx={dx:4d}, dy={dy:4d}")
                elif "scroll" in event["type"]:
                    dy_val = event.get('dy', 0)
                    print(f"{i:3d}. {time_str} {delay_str} {color_text(event_type_formatted, event_color)} dy={dy_val:+.2f}")
                else:
                    button = event.get('button', '')
                    print(f"{i:3d}. {time_str} {delay_str} {color_text(event_type_formatted, event_color)} {button}")
            
            else:
                event_color = Colors.BRIGHT_YELLOW
                event_type = event['type']
                event_type_formatted = f"{event_type:<12}"
                info = event.get('info', '')
                print(f"{i:3d}. {time_str} {delay_str} {color_text(event_type_formatted, event_color)} {info}")
        
        print()
        print(color_text("-" * 100, Colors.CYAN))
        input(color_text("\nPressione Enter para voltar ao menu...", Colors.DIM))
    
    def clear_events(self):
        """Limpa todos os eventos"""
        if self.recorder.events:
            confirm = input(color_text("Tem certeza que deseja limpar todos os eventos? (s/n): ", Colors.RED)).lower()
            if confirm == 's':
                self.recorder.clear_events()
                self.current_file = None
        else:
            print_color("Nenhum evento para limpar!", Colors.YELLOW)
    
    def settings(self):
        """Menu de configurações"""
        while True:
            self.clear_screen()
            self.display_header("CONFIGURAÇÕES")
            
            print(color_text("Opções de configuração:", Colors.BOLD))
            print()
            
            settings_list = [
                ("1", f"Gravar movimentos do mouse: {'SIM' if self.recorder.record_mouse_moves else 'NÃO'}"),
                ("2", f"Intervalo entre movimentos: {self.recorder.mouse_move_interval}ms"),
                ("3", f"Distância mínima do mouse: {self.recorder.min_mouse_move}px"),
                ("4", f"Salvar automaticamente ao parar: {'SIM' if self.auto_save else 'NÃO'}"),
                ("0", "Voltar ao menu principal")
            ]
            
            for num, text in settings_list:
                print(f"  {color_text(num, Colors.CYAN)}  {text}")
            
            print()
            print(color_text("=" * 60, Colors.CYAN))
            
            choice = input(color_text("\nEscolha: ", Colors.BRIGHT_WHITE)).strip()
            
            if choice == '1':
                self.recorder.record_mouse_moves = not self.recorder.record_mouse_moves
                print_color(f"Gravar movimentos: {'SIM' if self.recorder.record_mouse_moves else 'NÃO'}", Colors.GREEN)
                time.sleep(1)
            elif choice == '2':
                try:
                    interval = int(input(color_text("Novo intervalo (10-1000 ms): ", Colors.CYAN)))
                    if 10 <= interval <= 1000:
                        self.recorder.mouse_move_interval = interval
                        print_color(f"Intervalo definido para {interval}ms", Colors.GREEN)
                    else:
                        print_color("Intervalo deve estar entre 10 e 1000ms", Colors.RED)
                except ValueError:
                    print_color("Valor inválido!", Colors.RED)
                time.sleep(1)
            elif choice == '3':
                try:
                    distance = int(input(color_text("Nova distância mínima (1-50 px): ", Colors.CYAN)))
                    if 1 <= distance <= 50:
                        self.recorder.min_mouse_move = distance
                        print_color(f"Distância mínima definida para {distance}px", Colors.GREEN)
                    else:
                        print_color("Distância deve estar entre 1 e 50px", Colors.RED)
                except ValueError:
                    print_color("Valor inválido!", Colors.RED)
                time.sleep(1)
            elif choice == '4':
                self.auto_save = not self.auto_save
                print_color(f"Salvar automaticamente: {'SIM' if self.auto_save else 'NÃO'}", Colors.GREEN)
                time.sleep(1)
            elif choice == '0':
                break
            else:
                print_color("Opção inválida!", Colors.RED)
                time.sleep(1)
    
    def run(self):
        """Executa o menu principal"""
        running = True
        
        self.clear_screen()
        self.display_header("BEM-VINDO AO GRAVADOR PARA ARDUINO LEONARDO")
        
        print(color_text("Este programa grava eventos de teclado e mouse e exporta", Colors.WHITE))
        print(color_text("para Arduino Leonardo (ATmega32u4) em formato JSON.", Colors.WHITE))
        print()
        print(color_text("Recursos principais:", Colors.BOLD))
        print(color_text("  • Gravação de teclado com suporte a modificadores", Colors.BRIGHT_BLUE))
        print(color_text("  • Gravação de mouse (movimentos, cliques, scroll)", Colors.BRIGHT_BLUE))
        print(color_text("  • Exportação otimizada para Arduino Leonardo", Colors.BRIGHT_BLUE))
        print(color_text("  • Geração automática de código .ino", Colors.BRIGHT_BLUE))
        print(color_text("  • Compatível com Windows, Linux e macOS", Colors.BRIGHT_BLUE))
        print()
        input(color_text("Pressione Enter para começar...", Colors.BRIGHT_CYAN))
        
        while running:
            self.display_menu()
            choice = self.get_choice()
            running = self.handle_choice(choice)
        
        print_color("\nObrigado por usar o gravador!", Colors.BRIGHT_GREEN)
        print_color("Encerrando...", Colors.CYAN)
        time.sleep(1)


# ============================================================================
# MAIN FUNCTION
# ============================================================================
def main():
    """Função principal"""
    try:
        menu = Menu()
        menu.run()
    except KeyboardInterrupt:
        print_color("\n\nPrograma interrompido pelo usuário.", Colors.RED)
        sys.exit(0)
    except Exception as e:
        print_color(f"\nErro inesperado: {e}", Colors.RED)
        import traceback
        traceback.print_exc()
        input(color_text("\nPressione Enter para sair...", Colors.RED))
        sys.exit(1)


if __name__ == "__main__":
    main()
