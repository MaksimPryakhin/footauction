from flask import Flask, send_from_directory
from flask_socketio import SocketIO, emit
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

connected_players = set()
game_state = {
    "theme": "", "position": "ВРТ", "position_index": 0, "round": 1,
    "current_price": 1, "current_player": "", "current_cat": "", "used_players": [],
    "participants": [
        {"id": 1, "name": "Макс", "bank": 25, "squad": {}, "passed": False},
        {"id": 2, "name": "Пашок", "bank": 25, "squad": {}, "passed": False},
        {"id": 3, "name": "Тимоха", "bank": 25, "squad": {}, "passed": False}
    ],
    "turn_index": 0, "starting_turn": 0, "active": False
}
POSITIONS = ["ВРТ", "ЦЗ", "ЦОП", "ЦАП", "ФРВ"]

PLAYERS_POOL = {
    "modern": {
        "ВРТ": {"топ": ["Давид Райя", "Эдерсон", "Алиссон", "Куртуа", "Доннарумма"], "средний": ["Менди", "Онана", "Рамсдейл", "Мартинес", "Сомер"], "слабый": ["Пикфорд", "Санчес", "Льорис", "Батленд", "Фабиански"]},
        "ЦЗ": {"топ": ["Пау Кубарси", "Ашраф Хакими", "Нуну Мендеш", "Ван Дейк", "Рюдигер"], "средний": ["Салиба", "Бастони", "Гвардиол", "Томори", "Кунде"], "слабый": ["Магуайр", "Линделёф", "Кристенсен", "Байи", "Дирк"]},
        "ЦОП": {"топ": ["Родри", "Джуд Беллингем", "Витинья", "Киммих", "Каземиро"], "средний": ["Партей", "Фабиньо", "Тьяго", "Бентанкур", "Локателли"], "слабый": ["Мактоминей", "Хёйбьерг", "Скипп", "Уорд-Проуз", "Дуглас Луис"]},
        "ЦАП": {"топ": ["Кевин Де Брёйне", "Бруно Фернандеш", "Бернарду Силва", "Эдегор", "Мюллер"], "средний": ["Маунт", "Хаверц", "Грилиш", "Пайет", "Оскар"], "слабый": ["Лингард", "Баркли", "Лансини", "Джанини", "Уолкотт"]},
        "ФРВ": {"топ": ["Килиан Мбаппе", "Эрлинг Холанд", "Лионель Месси", "Ламин Ямаль", "Харри Кейн"], "средний": ["Габриэл Жезус", "Санчо", "Фирмино", "Коутиньо", "Жиру"], "слабый": ["Уэлбек", "Кэрролл", "Деле Алли", "Дринкуотер", "Уилшир"]},
    },
    "xxi": {
        "ВРТ": {"топ": ["Мануэль Нойер", "Джанлуиджи Буффон", "Икер Касильяс", "Петр Чех", "Тибо Куртуа"], "средний": ["Эдвин Ван дер Сар", "Уго Льорис", "Кейлор Навас", "Давид Де Хеа", "Джо Харт"], "слабый": ["Виктор Вальдес", "Пепе Рейна", "Бен Фостер", "Симон Миньоле", "Артур Боруц"]},
        "ЦЗ": {"топ": ["Серхио Рамос", "Паоло Мальдини", "Фабио Каннаваро", "Карлес Пуйоль", "Вирджил Ван Дейк"], "средний": ["Рио Фердинанд", "Джон Терри", "Венсан Компани", "Алессандро Неста", "Лилиан Тюрам"], "слабый": ["Жерар Пике", "Пепе", "Диего Годин", "Тиаго Силва", "Рафаэль Варан"]},
        "ЦОП": {"топ": ["Хави", "Андреа Пирло", "Серхио Бускетс", "Лука Модрич", "Родри"], "средний": ["Стивен Джеррард", "Фрэнк Лэмпард", "Яя Туре", "Н'Голо Канте", "Патрик Виейра"], "слабый": ["Пол Скоулз", "Кларенс Зеедорф", "Дэвид Бекхэм", "Михаэль Баллак", "Данни"]},
        "ЦАП": {"топ": ["Зинедин Зидан", "Андрес Иньеста", "Роналдиньо", "Кака", "Кевин Де Брёйне"], "средний": ["Давид Сильва", "Сеск Фабрегас", "Месут Озил", "Анхель Ди Мария", "Уэйн Руни"], "слабый": ["Хуан Рикельме", "Пабло Аймар", "Деку", "Рафаэль ван дер Ваарт", "Уэсли Снейдер"]},
        "ФРВ": {"топ": ["Лионель Месси", "Криштиану Роналду", "Роналдо", "Тьерри Анри", "Килиан Мбаппе"], "средний": ["Луис Суарес", "Златан Ибрагимович", "Карим Бензема", "Роберт Левандовски", "Самюэль Это'о"], "слабый": ["Неймар", "Дидье Дрогба", "Рауль", "Франческо Тотти", "Алессандро Дель Пьеро"]},
    },
    "rpl": {
        "ВРТ": {"топ": ["Игорь Акинфеев", "Вячеслав Малафеев", "Сергей Рыжиков", "Гилерме", "Андрей Лунёв"], "средний": ["Юрий Лодыгин", "Александр Беленов", "Сослан Джанаев", "Антон Шунин", "Маринато Гилерме"], "слабый": ["Сергей Песьяков", "Александр Селихов", "Илья Абаев", "Дмитрий Абакумов", "Евгений Городов"]},
        "ЦЗ": {"топ": ["Сергей Игнашевич", "Василий Березуцкий", "Алексей Березуцкий", "Бранислав Иванович", "Мариу Фернандес"], "средний": ["Дейвидас Шемберас", "Доменико Кришито", "Луис Нету", "Сердар Таски", "Ведран Чорлука"], "слабый": ["Владимир Гранат", "Андрей Семёнов", "Георгий Джикия", "Максим Беляев", "Тарас Бурлак"]},
        "ЦОП": {"топ": ["Понтус Вернблум", "Александр Головин", "Данни", "Халк", "Роман Широков"], "средний": ["Игорь Денисов", "Денис Глушаков", "Кристиан Нобоа", "Аксель Витсель", "Олег Шатов"], "слабый": ["Артур Юсупов", "Руслан Камболов", "Магомед Оздоев", "Александр Ерохин", "Юрий Газинский"]},
        "ЦАП": {"топ": ["Алан Дзагоев", "Кевин Кураньи", "Сейду Думбия", "Вагнер Лав", "Халк"], "средний": ["Александр Самедов", "Дмитрий Комбаров", "Бибрас Натхо", "Квинси Промес", "Матиас Норманн"], "слабый": ["Павел Мамаев", "Роман Ерёменко", "Иван Обляков", "Алексей Миранчук", "Антон Миранчук"]},
        "ФРВ": {"топ": ["Артём Дзюба", "Вагнер Лав", "Сейду Думбия", "Халк", "Квинси Промес"], "средний": ["Александр Кержаков", "Дмитрий Сычёв", "Роман Павлюченко", "Фёдор Смолов", "Саломон Рондон"], "слабый": ["Максим Канунников", "Дмитрий Полоз", "Ари", "Луис Адриано", "Николай Комличенко"]},
    },
    "apl": {
        "ВРТ": {"топ": ["Петр Чех", "Эдвин Ван дер Сар", "Алиссон", "Эдерсон", "Давид Де Хеа"], "средний": ["Хьюго Льорис", "Джо Харт", "Тим Крул", "Брэд Гюзан", "Шэй Гивен"], "слабый": ["Бен Фостер", "Симон Миньоле", "Артур Боруц", "Вито Манноне", "Роб Грин"]},
        "ЦЗ": {"топ": ["Рио Фердинанд", "Джон Терри", "Вирджил Ван Дейк", "Венсан Компани", "Эшли Коул"], "средний": ["Неманья Видич", "Сол Кэмпбелл", "Гари Кэхилл", "Ледли Кинг", "Тоби Алдервейрелд"], "слабый": ["Джолеон Лескотт", "Фил Джагелка", "Крис Смоллинг", "Мартин Келли", "Уэс Браун"]},
        "ЦОП": {"топ": ["Пол Скоулз", "Стивен Джеррард", "Фрэнк Лэмпард", "Патрик Виейра", "Родри"], "средний": ["Рой Кин", "Клод Макелеле", "Майкл Кэррик", "Даррен Флетчер", "Джеймс Милнер"], "слабый": ["Гарет Барри", "Скотт Паркер", "Ли Карсли", "Том Хаддлстоун", "Джордан Хендерсон"]},
        "ЦАП": {"топ": ["Кевин Де Брёйне", "Давид Сильва", "Сеск Фабрегас", "Эден Азар", "Яя Туре"], "средний": ["Месут Озил", "Хуан Мата", "Кристиан Эриксен", "Филипп Коутиньо", "Бернарду Силва"], "слабый": ["Джо Коул", "Шон Райт-Филлипс", "Санчес", "Нани", "Тео Уолкотт"]},
        "ФРВ": {"топ": ["Тьерри Анри", "Уэйн Руни", "Криштиану Роналду", "Мохамед Салах", "Серхио Агуэро"], "средний": ["Дидье Дрогба", "Луис Суарес", "Харри Кейн", "Эрлинг Холанд", "Робин Ван Перси"], "слабый": ["Фернандо Торрес", "Николя Анелька", "Джермейн Дефо", "Эммануэль Адебайор", "Питер Крауч"]},
    },
}

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@socketio.on('login')
def handle_login(data):
    idx = data.get('player_index')
    if idx in [0, 1, 2]:
        connected_players.add(idx)
        is_ready = len(connected_players) == 3
        emit('players_ready', is_ready, broadcast=True)

