from abc import ABC, abstractmethod
import openai
from preferences import preferences
import time


def retry_on_error(func, max_retries=5, delay=3):
    def wrapper(*args, **kwargs):
        retries = 0
        while retries < max_retries:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                retries += 1
                time.sleep(delay)
        raise Exception('error')

    return wrapper


class Processor(ABC):

    def __init__(self, text: list, **kwargs):
        """
        Class to translate by GPT 3.5 Turbo
        :param text: Text to translate
        """
        self.text = text
        self.prompt = None
        self.openai = openai
        self.openai.api_key = ''
        self.openai.api_base = 'https://api.openai.com/v1'
        self.openai.api_type = 'open_ai'
        self.result = []
        self.set_prompt(**kwargs)

    def process(self):
        for message in self.text:
            self.result.append(
                self.gpt_send(message)
            )
        return self.result

    @abstractmethod
    def set_prompt(self, **kwargs):
        pass

    @retry_on_error
    def gpt_send(self, message: str):
        if self.prompt is not None:
            messages = [
                {
                    "role": "user",
                    "content": "{prompt} {message}".format(prompt=self.prompt, message=message)
                }
            ]
            response = self.openai.ChatCompletion.create(
                model="gpt-3.5-turbo-0301",
                messages=messages,
                temperature=0.3
            )
            res = response.choices[0].message.content
            res = res.replace('\n', '')
            return res
        return None


class Translate(Processor):

    def set_prompt(self, **kwargs):
        self.prompt = "You are a helpful translator from {input_language} to {target_language}. " \
                     "You only reply with translations and do not provide any notes nor explanations. " \
                     "Translate the following text:".format(
                        input_language=kwargs['source_language'],
                        target_language=kwargs['target_language']
        )


class RewriteForGenderNeutrality(Processor):

    def set_prompt(self, **kwargs):
        self.prompt = "You are a helpful editor tasked with rewriting texts to be gender-neutral," \
                     " either by providing all possible gender variants ('husband/wife' instead of 'husband')" \
                     " or changing the word choice to be neutral ('spouse' instead of 'husband'): " \
                     "your choice is based on what's more appropriate in context. " \
                     "You only reply with rewritten texts and do not provide any notes nor explanations. " \
                     "Rewrite the following text:"


class RewriteForOtherGender(Processor):

    def set_prompt(self, **kwargs):
        self.prompt = "You are a helpful editor tasked with rewriting texts to assume other gender of the reader. " \
                      "You only reply with rewritten texts and do not provide any notes nor explanations." \
                      " Rewrite the following text to assume " \
                      "the reader is of {gender} gender and goes by {pronouns}:".format(
                        gender=kwargs['gender'],
                        pronouns=kwargs['pronouns']
        )


class RewriteForSimplicity(Processor):

    def set_prompt(self, **kwargs):
        self.prompt = "You are a helpful editor who rewrites texts to be simple and easy to understand. " \
                      "You can change grammar to make sentences more concise and split constructions " \
                      "to make them shorter, paraphrase avoiding difficult terms or use synonims, " \
                      "but the result must always stay grammaticaly correct. You only reply with rewritten " \
                      "texts and do not provide any notes nor explanations. Rewrite the following text for simplicity:"


class RewriteInOtherPerson(Processor):

    def set_prompt(self, **kwargs):
        self.prompt = "You are a helpful editor who rewrites texts in other grammatical person " \
                      "(first, second or third). You only reply with rewritten texts and do not provide " \
                      "any notes nor explanations. Rewrite the following text in {person}:".format(
                        person=kwargs['person']
        )


class CleanOutObscenities(Processor):

    def set_prompt(self, **kwargs):
        self.prompt = "Remove any offensive language from the following text, " \
                      "changing grammatical structure if needed but providing no notes nor explanations:"


class Summarize(Processor):

    def set_prompt(self, **kwargs):
        self.prompt = "Provide a brief summary of the following text:"
