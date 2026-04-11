import requests
from datetime import datetime
import json
import os
import logging
import time
from secrets import YD_TOKEN

GROUP = 'group_148'

# Настройка логирования
LOG_DIR = 'log'
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, f'log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

# Настройка корневого логгера
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()  # Вывод в консоль
    ]
)

logger = logging.getLogger(__name__)


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
            logger.info(f'Картинка для слова "{self.word}" сохранена локально {self.local_filename}')

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
            logger.error(f'Ошибка при получении картинки для слова "{self.word}", статус: {response.status_code}')
            return None

    def del_image(self):
        try:
            if self.local_filename and os.path.exists(self.local_filename):
                os.remove(self.local_filename)
                logger.info(f'Локальный файл "{self.local_filename}" успешно удален')
            else:
                logger.warning(f'Локальный файл "{self.local_filename}" не найден')
        except Exception as e:
            logger.error(f'Ошибка при удалении файла "{self.local_filename}": {e}')

    def yd_load(self):
        headers = {'Authorization': f'OAuth {self.token}'}

        # Проверка наличия папки на Яндекс.Диске
        url = 'https://cloud-api.yandex.net/v1/disk/resources'
        params = {'path': self.group}
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            # Создание папки на Яндекс.Диске
            response_create = requests.put(url, params=params, headers=headers)
            if response_create.status_code == 201:
                logger.info(f'Папка "{self.group}" создана на Яндекс.Диске')
            else:
                logger.error(
                    f'Папку "{self.group}" не удалось создать на Яндекс.Диске, статус: {response_create.status_code}')

        # Загружаем файл в папку
        url = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
        params = {'path': f'{self.group}/{self.filename}', 'overwrite': 'true'}
        response = requests.get(url, params=params, headers=headers)
        upload_link = response.json()['href']

        with open(self.local_filename, 'rb') as f:
            response = requests.put(upload_link, files={'file': f})
            if response.status_code == 201:
                logger.info(f'Файл "{self.filename}" успешно загружен на Яндекс.Диск в папку "{self.group}"')
                # После успешной загрузки удаляем локальный файл
                self.del_image()
            else:
                logger.error(
                    f'Файл "{self.filename}" не удалось загрузить на Яндекс.Диск, статус: {response.status_code}')


def save_info_to_json(load_images_data):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    json_filename = f'{GROUP}/info_images_{timestamp}.json'
    # Сохраняем все данные в один JSON файл
    with open(json_filename, "w", encoding="utf-8") as f:
        json.dump(load_images_data, f, ensure_ascii=False, indent=2)
    logger.info(f'Всего на Яндекс.Диске сохранено картинок: {len(load_images_data)}')
    logger.info(f'Все данные о картинках сохранены локально в {json_filename}')


if __name__ == '__main__':
    logger.info(f"Лог-файл: {LOG_FILE}")
    logger.info("Программа запущена")

    load_images_data = []
    token = YD_TOKEN

    while True:
        # Небольшая задержка перед выводом приглашения, чтобы не смешивалось с логами
        time.sleep(0.1)

        print('\nВведите текст для картинки (для завершения введите stop или оставьте пустую строку): ', end='',
              flush=True)
        word = input().strip()
        logger.info(f'Введено слово "{word}"')

        if not word or word.lower() == 'stop':
            logger.info("Программа завершена пользователем")
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
                    logger.info(f'Информация для слова "{word}" обновлена (картинка перезаписана на Яндекс.Диске)')
                    break

            if not found:
                # Если нет, добавляем
                load_images_data.append(image_data)
                logger.info(f'Информация для слова "{word}" добавлена')

        # Небольшая задержка после обработки, чтобы логи успели вывестись
        time.sleep(0.1)

    if load_images_data:
        save_info_to_json(load_images_data)
    else:
        logger.warning('Не было получено и загружено на Яндекс.Диск ни одной картинки')

    logger.info("Программа завершена")