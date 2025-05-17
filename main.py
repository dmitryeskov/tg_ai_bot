import asyncio
import logging
import os

from io import BytesIO

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message

from PIL import Image
from transformers import VisionEncoderDecoderModel, ViTImageProcessor, GPT2TokenizerFast

from dotenv import load_dotenv


# Настройка логгирования
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


# Получение API_TOKEN
load_dotenv()

# Конфигурация
API_TOKEN = os.getenv("API_TOKEN")
MODEL_NAME = "nlpconnect/vit-gpt2-image-captioning"

# Создание бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

try:
    model = VisionEncoderDecoderModel.from_pretrained(MODEL_NAME)
    feature_extractor = ViTImageProcessor.from_pretrained(MODEL_NAME)
    tokenizer = GPT2TokenizerFast.from_pretrained(MODEL_NAME)
except Exception as e:
    logger.error(f"Ошибка при загрузке модели: {e}")
    raise


# --- Обработка сообщений пользователя ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Я бот с ML-моделью. Отправь мне любое фото и я отправлю описание! "
    )


@dp.message(lambda msg: msg.photo is not None)
async def handle_photo(message: Message):
    try:
        photo = message.photo[-1]
        file_id = photo.file_id

        # Скачиваем фото
        photo_file = await bot.get_file(file_id)
        photo_bytes = await bot.download_file(photo_file.file_path)

        # Открываем изображение
        image = Image.open(BytesIO(photo_bytes.read())).convert("RGB")

        # Предобработка
        pixel_values = feature_extractor(images=image, return_tensors="pt").pixel_values

        # Генерация описания
        generated_ids = model.generate(pixel_values)
        caption = tokenizer.decode(generated_ids[0], skip_special_tokens=True)

        # Ответ пользователю
        await message.reply(f"Описание изображения:\n\n{caption}")

    except Exception as e:
        logger.error(f"Ошибка при обработке фото: {e}", exc_info=True)
        await message.reply("Произошла ошибка при обработке изображения.")


@dp.error()
async def error_handler(event: types.ErrorEvent):
    logger.error(f"Ошибка в событии: {event.exception}", exc_info=True)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
