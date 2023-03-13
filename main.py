# импорты
import os       # для работы с файловой системой
import marshal  # для записи заметок в файл и их чтения
import dotenv   # для безопасной подгрузки токена бота
from aiogram import Bot, Dispatcher, executor, types  # для работы с API Telegram

# инициализация модулей и объявление  переменных
dotenv.load_dotenv()            # подгрузка окружения
API_TOKEN = os.getenv("token")  # получение токена
bot = Bot(token=API_TOKEN)      # получение объекта бота
dp = Dispatcher(bot)            # получение диспетчера бота
launch_on_message = {}          # дополнительная переменная для ожидания ввода названия или текта
temp = {}                       # дополнительная переменная для временных данных пользователя

# создание клавиатур с кнопками
menu_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)  # клавиатура главного меню
menu_markup.add(types.KeyboardButton("➕ Новая заметка"))
menu_markup.add(types.KeyboardButton("👁‍ Мои заметки"))
menu_markup.add(types.KeyboardButton("🧑‍🔧 Профиль"))

settings_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)  # клавиатура настроек
settings_markup.row(types.KeyboardButton("🔄 Изменить порядок заметок"))
settings_markup.add(types.KeyboardButton("🗑 Удалить данные"))
settings_markup.add(types.KeyboardButton("✨ Mеню"))


# вывод текста о включении бота
async def on_ready(_):
    me = await bot.get_me()
    print(f"{me.full_name} is online")


# удобное получение заметки
def get_note(_id: int, filename: str):
    try:
        with open(f"Users/{_id}/{filename}", "rb") as f:
            return marshal.loads(f.read())
    except:
        return None


# обработка начальной команды
@dp.message_handler(commands=['start'])  # отслеживание команды start
async def on_start(message: types.Message):
    await message.answer(
        "Приветствую, я бот для создания и сохранения заметок.")
    dirname = str(message.from_user.id)
    if dirname not in os.listdir("Users"):
        os.makedirs(f"Users/{dirname}")
    await on_message(message)


# команды, вызываемые кнопками
async def add_new_note3(message: types.Message):  # создание новой заметки(конец)
    if not message.text:
        return
    if message.text != "👌 Как сейчас":
        with open(f"Users/{message.from_user.id}/{temp[message.from_user.id]}.data", "rb") as f:
            note = marshal.loads(f.read())
        note["content"] = message.html_text
        with open(f"Users/{message.from_user.id}/{temp[message.from_user.id]}.data", "wb") as f:
            f.write(marshal.dumps(note))
    await message.answer("✨ Заметка сохранена")
    global launch_on_message
    del launch_on_message[message.from_user.id]
    if f"{message.from_user.id}_{temp[message.from_user.id]}" in temp:
        await temp[f"{message.from_user.id}_{temp[message.from_user.id]}"].edit_text("Заметка была отредактирована")
        del temp[f"{message.from_user.id}_{temp[message.from_user.id]}"]
    del temp[message.from_user.id]
    await on_message(message)


async def add_new_note2(message: types.Message):  # создание новой заметки(ожидание текста)
    if not message.text:
        return
    if len(message.text) > 30:
        return await message.answer(
            "Название слишком длинное, придумайте что-нибудь покороче"
        )
    if message.from_user.id not in temp:
        temp[message.from_user.id] = message.message_id
    try:
        with open(f"Users/{message.from_user.id}/{temp[message.from_user.id]}.data", "rb") as f:
            note = marshal.loads(f.read())
    except:
        note = {"title": "Untitled", "content": "None"}
    note["title"] = message.text
    with open(f"Users/{message.from_user.id}/{temp[message.from_user.id]}.data", "wb") as f:
        f.write(marshal.dumps(note))
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add(types.KeyboardButton("👌 Как сейчас"))
    await message.answer("Введите текст заметки", reply_markup=markup)
    global launch_on_message
    launch_on_message[message.from_user.id] = add_new_note3


@dp.message_handler(text=["➕ Новая заметка"])
async def add_new_note(message: types.Message, user_id=None):  # создание новой заметки(ожидание названия)
    if not user_id:
        user_id = message.from_user.id
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add(types.KeyboardButton("👌 Как сейчас"))
    await message.answer(
        "Придумайте название для заметки, старайтесь сделать его коротким и понятным",
        reply_markup=markup
    )
    global launch_on_message
    launch_on_message[user_id] = add_new_note2


