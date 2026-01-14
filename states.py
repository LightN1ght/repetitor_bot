from aiogram.fsm.state import State, StatesGroup

class StudyStates(StatesGroup):
    waiting_for_class = State()
    waiting_for_subject = State()
    waiting_for_topic = State()
    in_learning = State()
