from flask import Flask, send_from_directory
from flask_socketio import SocketIO, emit
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

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


# ==================== СИМВОЛИЧЕСКАЯ СБОРНАЯ ====================
SCHEMES = {
    "4-4-2":   ["ВРТ", "ЦЗ", "ЦЗ", "ЛЗ", "ПЗ", "ЦОП", "ЦП", "ЛП", "ПП", "ФРВ", "ФРВ"],
    "4-3-3":   ["ВРТ", "ЦЗ", "ЦЗ", "ЛЗ", "ПЗ", "ЦОП", "ЦП", "ЦАП", "ЛВ", "ПВ", "ФРВ"],
    "4-2-3-1": ["ВРТ", "ЦЗ", "ЦЗ", "ЛЗ", "ПЗ", "ЦОП", "ЦП", "ЛВ", "ЦАП", "ПВ", "ФРВ"],
}

POS_TO_POOL = {"ЛВ": "ЛП", "ПВ": "ПП", "ЛП": "ЛВ", "ПП": "ПВ"}

CLUBS = {
    "Реал": {
        "players": {
            "ВРТ": [
                {"name": "Касильяс", "alt": []},
                {"name": "Куртуа", "alt": []},
                {"name": "Навас", "alt": []},
            ],
            "ЦЗ": [
                {"name": "Рамос", "alt": ["ПЗ"]},
                {"name": "Пепе", "alt": []},
                {"name": "Варан", "alt": []},
                {"name": "Карвальо", "alt": []},
                {"name": "Йерро", "alt": []},
                {"name": "Рюдигер", "alt": []},
                {"name": "Начо", "alt": ["ПЗ"]},
            ],
            "ЛЗ": [
                {"name": "Марсело", "alt": ["ЛП"]},
                {"name": "Роберто Карлос", "alt": []},
                {"name": "Менди", "alt": []},
            ],
            "ПЗ": [
                {"name": "Карвахаль", "alt": ["ПП"]},
                {"name": "Сальгадо", "alt": []},
                {"name": "Арбелоа", "alt": []},
                {"name": "Вальверде", "alt": ["ЦП"]},
            ],
            "ЦОП": [
                {"name": "Макелеле", "alt": ["ЦП"]},
                {"name": "Каземиро", "alt": ["ЦП", "ЦЗ"]},
                {"name": "Алонсо", "alt": ["ЦП"]},
                {"name": "Кросс", "alt": ["ЦП"]},
            ],
            "ЦП": [
                {"name": "Модрич", "alt": ["ЦАП"]},
                {"name": "Гути", "alt": ["ЦАП"]},
                {"name": "Иско", "alt": ["ЦАП", "ЛП"]},
            ],
            "ЦАП": [
                {"name": "Зидан", "alt": ["ЦП"]},
                {"name": "Озил", "alt": ["ПП"]},
                {"name": "Бекхэм", "alt": ["ЦП", "ПП"]},
                {"name": "Беллингем", "alt": ["ЦП"]},
            ],
            "ЛВ": [
                {"name": "Криштиану Роналду", "alt": ["ФРВ"]},
                {"name": "Винисиус", "alt": ["ЛП"]},
                {"name": "Асенсио", "alt": ["ПВ"]},
            ],
            "ПВ": [
                {"name": "Бэйл", "alt": ["ПП"]},
                {"name": "Фигу", "alt": []},
                {"name": "Ди Мария", "alt": ["ПП"]},
                {"name": "Лукас Васкес", "alt": ["ПЗ"]},
            ],
            "ФРВ": [
                {"name": "Рауль", "alt": []},
                {"name": "Бензема", "alt": []},
                {"name": "Игуаин", "alt": []},
                {"name": "Роналдо", "alt": []},
                {"name": "Мбаппе", "alt": []},
            ],
        },
        "coaches": ["Дель Боске", "Моуринью", "Анчелотти", "Зидан"],
    },
}

DRAFT_STATE = {
    "active": False,
    "club": "Реал",
    "scheme": "4-4-2",
    "pool": [],
    "subs": [],
    "starters": [],
    "coach": None,
    "trio": [],
    "current_player_index": 0,
    "players_order": [0, 1, 2],
    "results": {},
    "sub_phase": False,
    "sub_index": 0,
    "sub_used": None,
    "sub_decision_pending": False,
    "confirm_phase": False,
    "pending_choice": None,
}