@dp.message_handler(text=["👁‍ Мои заметки"])
async def view_notes(message: types.Message):  # показ заметок
    markup = types.InlineKeyboardMarkup(row_width=2)
    path = f"Users/{message.from_user.id}"
    if os.name == "nt":
        path = path.replace("/", "\\")
    file_list = os.listdir(path)
    _reverse = False
    if "reverse" in file_list:
        _reverse = True
        file_list.remove("reverse")
    file_list = [os.path.join(path, i) for i in file_list]
    notes = sorted(file_list, key=os.path.getmtime, reverse=_reverse)
    notes = [i[len(path)+1:] for i in notes]
    del file_list
    if len(notes) == 0:
        return await message.answer("🗒 У вас еще нет заметок")
    num = 3
    if len(notes) < 6:
        num = int(float((len(notes) + 1) / 2))
    for i in range(num):
        _id = message.from_user.id
        note1 = get_note(_id, notes[i * 2])
        try:
            note2 = get_note(_id, notes[i * 2 + 1])
        except IndexError:
            note2 = None
        button1 = types.InlineKeyboardButton(
            note1.get("title", "Без названия"),
            callback_data=f"ViewNote_{notes[i * 2]}"
        )
        row = [button1]
        if note2:
            button2 = types.InlineKeyboardButton(
                note2.get("title", "Без названия"),
                callback_data=f"ViewNote_{notes[i * 2 + 1]}"
            )
            row.append(button2)
        markup.row(*row)
    if len(notes) > 6:
        button_next = types.InlineKeyboardButton("Дальше ➡", callback_data="NextPage_6")
        markup.row(button_next)
    await message.answer("🗒 Ваши заметки(сортировка по дате)", reply_markup=markup)


@dp.message_handler(text=["🧑‍🔧 Профиль"])
async def settings(message: types.Message):  # открытие настроек
    user = message.from_user
    mention = f"({user.mention})" if user.mention else ""
    await message.answer(f"""
Настройки профиля {user.full_name} {mention}

Заметок: {len(os.listdir(f"Users/{user.id}"))}
ID: {user.id}
""", reply_markup=settings_markup)


@dp.message_handler(text="🗑 Удалить данные")  # переспрашиваем об удалении всех заметок
async def delete_data(message: types.Message):
    markup = types.InlineKeyboardMarkup()
    markup.insert(types.InlineKeyboardButton("Да", callback_data="DeleteUserData"))
    markup.insert(types.InlineKeyboardButton("Нет", callback_data="OpenMenu"))
    await message.answer("Вы точно хотите удалить все данные? Это нельзя будет отменить", reply_markup=markup)


@dp.message_handler(text=["🔄 Изменить порядок заметок"])
async def reverse(message: types.Message):  # изменение порядка заметок
    if "reverse" in os.listdir(f"Users/{message.from_user.id}"):
        os.remove(f"Users/{message.from_user.id}/reverse")
    else:
        with open(f"Users/{message.from_user.id}/reverse", "w") as f:
            f.write("")
    await message.answer("✅ Успешно")

@dp.message_handler()
async def on_message(message: types.Message):  # во всех остальных случаях
    if message.from_user.id in launch_on_message:
        return await launch_on_message[message.from_user.id](message)
    await message.answer("✨ Главное меню", reply_markup=menu_markup)


