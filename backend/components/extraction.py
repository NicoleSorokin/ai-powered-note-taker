import openai
from prompt_eng.prompt_manager import PromptManager

pm = PromptManager()
lecture_title_prompt = pm.get_prompt("lecture_title")
lecture_type_prompt = pm.get_prompt("lecture_type")
general_extraction_prompt = pm.get_prompt("general_summary")
role_description = pm.get_role("extractor")
class Extraction:
    def __init__(self, api_key):
        openai.api_key = api_key
        self.transcription = None
        self.lecture_title = None
        self.lecture_type = None
        self.lecture_length = None

    def extract(self, role_description, prompt) :
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": role_description},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content

    def process(self, transcription, minutes, seconds):
        information = {
            'lecture_title': None, 
            'lecture_type': None, 
            'minutes': minutes, 
            'seconds': seconds, 
            'general_extraction': None
        }

        lecture_title = self.extract(
            role_description, 
            f"{transcription}\n\n{lecture_title_prompt}"
            )
        
        lecture_type = self.extract(
            role_description, 
            f"{transcription}\n\n{lecture_type_prompt}"
            )
        
        information['lecture_title'] = lecture_title
        information['lecture_type'] = lecture_type

        information['general_extraction'] = self.extract(
            role_description,
            f"{transcription}\n\n{general_extraction_prompt}' This was a ' {information['lecture_type']}' lecture"f"titled '{information['lecture_title']}'."f"The lecture lasted for {information['minutes']} minutes "f"and {information['seconds']} seconds. '"
        )

        return information