@socketio.on('start_game')
def handle_start_game(data):
    if data.get('player_index') != 0:
        emit('error', {'message': 'Только Максим может запускать игру!'})
        return
    if len(connected_players) < 3:
        emit('error', {'message': 'Не все игроки подключились!'})
        return

    game_state['theme'] = data['theme']
    game_state['active'] = True
    game_state['position_index'] = 0
    game_state['round'] = 1
    game_state['used_players'] = []
    game_state['starting_turn'] = 0
    for p in game_state['participants']:
        p['bank'] = 25; p['squad'] = {}; p['passed'] = False
    next_auction()
    emit_state()

@socketio.on('place_bid')
def handle_bid(data):
    amount = float(data['amount'])
    player = game_state['participants'][game_state['turn_index']]
    if amount > player['bank'] or amount <= game_state['current_price']:
        emit('error', {'message': 'Неверная ставка!'}); return
    game_state['current_price'] = amount
    emit('log', {'text': f"{player['name']} ставит ${amount:.2f}"}, broadcast=True)
    next_turn()

@socketio.on('pass_auction')
def handle_pass():
    player = game_state['participants'][game_state['turn_index']]
    player['passed'] = True
    emit('log', {'text': f"❌ {player['name']} уступает."}, broadcast=True)
    next_turn()