# отслеживание нажатий Inline кнопок
@dp.callback_query_handler()
async def callback_handler(callback: types.CallbackQuery):
    if callback.data == "OpenMenu":  # при нажатии "В меню"
        await callback.message.answer("✨ Главное меню", reply_markup=menu_markup)
    elif callback.data == "DeleteThis":  # при нажатии на кнопку удалить сообщение
        await callback.message.delete()
    elif callback.data == "DeleteUserData":  # удаление заметок пользователя
        for filename in os.listdir(f"Users/{callback.from_user.id}"):
            try:
                path = f"Users/{callback.from_user.id}/{filename}"
                os.remove(path)
            except:
                pass
        await callback.message.answer("✨ Главное меню", reply_markup=menu_markup)
        return await callback.answer("Все данные о вас удалены", show_alert=True)
    elif callback.data.startswith("NextPage"):  # листание вперед в списке заметок
        num = float(int(callback.data[9:]) / 2)
        num2 = float(num + 3)
        notes = os.listdir(f"Users/{callback.from_user.id}")
        markup = types.InlineKeyboardMarkup(row_width=2)
        if num2 * 2 > len(notes):
            num2 = float((len(notes) + 1) / 2)
        for i in range(int(num), int(num2)):
            _id = callback.from_user.id
            note1 = get_note(_id, notes[i * 2])
            try:
                note2 = get_note(_id, notes[i * 2 + 1])
            except IndexError:
                note2 = None
            button1 = types.InlineKeyboardButton(
                note1.get("title", "Без названия"),
                callback_data=f"ViewNote_{notes[i * 2]}"
            )
            row = [button1]
            if note2:
                button2 = types.InlineKeyboardButton(
                    note2.get("title", "Без названия"),
                    callback_data=f"ViewNote_{notes[i * 2 + 1]}"
                )
                row.append(button2)
            markup.row(*row)
        button_back = types.InlineKeyboardButton("⬅ Назад", callback_data=f"PrevPage_{int(float(num * 2 - 6))}")
        row = [button_back]
        if len(notes) > num2 * 2:
            button_next = types.InlineKeyboardButton("Дальше ➡", callback_data=f"NextPage_{int(float(num2 * 2))}")
            row.append(button_next)
        markup.row(*row)
        await callback.message.edit_reply_markup(markup)
    elif callback.data.startswith("PrevPage"):  # листание назад в списке заметок
        num = float(int(int(callback.data[9:])) / 2)
        num2 = float(num + 3)
        notes = os.listdir(f"Users/{callback.from_user.id}")
        markup = types.InlineKeyboardMarkup(row_width=2)
        if num2 * 2 > len(notes):
            num2 = float((len(notes) + 1) / 2)
        for i in range(int(num), int(num2)):
            _id = callback.from_user.id
            note1 = get_note(_id, notes[i * 2])
            try:
                note2 = get_note(_id, notes[i * 2 + 1])
            except IndexError:
                note2 = None
            button1 = types.InlineKeyboardButton(
                note1.get("title", "Без названия"),
                callback_data=f"ViewNote_{notes[i * 2]}"
            )
            row = [button1]
            if note2:
                button2 = types.InlineKeyboardButton(
                    note2.get("title", "Без названия"),
                    callback_data=f"ViewNote_{notes[i * 2 + 1]}"
                )
                row.append(button2)
            markup.row(*row)
        row = []
        if num * 2 - 6 >= 0:
            button_back = types.InlineKeyboardButton("⬅ Назад", callback_data=f"PrevPage_{int(float(num * 2 - 6))}")
            row.append(button_back)
        if len(notes) > num2 * 2:
            button_next = types.InlineKeyboardButton("Дальше ➡", callback_data=f"NextPage_{int(float(num2 * 2))}")
            row.append(button_next)
        markup.row(*row)
        await callback.message.edit_reply_markup(markup)
    elif callback.data.startswith("ViewNote"):  # отобразить выбранную заметку
        _id = callback.from_user.id
        filename = callback.data[9:]
        note = get_note(_id, filename)
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.insert(types.InlineKeyboardButton("Изменить заметку", callback_data=f"EditNote_{filename}"))
        markup.insert(types.InlineKeyboardButton("Удалить заметку", callback_data=f"RequestDelete_{filename}"))
        await callback.message.edit_text(
            f"<strong>{note['title']}</strong>\n\n{note['content']}",
            parse_mode=types.ParseMode.HTML,
            reply_markup=markup
        )
    elif callback.data.startswith("EditNote"):  # изменить заметку
        filename = callback.data[9:-5]
        global temp
        temp[f"{callback.from_user.id}_{filename}"] = callback.message
        temp[callback.from_user.id] = filename
        await add_new_note(callback.message, callback.from_user.id)
    elif callback.data.startswith("RequestDelete"):  # спросить о удалении заметки
        filename = callback.data[14:]
        markup = types.InlineKeyboardMarkup()
        markup.insert(types.InlineKeyboardButton("Да", callback_data=f"DeleteNote_{filename}"))
        markup.insert(types.InlineKeyboardButton("Нет", callback_data="DeleteThis"))
        await callback.message.answer("Вы уверены что хотите удалить эту заметку?", reply_markup=markup)
        temp[-1*callback.from_user.id] = callback.message.message_id
    elif callback.data.startswith("DeleteNote"):  # удалить заметку
        filename = callback.data[11:]
        path = f"Users/{callback.from_user.id}/{filename}"
        os.remove(path)
        await callback.answer("✅ Удалено", show_alert=True)
        await callback.message.delete()
        await bot.delete_message(callback.from_user.id, temp[-1*callback.from_user.id])
        return
    else:
        return await callback.answer("ErrCode 404\nUnknown callback data")
    await callback.answer()


# запуск программы
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_ready)
