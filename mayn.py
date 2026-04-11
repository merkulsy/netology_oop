import requests
from datetime import datetime
import json
import os
from secrets import YD_TOKEN

GROUP = 'group_148'

class CatImage():
    def __init__(self, token, word):
        self.token = token
        self.word = word
        self.group = GROUP
        self.filename = None
        self.local_filename = None

    def get_image(self):

        url = f'https://cataas.com/cat/cute/says/{self.word}'
        response = requests.get(url)

        if response.status_code == 200:
            # Создаем директорию, если её нет
            os.makedirs(self.group, exist_ok=True)
            self.local_filename = f'{self.group}/{self.word}.jpg'

            with open(self.local_filename, 'wb') as file:
                file.write(response.content)
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            print(f'Картинка для слова "{self.word}" сохранена локально {self.local_filename}')

            # Сохраняем имя локального файла
            self.filename = f'{self.word}.jpg'

            # Возвращаем данные о картинке
            return {
                'word': self.word,
                'timestamp': timestamp,
                'filename': self.filename,
                'content_length': response.headers.get('Content-Length', 'unknown')
            }
        else:
            print(f'Ошибка при получении картинки для слова "{self.word}"')
            return None

    def del_image(self):
        try:
            if self.local_filename and os.path.exists(self.local_filename):
                os.remove(self.local_filename)
                print(f'Локальный файл "{self.local_filename}" успешно удален')
            else:
                print(f'Локальный файл "{self.local_filename}" не найден')
        except Exception as e:
            print(f'Ошибка при удалении файла "{self.local_filename}": {e}')

    def yd_load(self):
        headers = {'Authorization': f'OAuth {self.token}'}
        
        # Проверка наличия папки на Яндекс.Диске
        url = 'https://cloud-api.yandex.net/v1/disk/resources'
        params = {'path': {self.group}}
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            # Создание папки на Яндекс.Диске
            response_create = requests.put(url, params=params, headers=headers)
            if response_create.status_code == 201:
                print(f'Папка "{self.group}" создана на Яндекс.Диске')
            else:
                print(f'Папку "{self.group}" не удалось создать на Яндекс.Диске')


        # Загружаем файл в папку
        url = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
        params = {'path': f'{self.group}/{self.filename}', 'overwrite': 'true'}
        response = requests.get(url, params=params, headers=headers)
        upload_link = response.json()['href']

        with open(self.local_filename, 'rb') as f:
            response = requests.put(upload_link, files={'file': f})
            if response.status_code == 201:
                print(f'Файл "{self.filename}" успешно загружен на Яндекс.Диск в папку "{self.group}"')
                # После успешной загрузки удаляем локальный файл
                self.del_image()
            else:
                print(f'Файл "{self.filename}" не удалось загрузить на Яндекс.Диск')


def save_info_to_json(load_images_data):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    json_filename = f'{GROUP}/info_images_{timestamp}.json'
    # Сохраняем все данные в один JSON файл
    with open(json_filename, "w", encoding="utf-8") as f:
        json.dump(load_images_data, f, ensure_ascii=False, indent=2)
    print(f'\nВсего на Яндекс.Диске сохранено картинок: {len(load_images_data)}')
    print(f'Все данные о картинках сохранены локально в {json_filename}')


if __name__ == '__main__':
    load_images_data = []
    # token = input('Введите токен Яндекс.Диска: ').strip()
    token = YD_TOKEN

    while True:
        word = input('\nВведите текст для картинки (для завершения введите stop или оставьте пустую строку): ').strip()

        if not word or word.lower() == 'stop':
            break

        cat = CatImage(token, word)
        image_data = cat.get_image()

        if image_data:
            cat.yd_load()

            # Проверяем, есть ли уже такое слово в списке
            found = False
            for i, existing_data in enumerate(load_images_data):
                if existing_data['word'] == word:
                    # Если есть, заменяем
                    load_images_data[i] = image_data
                    found = True
                    print(f'Информация для слова "{word}" обновлена (картинка перезаписана на Яндекс.Диске)')
                    break

            if not found:
                # Если нет, добавляем
                load_images_data.append(image_data)
                print(f'Информация для слова "{word}" добавлена')


    if load_images_data:
        save_info_to_json(load_images_data)
    else:
        print('Не было получено и загружено на Яндекс.Диск ни одной картинки')