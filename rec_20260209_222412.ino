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
  delay(1073);
  Keyboard.press(KEY_LEFT_GUI);
  delay(10);
  delay(1704);
  Keyboard.print("p");
  delay(10);
  delay(159);
  Keyboard.print("r");
  delay(10);
  delay(104);
  Keyboard.print("o");
  delay(10);
  delay(1472);
  Keyboard.press(KEY_RETURN);
  delay(10);
  delay(2312);
  Keyboard.press(KEY_TAB);
  delay(10);
  delay(752);
  Keyboard.press(KEY_TAB);
  delay(10);
  delay(360);
  Keyboard.press(KEY_TAB);
  delay(10);
  delay(239);
  Keyboard.press(KEY_TAB);
  delay(10);
  delay(1128);
  Keyboard.press(KEY_RETURN);
  delay(10);
  delay(1536);
  Keyboard.write(' ');
  delay(10);
  delay(3536);
  Keyboard.press(KEY_TAB);
  delay(10);
  delay(1424);
  Keyboard.write(' ');
  delay(10);
  delay(351);
  Keyboard.press(KEY_TAB);
  delay(10);
  delay(384);
  Keyboard.write(' ');
  delay(10);
  delay(288);
  Keyboard.press(KEY_TAB);
  delay(10);
  delay(408);
  Keyboard.write(' ');
  delay(10);
  delay(368);
  Keyboard.press(KEY_TAB);
  delay(10);
  delay(376);
  Keyboard.write(' ');
  delay(10);
  delay(712);
  Keyboard.press(KEY_TAB);
  delay(10);
  delay(704);
  Keyboard.press(KEY_TAB);
  delay(10);
  delay(447);
  Keyboard.press(KEY_TAB);
  delay(10);
  delay(536);
  Keyboard.press(KEY_TAB);
  delay(10);

  Keyboard.end();
  Mouse.end();
}

void loop() {}