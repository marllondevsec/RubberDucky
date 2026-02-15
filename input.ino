#include <Keyboard.h>
#include <Mouse.h>

void setup() {
  // Delay de segurança para evitar execução acidental
  delay(3000);
  
  Keyboard.begin();
  Mouse.begin();
  delay(1000);  // Aguarda inicialização

  // Zera posição do mouse (move para canto superior esquerdo)
  for(int i=0; i<40; i++) {
    Mouse.move(-127, -127);
    delay(10); // Pequeno delay entre movimentos
  }
  delay(100);
  delay(545);
  Keyboard.press(KEY_LEFT_GUI);
  delay(100);
  Keyboard.release(KEY_LEFT_GUI);
  delay(496);
  Keyboard.print("p");
  delay(10);
  delay(167);
  Keyboard.print("r");
  delay(10);
  delay(128);
  Keyboard.print("o");
  delay(10);
  delay(287);
  Keyboard.press(KEY_RETURN);
  delay(100);
  Keyboard.release(KEY_RETURN);
  delay(928);
  Keyboard.press(KEY_TAB);
  delay(100);
  Keyboard.release(KEY_TAB);
  delay(288);
  Keyboard.press(KEY_TAB);
  delay(100);
  Keyboard.release(KEY_TAB);
  delay(176);
  Keyboard.press(KEY_TAB);
  delay(100);
  Keyboard.release(KEY_TAB);
  delay(312);
  Keyboard.press(KEY_TAB);
  delay(100);
  Keyboard.release(KEY_TAB);
  delay(528);
  Keyboard.press(KEY_RETURN);
  delay(100);
  Keyboard.release(KEY_RETURN);
  delay(936);
  Keyboard.write(' ');
  delay(10);
  delay(3408);
  Keyboard.press(KEY_TAB);
  delay(100);
  Keyboard.release(KEY_TAB);
  delay(352);
  Keyboard.write(' ');
  delay(10);
  delay(440);
  Keyboard.press(KEY_TAB);
  delay(100);
  Keyboard.release(KEY_TAB);
  delay(296);
  Keyboard.press(KEY_TAB);
  delay(100);
  Keyboard.release(KEY_TAB);
  delay(944);
  Keyboard.press(KEY_UP_ARROW);
  delay(50);
  Keyboard.release(KEY_UP_ARROW);
  delay(215);
  Keyboard.press(KEY_UP_ARROW);
  delay(50);
  Keyboard.release(KEY_UP_ARROW);
  delay(424);
  Keyboard.press(KEY_UP_ARROW);
  delay(50);
  Keyboard.release(KEY_UP_ARROW);
  delay(496);
  Keyboard.press(KEY_DOWN_ARROW);
  delay(50);
  Keyboard.release(KEY_DOWN_ARROW);
  delay(199);
  Keyboard.press(KEY_DOWN_ARROW);
  delay(50);
  Keyboard.release(KEY_DOWN_ARROW);
  delay(375);
  Keyboard.press(KEY_TAB);
  delay(100);
  Keyboard.release(KEY_TAB);
  delay(552);
  Keyboard.press(KEY_UP_ARROW);
  delay(50);
  Keyboard.release(KEY_UP_ARROW);
  delay(344);
  Keyboard.press(KEY_UP_ARROW);
  delay(50);
  Keyboard.release(KEY_UP_ARROW);
  delay(544);
  Keyboard.press(KEY_UP_ARROW);
  delay(50);
  Keyboard.release(KEY_UP_ARROW);
  delay(312);
  Keyboard.press(KEY_UP_ARROW);
  delay(50);
  Keyboard.release(KEY_UP_ARROW);
  delay(151);
  Keyboard.press(KEY_UP_ARROW);
  delay(50);
  Keyboard.release(KEY_UP_ARROW);
  delay(168);
  Keyboard.press(KEY_UP_ARROW);
  delay(50);
  Keyboard.release(KEY_UP_ARROW);

  Keyboard.end();
  Mouse.end();
}

void loop() {}