def draft_build_pool(club):
    pool = []
    for pos, players in club["players"].items():
        for p in players:
            pool.append({"name": p["name"], "pos": pos, "alt": p["alt"], "type": "player"})
    for c in club["coaches"]:
        pool.append({"name": c, "pos": "ТРЕНЕР", "alt": [], "type": "coach"})
    return pool


def player_can_play(player_pos, player_alt, slot_pos):
    slot_pool = POS_TO_POOL.get(slot_pos, slot_pos)
    if player_pos == slot_pos or POS_TO_POOL.get(player_pos, player_pos) == slot_pool:
        return True
    for a in player_alt:
        if a == slot_pos or POS_TO_POOL.get(a, a) == slot_pool:
            return True
    return False


def draft_scheme_view(st):
    scheme = SCHEMES[st["scheme"]]
    view = [{"pos": pos, "name": None} for pos in scheme]
    for s in st["starters"]:
        view[s["slot_index"]]["name"] = s["name"]
    return view


def build_options(st, chosen):
    scheme = SCHEMES[st["scheme"]]
    occupied = {s["slot_index"]: s for s in st["starters"]}
    free_slots = [i for i in range(len(scheme)) if i not in occupied]
    options = []
    for i in free_slots:
        can = player_can_play(chosen["pos"], chosen["alt"], scheme[i])
        options.append({
            "type": "place", "slot_index": i, "slot_pos": scheme[i],
            "moves": [], "off_position": not can
        })
    for occ_idx, occ in occupied.items():
        if not player_can_play(chosen["pos"], chosen["alt"], scheme[occ_idx]):
            continue
        for free_idx in free_slots:
            if player_can_play(occ["pos"], occ.get("alt", []), scheme[free_idx]):
                options.append({
                    "type": "swap", "slot_index": occ_idx, "slot_pos": scheme[occ_idx],
                    "moves": [{"from_slot": occ_idx, "to_slot": free_idx,
                               "player": occ["name"], "to_pos": scheme[free_idx]}],
                })
    return options


def draft_emit():
    st = DRAFT_STATE
    sub = None
    if st["sub_phase"] and st["sub_index"] < len(st["subs"]):
        sub = st["subs"][st["sub_index"]]
    socketio.emit('draft_state', {
        "active": st["active"],
        "club": st["club"],
        "scheme": st["scheme"],
        "current_player_index": st["current_player_index"],
        "current_player_name": game_state["participants"][st["current_player_index"]]["name"],
        "starters": st["starters"],
        "scheme_view": draft_scheme_view(st),
        "coach": st["coach"],
        "trio": st["trio"],
        "sub_phase": st["sub_phase"],
        "sub_decision_pending": st["sub_decision_pending"],
        "sub": sub,
        "sub_total": len(st["subs"]),
        "sub_index": st["sub_index"],
        "confirm_phase": st["confirm_phase"],
        "pending_choice": st["pending_choice"],
        "results": st["results"],
    })


def draft_next_trio():
    st = DRAFT_STATE
    # 11 игроков + тренер — переход к заменам
    if len(st["starters"]) >= 11 and st["coach"] is not None:
        st["sub_phase"] = True
        st["sub_index"] = 0
        st["trio"] = []
        return

    # 12-й пик: 11 игроков, тренера нет — обязательно минимум 1 тренер
    if len(st["starters"]) >= 11 and st["coach"] is None:
        coaches = [p for p in st["pool"] if p["type"] == "coach"]
        if not coaches:
            st["sub_phase"] = True
            st["sub_index"] = 0
            st["trio"] = []
            return
        chosen_coach = random.choice(coaches)
        rest_pool = [p for p in st["pool"] if p is not chosen_coach]
        extra = random.sample(rest_pool, min(2, len(rest_pool)))
        st["trio"] = [chosen_coach] + extra
        return

    # пики 1–11
    if len(st["pool"]) < 3:
        st["trio"] = []
        st["confirm_phase"] = True
        return

    players = [p for p in st["pool"] if p["type"] == "player"]
    coaches = [p for p in st["pool"] if p["type"] == "coach"]

    # придерживаем последнего тренера, если он ещё не выбран
    coaches_available = coaches
    if st["coach"] is None and len(coaches) == 1:
        coaches_available = []

    candidates = players + coaches_available
    if len(candidates) < 3:
        st["trio"] = candidates
        return
    st["trio"] = random.sample(candidates, 3)


