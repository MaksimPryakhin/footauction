from flask import Flask, send_from_directory
from flask_socketio import SocketIO, emit
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

connected_players = set()
game_state = {
    "theme": "", "position": "ВРТ", "position_index": 0, "round": 1,
    "current_price": 0, "current_player": "", "current_cat": "", "used_players": [],
    "participants": [
        {"id": 1, "name": "Макс", "bank": 25, "squad": [], "passed": False},
        {"id": 2, "name": "Пашок", "bank": 25, "squad": [], "passed": False},
        {"id": 3, "name": "Тимоха", "bank": 25, "squad": [], "passed": False}
    ],
    "turn_index": 0, "starting_turn": 0, "active": False,
    "lock": False, "waiting_for_decision": False, "solo_winner_id": None
}

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
    "rpl_modern": {
        "ВРТ": {
            "топ": ["Игорь Акинфеев", "Антон Митрюшкин", "Денис Адамов", "Евгений Латышонок", "Александр Максименко"], 
            "средний": ["Сергей Песьяков", "Антон Шунин", "Илья Помазун", "Никита Медведев", "Юрий Дюпин"], 
            "слабый": ["Александр Беленов", "Евгений Городов", "Виталий Гудиев", "Никита Гойло", "Богдан Овсянников"]
        },
        "ЦЗ": {
            "топ": ["Вильмар Барриос", "Максим Осипенко", "Игорь Дивеев", "Родриган", "Срджан Бабич"], 
            "средний": ["Георгий Джикия", "Александр Солдатенков", "Павел Клинов", "Дмитрий Чистяков", "Дмитрий Круговой"], 
            "слабый": ["Самюэль Жиго", "Николай Чернов", "Илья Самошников", "Артем Макарчук", "Степан Оганесян"]
        },
        "ЦОП": {
            "топ": ["Клаудиньо", "Вендел", "Иван Обляков", "Данил Глебов", "Даниэль Фернандес"], 
            "средний": ["Роман Зобнин", "Дмитрий Баринов", "Александр Черников", "Тимофей Пикалев", "Данила Козлов"], 
            "слабый": ["Магомед Оздоев", "Артем Тимофеев", "Илья Камышев", "Антон Миранчук", "Константин Кучаев"]
        },
        "ЦАП": {
            "топ": ["Максим Глушенков", "Эдуард Сперцян", "Бителло", "Алексей Батраков"], 
            "средний": ["Лео Кордоба", "Манфред Угальде", "Фёдор Чалов", "Максим Пряхин"], 
            "слабый": ["Маркус Вендел", "Хесус Медина", "Жоан Хаджи", "Даниил Уткин", "Артур Галоян"]
        },
        "ФРВ": {
            "топ": ["Мирлинд Даку", "Джон Кордоба", "Артём Дзюба", "Константин Тюкавин", "Александр Соболев"], 
            "средний": ["Иван Сергеев", "Николай Комличенко", "Матео Кассьерра", "Евгений Марков", "Дмитрий Воробьев"], 
            "слабый": ["Владислав Шитов", "Александр Юшин", "Максим Канунников", "Ари", "Луис Адриано"]
        },
    },
    "gym1": {
        "ВРТ": {
            "топ": ["Ваня Попов", "Кирилл Князев", "Кирилл Максимов"], 
            "средний": ["Женек Алцыбеев", "Колян Севрюгин"], 
            "слабый": ["Настя Павлова", "Вова Исайкин"]
        },
        "ЦЗ": {
            "топ": ["Павел Клинов", "Юрич", "Кисель"], 
            "средний": ["Никита Валяник", "Никита Махаев"], 
            "слабый": ["Влад Воронин", "Айдар Майланов"]
        },
        "ЦОП": {
            "топ": ["Тимофей Пикалев", "Святослав Павлюк", "Рома Амирханов", "Анисимов"], 
            "средний": ["Миша Воробейкин", "Химич"], 
            "слабый": ["Егор Сивелькин"]
        },
        "ФРВ": {
            "топ": ["Максим Пряхин", "Никита Бальцер", "Саша Должников"], 
            "средний": ["Кобза", "Сазон"], 
            "слабый": ["Артем Климов", "Влад Божинский"]
        },
    }
}

