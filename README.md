# <img width="128" height="128" alt="Copilot_20260211_072828" src="https://github.com/user-attachments/assets/53b5fbeb-8c45-4e2e-a831-49d2ccff97c9" /> Система Экзаменационного Тестирования

На Python и CustomTkinter

<img width="300" height="263" alt="image" src="https://github.com/user-attachments/assets/884e8a7a-fffe-40ab-a770-1eabaa7bc3e8" /> <img width="300" height="263" alt="image" src="https://github.com/user-attachments/assets/b1694876-b4e6-4167-9bfc-449f149a74a7" /> <img width="300" height="263" alt="image" src="https://github.com/user-attachments/assets/74521bd7-aa11-46fc-8700-1cef3beeadae" /> <img width="300" height="263" alt="image" src="https://github.com/user-attachments/assets/c38e5488-4bad-4789-ac74-0e0a7bab0540" />

## Возможности
- Запуск одного теста или банка тестов.
- Поддержка типов вопросов:
  - один вариант,
  - несколько вариантов,
  - сопоставление,
  - свободный ввод.
- Поддержка изображений в вопросах (`!(Подпись)[image.png]`) и увеличение по клику.
- Сохранение результатов, просмотр ошибок, опциональная отправка в Telegram.
- Настройки UI(светлая/темная)/логики и управление пользовательскими данными.
  - Возможность запрета сворачивания и окон поверх тестирования для предотвращения списывания
  - Таймер (фиксированный или авто-режим `A(n)`).
  - Настройка количества вопросов, запуск отдельных файлов с тестами

## Где хранятся данные
- Linux: `~/.local/share/pyquiz/`
- Windows: `%LOCALAPPDATA%\pyquiz\`

В каталоге хранятся:
- `settings.json` — настройки,
- `names_user.txt` — пользовательские имена,
- `tests/` — загруженные пользователем тесты,
- `results/` — результаты.

## Синтаксис тестов
```text
Название списка тестов

Текст вопроса
A) Вариант 1
B) Вариант 2
B

Вопрос с несколькими ответами
A) Вариант 1
B) Вариант 2
C) Вариант 3
A, C

Сопоставление
A) Вариант 1
B) Вариант 2
C) Вариант 3
D) Вариант 4
A-C, B-D

Свободный ввод - Напишите что-нибудь (правильный только один вариант из списка, через запятую)
что-нибудь, чтонибудь
```

Изображение в тексте вопроса:
```text
1. Вопрос !(Подпись)[my_image.png]
```
Изображения хранятся в 'tests\images\...', либо прямо рядом с тестами

## Сборка .exe
Ниже два варианта (из корня проекта, в активированной venv).
### 0) Установка библиотеки
```bash
pip install --upgrade -r requirements.txt
```
### 1) Базовая сборка ("голый" exe)
```bash
pyinstaller --noconfirm --windowed --onefile --icon=pyquiz.ico main.py
```
### 2) Сборка с включением тестов/ресурсов
```bash
pyinstaller --noconfirm --windowed --onefile --add-data "tests;tests" --add-data "names_base.txt;." --icon=pyquiz.ico main.py
```
> На Linux/macOS в `--add-data` используется разделитель `:` вместо `;`.

### Тесты в приложении при сборке должны находиться в корневом каталоге в папке 'tests', картинки в этой папке в папке 'images'
### Заранее созданный список имен студентов указывать в файле 'names_base.txt' хранимый в корневом каталоге

## Запуск из исходников
```bash
python main.py
```