@socketio.on('draft_start')
def handle_draft_start(data):
    if data.get('player_index') != 0:
        return
    scheme = data.get('scheme', '4-4-2')
    club_name = data.get('club', 'Реал')
    club = CLUBS[club_name]
    DRAFT_STATE.update({
        "active": True, "club": club_name, "scheme": scheme,
        "starters": [], "coach": None, "trio": [],
        "current_player_index": 0, "results": {},
        "sub_phase": False, "sub_index": 0, "sub_used": None,
        "sub_decision_pending": False, "confirm_phase": False, "pending_choice": None,
    })
    pool = draft_build_pool(club)
    subs = random.sample(pool, 8)
    DRAFT_STATE["subs"] = subs
    DRAFT_STATE["pool"] = [p for p in pool if p not in subs]
    draft_next_trio()
    draft_emit()


@socketio.on('draft_pick')
def handle_draft_pick(data):
    st = DRAFT_STATE
    if not st["active"] or st["sub_phase"] or st["confirm_phase"]:
        return
    if data.get('player_index') != st["current_player_index"]:
        return
    if st["pending_choice"] is not None:
        return
    idx = int(data.get('index', -1))
    if idx < 0 or idx >= len(st["trio"]):
        return
    chosen = st["trio"][idx]

    # 12-й пик: только тренер
    if len(st["starters"]) >= 11 and st["coach"] is None and chosen["type"] != "coach":
        return

    # Зидан: если уже тренером — игрока нельзя
    if chosen["type"] == "player" and st["coach"] == chosen["name"]:
        return
    # Зидан: если уже в старте — тренера нельзя
    if chosen["type"] == "coach":
        if st["coach"] is not None:
            return
        if any(s["name"] == chosen["name"] for s in st["starters"]):
            return

    if chosen["type"] == "coach":
        st["coach"] = chosen["name"]
        st["pool"] = [p for p in st["pool"] if p not in st["trio"]]
        st["trio"] = []
        draft_next_trio()
        draft_emit()
        return

    options = build_options(st, chosen)
    st["pending_choice"] = {"chosen": chosen, "options": options}
    draft_emit()


@socketio.on('draft_choose_position')
def handle_draft_choose_position(data):
    st = DRAFT_STATE
    if not st["active"] or st["pending_choice"] is None:
        return
    if data.get('player_index') != st["current_player_index"]:
        return
    opt_idx = int(data.get('option_index', -1))
    opts = st["pending_choice"]["options"]
    if opt_idx < 0 or opt_idx >= len(opts):
        return
    chosen = st["pending_choice"]["chosen"]
    apply_option(st, chosen, opts[opt_idx])
    st["pool"] = [p for p in st["pool"] if p not in st["trio"]]
    st["pending_choice"] = None
    st["trio"] = []
    draft_next_trio()
    draft_emit()


def apply_option(st, chosen, opt):
    if opt["type"] == "place":
        st["starters"].append({
            "name": chosen["name"], "pos": chosen["pos"], "alt": chosen["alt"],
            "slot_index": opt["slot_index"], "type": "player",
            "off_position": opt.get("off_position", False)
        })
    else:
        for mv in opt["moves"]:
            for s in st["starters"]:
                if s["slot_index"] == mv["from_slot"]:
                    s["slot_index"] = mv["to_slot"]
                    break
        st["starters"].append({
            "name": chosen["name"], "pos": chosen["pos"], "alt": chosen["alt"],
            "slot_index": opt["slot_index"], "type": "player"
        })


