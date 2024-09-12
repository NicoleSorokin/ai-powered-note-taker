# using all the information collected/extracted start specifically working in creating a concise summary
import openai
from prompt_eng.prompt_manager import PromptManager

pm = PromptManager()
concise_notes_prompt = pm.get_prompt("concise_notes")
processor_role = pm.get_role("processor")

class Processing:
    def __init__(self, api_key, details):
        openai.api_key = api_key
        self.general_summary = details['general_extraction']
        self.lecture_title = details['lecture_title']
        self.lecture_type = details['lecture_type']
        self.lecture_length = details['minutes'], details['seconds']

    def process(self):
        prompt = (
            f"{concise_notes_prompt}' This was a ' {self.lecture_type}' lecture"f"titled '{self.lecture_title}'."f"The lecture lasted for {self.lecture_length[0]} minutes "f"and {self.lecture_length[1]} seconds. "
        )

        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": processor_role},
                {"role": "user", "content": f"{self.general_summary}\n\n{prompt}"}
            ]
        )
        return response.choices[0].message.content