def next_turn():
    active_players = [p for p in game_state['participants'] if not p['passed'] and p['bank'] >= 1]
    if len(active_players) <= 1:
        winner = active_players[0] if active_players else None
        if winner and game_state['current_price'] > 0:
            winner['squad'][game_state['position']] = {"name": game_state['current_player'], "price": game_state['current_price']}
            winner['bank'] -= game_state['current_price']
            emit('log', {'text': f"🏆 {game_state['current_player']} ушел к {winner['name']} за ${game_state['current_price']:.2f}"}, broadcast=True)
        else:
            emit('log', {'text': f"🏁 Никто не забрал {game_state['current_player']}."}, broadcast=True)
        game_state['round'] += 1
        socketio.sleep(3)
        advance_auction()
    else:
        while True:
            game_state['turn_index'] = (game_state['turn_index'] + 1) % 3
            if not game_state['participants'][game_state['turn_index']]['passed'] and game_state['participants'][game_state['turn_index']]['bank'] >= 1:
                break
        emit_state()

def advance_auction():
    if game_state['round'] > 3:
        game_state['round'] = 1; game_state['position_index'] += 1
    if game_state['position_index'] >= len(POSITIONS):
        game_state['active'] = False; emit('game_over', broadcast=True); return
    game_state['starting_turn'] = (game_state['starting_turn'] + 1) % 3
    next_auction()

def next_auction():
    game_state['position'] = POSITIONS[game_state['position_index']]
    game_state['current_price'] = 1
    for p in game_state['participants']: p['passed'] = False
    
    game_state['turn_index'] = game_state['starting_turn']
    while game_state['participants'][game_state['turn_index']]['bank'] < 1:
        game_state['turn_index'] = (game_state['turn_index'] + 1) % 3
        
    rand = random.random() * 100
    if rand < 70: cat = "топ"
    elif rand < 90: cat = "средний"
    else: cat = "слабый"
    
    pool = PLAYERS_POOL[game_state['theme']][game_state['position']][cat]
    available = [p for p in pool if p not in game_state['used_players']]
    
    if available:
        name = random.choice(available); game_state['used_players'].append(name); game_state['current_player'] = name
        game_state['current_cat'] = cat
    else:
        all_pool = []
        for c in ["топ", "средний", "слабый"]:
            all_pool.extend(PLAYERS_POOL[game_state['theme']][game_state['position']][c])
        available = [p for p in all_pool if p not in game_state['used_players']]
        if available:
            name = random.choice(available); game_state['used_players'].append(name); game_state['current_player'] = name
            game_state['current_cat'] = "любая"
        else:
            game_state['current_player'] = "Нет игроков"
            game_state['current_cat'] = "нет"
            
    emit_state()

def emit_state():
    socketio.emit('state_update', {
        'participants': game_state['participants'], 'position': game_state['position'],
        'round': game_state['round'], 'current_price': game_state['current_price'],
        'current_player': game_state['current_player'], 'current_cat': game_state['current_cat'],
        'turn_index': game_state['turn_index'], 'active': game_state['active']
    })

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