@socketio.on('draft_move')
def handle_draft_move(data):
    st = DRAFT_STATE
    if not st["active"] or st["sub_phase"] or st["confirm_phase"] or st["pending_choice"]:
        return
    if data.get('player_index') != st["current_player_index"]:
        return
    from_slot = int(data.get('from_slot', -1))
    to_slot = int(data.get('to_slot', -1))
    scheme = SCHEMES[st["scheme"]]
    if from_slot < 0 or to_slot < 0 or from_slot >= len(scheme) or to_slot >= len(scheme):
        return
    if from_slot == to_slot:
        return
    from_player = None
    to_player = None
    for s in st["starters"]:
        if s["slot_index"] == from_slot:
            from_player = s
        if s["slot_index"] == to_slot:
            to_player = s
    if from_player is None:
        return
    # без проверки позиции
    if to_player is not None:
        to_player["slot_index"] = from_slot
        to_player["off_position"] = not player_can_play(to_player["pos"], to_player.get("alt", []), scheme[from_slot])
    from_player["slot_index"] = to_slot
    from_player["off_position"] = not player_can_play(from_player["pos"], from_player.get("alt", []), scheme[to_slot])
    draft_emit()


@socketio.on('draft_skip_trio')
def handle_draft_skip_trio(data):
    st = DRAFT_STATE
    if not st["active"] or st["sub_phase"] or st["confirm_phase"] or st["pending_choice"]:
        return
    if data.get('player_index') != st["current_player_index"]:
        return
    if not st["trio"]:
        return
    # на 12-м пике пропуск запрещён
    if len(st["starters"]) >= 11 and st["coach"] is None:
        return
    st["pool"] = [p for p in st["pool"] if p not in st["trio"]]
    st["trio"] = []
    draft_next_trio()
    draft_emit()


@socketio.on('draft_sub_decision')
def handle_draft_sub_decision(data):
    st = DRAFT_STATE
    if not st["active"] or not st["sub_phase"]:
        return
    if data.get('player_index') != st["current_player_index"]:
        return
    if not data.get('use'):
        st["sub_index"] += 1
        st["sub_decision_pending"] = False
        if st["sub_index"] >= len(st["subs"]):
            st["sub_phase"] = False
            st["confirm_phase"] = True
        draft_emit()
        return
    st["sub_decision_pending"] = True
    draft_emit()


@socketio.on('draft_sub_apply')
def handle_draft_sub_apply(data):
    st = DRAFT_STATE
    if not st["active"] or not st["sub_decision_pending"]:
        return
    if data.get('player_index') != st["current_player_index"]:
        return
    idx = int(data.get('starter_index', -1))
    if idx < 0 or idx >= len(st["starters"]):
        return
    sub = st["subs"][st["sub_index"]]
    old = st["starters"][idx]
    st["starters"][idx] = {
        "name": sub["name"], "pos": sub["pos"], "alt": sub.get("alt", []),
        "slot_index": old["slot_index"], "type": "player",
        "off_position": old.get("off_position", False)
    }
    st["sub_used"] = {"from": old["name"], "to": sub["name"]}
    st["sub_decision_pending"] = False
    st["sub_phase"] = False
    st["confirm_phase"] = True
    draft_emit()


@socketio.on('draft_confirm')
def handle_draft_confirm(data):
    st = DRAFT_STATE
    if not st["active"] or not st["confirm_phase"]:
        return
    if data.get('player_index') != st["current_player_index"]:
        return
    st["confirm_phase"] = False
    draft_finish_current()


def draft_finish_current():
    st = DRAFT_STATE
    st["results"][st["current_player_index"]] = {
        "starters": [{"name": p["name"], "pos": p["pos"], "slot_pos": SCHEMES[st["scheme"]][p["slot_index"]], "off_position": p.get("off_position", False)} for p in st["starters"]],
        "coach": st["coach"],
        "scheme": st["scheme"],
        "sub_used": st["sub_used"],
    }
    order = st["players_order"]
    cur = st["current_player_index"]
    pos = order.index(cur)
    if pos + 1 < len(order):
        st["current_player_index"] = order[pos + 1]
        st["starters"] = []
        st["coach"] = None
        st["sub_phase"] = False
        st["sub_index"] = 0
        st["sub_used"] = None
        st["sub_decision_pending"] = False
        st["confirm_phase"] = False
        st["pending_choice"] = None
        club = CLUBS[st["club"]]
        pool = draft_build_pool(club)
        subs = random.sample(pool, 8)
        st["subs"] = subs
        st["pool"] = [p for p in pool if p not in subs]
        draft_next_trio()
    else:
        st["active"] = False
        socketio.emit('draft_finished', {"results": st["results"]}, broadcast=True)
    draft_emit()


