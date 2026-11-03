from repetitor_bot.prompts import build_start_prompt


def test_prompt_contains_lesson_parameters_and_original_rules():
    prompt = build_start_prompt("7", "Математика", "Дроби")
    assert "Класс: 7" in prompt
    assert "Предмет: Математика" in prompt
    assert "Тема: Дроби" in prompt
    assert "Потом задай ОДИН вопрос." in prompt
    assert "Жди ответ." in prompt
    assert 'напиши "Тема усвоена"' in prompt
    assert "Не используй LaTeX" in prompt
    assert "{, }" in prompt
