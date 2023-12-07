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
        self.is_wrap = False

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
            if self.is_wrap:
                messages = [
                    {
                        "role": "user",
                        "content": "{prompt} ###start of text###\n {message} \n###endof text###".format(prompt=self.prompt, message=message)
                    }
                ]
            response = self.openai.ChatCompletion.create(
                model="gpt-3.5-turbo-1106",
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

class Summary(Processor):
    def set_prompt(self, **kwargs):
        self.is_wrap = True
        self.prompt = "You will provide a summary of the text. The size of the summary must be 20% of the original document.\n"\
                        "You will answer in the language of the text. I want you to act as a lawyer. "\
                         "I want you to start your summary with a short introduction explaining the context and parties involved, "\
                         "then you will develop the main ideas of the document. Your last sentence is a conclusion\n"

class SimplifyAText(Processor):

    def set_prompt(self, **kwargs):
        self.is_wrap = True
        self.prompt = "Simplify the text. Answer in the language of the text. Act as if you were explaining to a kid.\n"

class ReplaceHateSpeech(Processor):

    def set_prompt(self, **kwargs):
        self.is_wrap = True
        self.prompt = "Rephrase the text in the same language by replacing any obscenities"\
                       " with appropriate wording or hate speach with non-violent communication. The tone should remain professional.\n"\
                        "Example input 1 \nHe is an asshole."\
                        "Example output 1 \nHe is a bad person."\
                        "Example input 2 \nLook at that nigger."\
                        "Example output 2 \nLook at that black person."\
                        "Example input 3 \nYou’re always late and that upset me."\
                        "Example output 3 \nI’m upset that you were late.\n"

class  HidePersonalData(Processor):

    def set_prompt(self, **kwargs):
        self.is_wrap = True
        self.prompt = """
You will replace data in the text following the instructions described in each option.

[VARIABLE1:Data to be removed::|Only names|Any figures|Dates]

###Option 1:Personnal data###
Remove all types of personnal data and replace with "XXX". This includes first name, last name, company names, personal addresses, email addresses, telephone number, social security number.

###Example Option 1 input###
Mr Lewinston works at Bain & Company. The Company is the biggest firm of New-York. He was fired on 12/12/2023. He lives at 2, Villa Delmore, Los Angeles. His phone number is 01 23 42 33 43. His social security number is 2910186113878. Last year him and his colleague, Enzo Moretti, earned 2,5 million dollars working as as agents.

###Example Option 1 output###
Mr XXX works at XXX. The Company is the biggest firm of New-York. He was fired on 12/12/2023. He lives at XXX. His phone number is XXX. His social security number is XXXX. Last year him and his colleague, XXX, earned XX million dollars working as agents.

###Option 2:Only names###
Replace all names such as first names and last names by "XXX".

###Example Option 2 input###
Mr Lewinston works at Bain & Company. The Company is the biggest firm of New-York. He was fired on 12/12/2023. He lives at 2, Villa Delmore, Los Angeles. His phone number is 01 23 42 33 43. His social security number is 2910186113878. Last year he earned 2,5 million dollars working as a director. Last year him and his colleague, Enzo Moretti, earned 2,5 million dollars working as agents.

###Example Option 2 output###
Mr XXX works at Bain & Company. The Company is the biggest firm of New-York. He was fired on 12/12/2023. He lives at 2, Villa Delmore, Los Angeles. His phone number is 01 23 42 33 43. His social security number is 2910186113878. Last year him and his colleague, XXX, earned 2,5 million dollars working as agents.

###Option 3: Financial data###
Replace all financial information by "XXX". Other figures such as telephone numbers or part of addresses can be left out.

###Example Option 3 input###
Mr Lewinston works at Bain & Company. The Company is the biggest firm of New-York. He was fired on 12/12/2023. He lives at 2, Villa Delmore, Los Angeles. His phone number is 01 23 42 33 43. His social security number is 2910186113878. His 2014 bonus was of €250,0000. Last year him and his colleague, Enzo Moretti, earned 2,5 million dollars working as agents.

###Example Option 3 output###
Mr Lewinston works at Bain & Company. The Company is the biggest firm of New-York. He was fired on 12/12/2023. He lives at 2, Villa Delmore, Los Angeles. His phone number is 01 23 42 33 43. His social security number is 2910186113878. His 2014 bonus was of €XXX. Last year him and his colleague, Enzo Moretti, earned XXX million dollars working as agents.

###Option 4: Dates###
Replace any date by XXX but keep the format of the source text.

###Example Option 4 input###
Mr Lewinston works at Bain & Company. He was fired on 12/12/2023. He lives at 2, Villa Delmore, Los Angeles. His phone number is 01 23 42 33 43. His social security number is 2910186113878. On Thursday, 4 December he asked for a bonus.

###Example Option 4 output###
Mr Lewinston works at Bain & Company. He was fired on XX/XX/XX. He lives at 2, Villa Delmore, Los Angeles. His phone number is 01 23 42 33 43. His social security number is 2910186113878. On XX, X XX he asked for a bonus.
\n"""


class ChangeTheGender(Processor):
    def set_prompt(self, **kwargs):
        self.is_wrap = True
        self.prompt = """
Change the gender in the text and adapt pronouns and adjectives when necessary. You will make the changes in the language of the text.

Style
Mr should be changed to Mrs
Mrs should be changed to Mr
M. should be changed to Mme
Mme should be changed to M.
Monsieur should be changed to Madame
Madame should be changed to Monsieur
Family names must not be changed

Style
Example input
Chang Yue, you should go with him

Example output
Chang Yue, you should go with her

Example input
Mrs Lindt is a very beautiful women.

Example output
Mr Lindt is a very handsome men.\n
"""