# ==================== МАРШРУТЫ ====================
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


# ==================== АУКЦИОН ====================
@socketio.on('login')
def handle_login(data):
    idx = data.get('player_index')
    if idx in [0, 1, 2]:
        connected_players.add(idx)
        emit('players_ready', len(connected_players) == 3, broadcast=True)


@socketio.on('start_game')
def handle_start_game(data):
    if data.get('player_index') != 0 or len(connected_players) < 3:
        return
    theme = data['theme']
    rules = get_game_rules(theme)
    DRAFT_STATE["active"] = False
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
    if player['passed'] or player['bank'] < 1 or len(player['squad']) >= 5:
        return False
    if game_state['position'] == "ВРТ":
        has_gk = any(p['pos'] == "ВРТ" for p in player['squad'])
        if has_gk:
            return False
    return True


@socketio.on('place_bid')
def handle_bid(data):
    if game_state['lock'] or not game_state['active'] or game_state['waiting_for_decision']:
        return
    player = game_state['participants'][game_state['turn_index']]
    if not can_bid(player):
        return
    amount = float(data['amount'])
    if amount > player['bank'] or amount <= game_state['current_price']:
        return
    game_state['current_price'] = amount
    emit('log', {'text': f"{player['name']} ставит ${amount:.2f}"}, broadcast=True)
    game_state['lock'] = True
    socketio.sleep(0.5)
    game_state['lock'] = False
    next_turn()


@socketio.on('pass_auction')
def handle_pass():
    if game_state['lock'] or not game_state['active'] or game_state['waiting_for_decision']:
        return
    player = game_state['participants'][game_state['turn_index']]
    player['passed'] = True
    emit('log', {'text': f"❌ {player['name']} уступает."}, broadcast=True)
    game_state['lock'] = True
    socketio.sleep(0.5)
    game_state['lock'] = False
    next_turn()


@socketio.on('solo_decision')
def handle_solo_decision(data):
    if not game_state['waiting_for_decision']:
        return
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
            if can_bid(p):
                winner_index = idx
                break
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
            if can_bid(game_state['participants'][game_state['turn_index']]):
                break
        emit_state()


def advance_auction():
    rules = get_game_rules(game_state['theme'])
    positions = rules['positions']
    if not any(len(p['squad']) < 5 and p['bank'] >= 1 for p in game_state['participants']):
        game_state['active'] = False
        emit('game_over', broadcast=True)
        return
    if game_state['round'] > 3:
        game_state['round'] = 1
        game_state['position_index'] += 1
    if game_state['position_index'] >= len(positions):
        game_state['active'] = False
        emit('game_over', broadcast=True)
        return
    game_state['starting_turn'] = (game_state['starting_turn'] + 1) % 3
    next_auction()


def next_auction():
    rules = get_game_rules(game_state['theme'])
    positions = rules['positions']
    probs = rules['probs']
    game_state['position'] = positions[game_state['position_index']]
    game_state['current_price'] = 0
    game_state['waiting_for_decision'] = False
    for p in game_state['participants']:
        p['passed'] = False
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
    if rand < probs[0]:
        cat = "топ"
    elif rand < probs[0] + probs[1]:
        cat = "средний"
    else:
        cat = "слабый"

    pool = PLAYERS_POOL[game_state['theme']][game_state['position']][cat]
    available = [p for p in pool if p not in game_state['used_players']]

    if available:
        name = random.choice(available)
        game_state['used_players'].append(name)
        game_state['current_player'] = name
        game_state['current_cat'] = cat
    else:
        all_pool = []
        for c in ["топ", "средний", "слабый"]:
            if game_state['position'] in PLAYERS_POOL[game_state['theme']]:
                all_pool.extend(PLAYERS_POOL[game_state['theme']][game_state['position']].get(c, []))
        available = [p for p in all_pool if p not in game_state['used_players']]
        if available:
            name = random.choice(available)
            game_state['used_players'].append(name)
            game_state['current_player'] = name
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
        'turn_index': game_state['turn_index'], 'active': game_state['active'],
        'waiting_for_decision': game_state['waiting_for_decision'], 'solo_winner_id': game_state['solo_winner_id']
    })


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