def get_game_rules(theme):
    if theme == "gym1":
        return {"positions": ["ВРТ", "ЦЗ", "ЦОП", "ФРВ"], "bank": 20, "probs": [50, 25, 25]}
    return {"positions": ["ВРТ", "ЦЗ", "ЦОП", "ЦАП", "ФРВ"], "bank": 25, "probs": [70, 20, 10]}

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@socketio.on('login')
def handle_login(data):
    idx = data.get('player_index')
    if idx in [0, 1, 2]:
        connected_players.add(idx)
        emit('players_ready', len(connected_players) == 3, broadcast=True)

@socketio.on('start_game')
def handle_start_game(data):
    if data.get('player_index') != 0 or len(connected_players) < 3: return
    theme = data['theme']
    rules = get_game_rules(theme)
    
    game_state['theme'] = theme
    game_state['active'] = True
    game_state['position_index'] = 0
    game_state['round'] = 1
    game_state['used_players'] = []
    game_state['starting_turn'] = 0
    game_state['lock'] = False
    game_state['waiting_for_decision'] = False
    for p in game_state['participants']:
        p['bank'] = rules['bank']
        p['squad'] = []
        p['passed'] = False
    next_auction()
    emit_state()

def can_bid(player):
    if player['passed'] or player['bank'] < 1 or len(player['squad']) >= 5: return False
    if game_state['position'] == "ВРТ":
        has_gk = any(p['pos'] == "ВРТ" for p in player['squad'])
        if has_gk: return False
    return True

@socketio.on('place_bid')
def handle_bid(data):
    if game_state['lock'] or not game_state['active'] or game_state['waiting_for_decision']: return
    player = game_state['participants'][game_state['turn_index']]
    if not can_bid(player): return
    amount = float(data['amount'])
    if amount > player['bank'] or amount <= game_state['current_price']: return
    game_state['current_price'] = amount
    emit('log', {'text': f"{player['name']} ставит ${amount:.2f}"}, broadcast=True)
    game_state['lock'] = True
    socketio.sleep(0.5)
    game_state['lock'] = False
    next_turn()

@socketio.on('pass_auction')
def handle_pass():
    if game_state['lock'] or not game_state['active'] or game_state['waiting_for_decision']: return
    player = game_state['participants'][game_state['turn_index']]
    player['passed'] = True
    emit('log', {'text': f"❌ {player['name']} уступает."}, broadcast=True)
    game_state['lock'] = True
    socketio.sleep(0.5)
    game_state['lock'] = False
    next_turn()

@socketio.on('solo_decision')
def handle_solo_decision(data):
    if not game_state['waiting_for_decision']: return
    winner = game_state['participants'][game_state['solo_winner_id']]
    take_it = data.get('take')
    if take_it and winner['bank'] >= 1:
        winner['squad'].append({"name": game_state['current_player'], "price": 1, "cat": game_state['current_cat'], "pos": game_state['position']})
        winner['bank'] -= 1
        emit('log', {'text': f"🏆 {winner['name']} забрал {game_state['current_player']} за $1."}, broadcast=True)
    else:
        emit('log', {'text': f"🏁 {winner['name']} отказался от {game_state['current_player']}."}, broadcast=True)
    game_state['waiting_for_decision'] = False
    game_state['round'] += 1
    game_state['lock'] = True
    socketio.sleep(2)
    game_state['lock'] = False
    advance_auction()

