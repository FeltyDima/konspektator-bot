from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from gigachat import GigaChat

GIGACHAT_KEY = "MDE5YmRkNDAtM2QzMS03YjcwLWE5YWItOTBjY2MwNjM4NmRmOmJjZjNiZTFmLTFmZWYtNGZhNC1iOTNlLTNkNjk4YzczNzU2Mg=="

class GigaChatService:
    @staticmethod
    def get_response(prompt: str, text: str) -> str:
        try:
            with GigaChat(credentials=GIGACHAT_KEY, verify_ssl_certs=False) as giga:
                full_prompt = f"{prompt}:\n\n{text}"
                response = giga.chat(full_prompt)
                return response.choices[0].message.content
        except Exception as e:
            return f"Ошибка при обращении к GigaChat: {str(e)}"

class ActionSummary(Action):
    def name(self) -> Text:
        return "action_gigachat_summary"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        text = tracker.get_slot("text_content")
        if not text:
            dispatcher.utter_message(
                text="📄 <b>Сначала пришлите текст</b>, и я сразу начну с ним работать."
            )
            return []
        
        
        answer = GigaChatService.get_response("Сделай структурированный конспект этого текста", text)
        final_text = (
            "✨ <b>Готово! Структурированный конспект:</b>\n\n"
            + answer
        )

        dispatcher.utter_message(text=final_text)
        return []

class ActionTerms(Action):
    def name(self) -> Text:
        return "action_gigachat_terms"

    def run(self, dispatcher, tracker, domain):
        text = tracker.get_slot("text_content")
        if not text:
            dispatcher.utter_message(
                text="📄 <b>Сначала пришлите текст</b>, и я сразу начну с ним работать."
            )
            return []

        answer = GigaChatService.get_response(
            "Выпиши ключевые термины и их определения. "
            "Оформляй каждый термин с новой строки, без списков. "
            "Сначала термин, затем с новой строки его определение. "
            "Не используй маркеры, нумерацию и символы списка.",
            text
        )
        final_text = (
            "✨ <b>Готово! Определения по вашей теме:</b>\n\n"
            + answer
        )

        dispatcher.utter_message(text=final_text)
        return []

class ActionExplain(Action):
    def name(self) -> Text:
        return "action_gigachat_explain"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        text = tracker.get_slot("text_content")
        if not text:
            dispatcher.utter_message(
                text="📄 <b>Сначала пришлите текст</b>, и я сразу начну с ним работать."
            )
            return []
        
        answer = GigaChatService.get_response("Объясни предложенный текст простыми словами. Избегай сложной терминологии, но сохраняй научную точность и взрослый тон. Представь, что объясняешь тему коллеге из другой области, который не знаком с этим предметом. Текст должен быть структурированным и легким для чтения.", text)
        final_text = (
            "✨ <b>Готово! Максимально простое объяснение:</b>\n\n"
            + answer
        )

        dispatcher.utter_message(text=final_text)
        return []