def next_turn():
    active_players = [p for p in game_state['participants'] if can_bid(p)]
    if len(active_players) <= 1:
        winner_index = None
        for idx, p in enumerate(game_state['participants']):
            if can_bid(p): winner_index = idx; break
        if winner_index is not None:
            if game_state['current_price'] == 0:
                game_state['waiting_for_decision'] = True
                game_state['solo_winner_id'] = winner_index
                emit('log', {'text': f"🤔 {game_state['participants'][winner_index]['name']}, будете брать за $1?"}, broadcast=True)
                emit_state()
                return
            else:
                winner = game_state['participants'][winner_index]
                winner['squad'].append({"name": game_state['current_player'], "price": game_state['current_price'], "cat": game_state['current_cat'], "pos": game_state['position']})
                winner['bank'] -= game_state['current_price']
                emit('log', {'text': f"🏆 {winner['name']} забирает {game_state['current_player']} за ${game_state['current_price']:.2f}"}, broadcast=True)
        else:
            emit('log', {'text': f"🏁 Никто не забрал {game_state['current_player']}."}, broadcast=True)
        game_state['round'] += 1
        game_state['lock'] = True
        socketio.sleep(2)
        game_state['lock'] = False
        advance_auction()
    else:
        while True:
            game_state['turn_index'] = (game_state['turn_index'] + 1) % 3
            if can_bid(game_state['participants'][game_state['turn_index']]): break
        emit_state()

def advance_auction():
    rules = get_game_rules(game_state['theme'])
    positions = rules['positions']
    if not any(len(p['squad']) < 5 and p['bank'] >= 1 for p in game_state['participants']):
        game_state['active'] = False; emit('game_over', broadcast=True); return
    if game_state['round'] > 3:
        game_state['round'] = 1; game_state['position_index'] += 1
    if game_state['position_index'] >= len(positions):
        game_state['active'] = False; emit('game_over', broadcast=True); return
    game_state['starting_turn'] = (game_state['starting_turn'] + 1) % 3
    next_auction()

def next_auction():
    rules = get_game_rules(game_state['theme'])
    positions = rules['positions']
    probs = rules['probs']
    game_state['position'] = positions[game_state['position_index']]
    game_state['current_price'] = 0
    game_state['waiting_for_decision'] = False
    for p in game_state['participants']: p['passed'] = False
    attempts = 0
    while True:
        p = game_state['participants'][game_state['starting_turn']]
        if can_bid(p) or (game_state['position'] != "ВРТ" and p['bank'] >= 1 and len(p['squad']) < 5 and not p['passed']): 
            game_state['turn_index'] = game_state['starting_turn']
            break
        game_state['starting_turn'] = (game_state['starting_turn'] + 1) % 3
        attempts += 1
        if attempts > 3:
            game_state['round'] += 1
            advance_auction()
            return

    rand = random.random() * 100
    if rand < probs[0]: cat = "топ"
    elif rand < probs[0] + probs[1]: cat = "средний"
    else: cat = "слабый"
    
    pool = PLAYERS_POOL[game_state['theme']][game_state['position']][cat]
    available = [p for p in pool if p not in game_state['used_players']]
    
    if available:
        name = random.choice(available); game_state['used_players'].append(name); game_state['current_player'] = name; game_state['current_cat'] = cat
    else:
        all_pool = []
        for c in ["топ", "средний", "слабый"]:
            if game_state['position'] in PLAYERS_POOL[game_state['theme']]:
                all_pool.extend(PLAYERS_POOL[game_state['theme']][game_state['position']].get(c, []))
        available = [p for p in all_pool if p not in game_state['used_players']]
        if available: 
            name = random.choice(available); game_state['used_players'].append(name); game_state['current_player'] = name; game_state['current_cat'] = "любая"
        else: 
            game_state['current_player'] = "Нет игроков"; game_state['current_cat'] = "нет"
    emit_state()

def emit_state():
    socketio.emit('state_update', {
        'participants': game_state['participants'], 'position': game_state['position'],
        'round': game_state['round'], 'current_price': game_state['current_price'],
        'current_player': game_state['current_player'], 'current_cat': game_state['current_cat'],
        'turn_index': game_state['turn_index'], 'active': game_state['active'],
        'waiting_for_decision': game_state['waiting_for_decision'], 'solo_winner_id': game_state['solo_winner_id']
    })

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
