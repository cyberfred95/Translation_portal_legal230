prompts_list = {
    "en": [
        {
            "name": "Hide personal data",
            "description": "Replace data such as names, birth dates, email, addresses or figures by “XXX”",
            "slug": "hide-personal-data",
            "prompt": """You will replace data in the text following the instructions described in each option. 
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

                    ###start of text###
                    {text}
                     ###end of text###
                    """
        },

        {
            "name": "Replace hate speech",
            "description": "Replace any kind of hate speech or obscenities with non violent communication",
            "slug": "replace-hate-speech",
            "prompt": """### Instructions ### 
                    Rephrase the text in the same language by replacing any obscenities with appropriate wording or hate speach with non-violent communication. The tone should remain professional.

                    ### Example input 1### 
                    He is an asshole.

                    ### Example output 1### 
                    He is a bad person.

                    ### Example input 2### 
                    Look at that nigger.

                    ### Example output 2### 
                    Look at that black person.

                    ### Example input 3### 
                    You’re always late and that upset me.

                    ### Example output 3### 
                    I’m upset that you were late.

                    ###start of text###

                    {text}
                    ###endof text###"""
        },
        {
            "name": "Simplify a text",
            "description": "Simplify a technical text by using a user-friendly terminology",
            "slug": "simplify-text",
            "prompt": """Simplify the text. Answer in the language of the text. Act as if you were explaining to a kid.

                    ###start of the text###

                    {text}

                    ###end of the text###"""
        },
        {
            "name": "Summarization",
            "description": "Summarises a document laying out an introduction, a development containing the main facts and a conclusion.",
            "slug": "summarization",
            "prompt": """###Role###
                    Change the gender of the text

                    ###Instructions###
                    1.  
                    2. Keep each sentence stating that a member leaves the meeting. 
                    3. The size of the summary must be approximately 30% of the volume of the source text.

                    ###Text to summarize###
                    {text}"""
        }
    ],
    "fr": [
        {
            "name": "Masquer les données personnelles",
            "description": "Remplace les données sensibles telles que les noms, dates, adresses, email par des «XXX»",
            "slug": "hide-personal-data",
            "prompt": """You will replace data in the text following the instructions described in each option. 
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

                    ###start of text###
                    {text}
                     ###end of text###
                    """
        },

        {
            "name": "Eliminer les offenses et discours haineux",
            "description": "Remplace les offenses, les discours d’incitation à la haine ou les obscénités par une communication non violente",
            "slug": "replace-hate-speech",
            "prompt": """### Instructions ### 
                    Rephrase the text in the same language by replacing any obscenities with appropriate wording or hate speach with non-violent communication. The tone should remain professional.

                    ### Example input 1### 
                    He is an asshole.

                    ### Example output 1### 
                    He is a bad person.

                    ### Example input 2### 
                    Look at that nigger.

                    ### Example output 2### 
                    Look at that black person.

                    ### Example input 3### 
                    You’re always late and that upset me.

                    ### Example output 3### 
                    I’m upset that you were late.

                    ###start of text###

                    {text}
                    ###endof text###"""
        },
        {
            "name": "Simplifier un texte",
            "description": "Simplifie un texte technique en utilisant une terminologie plus accessible",
            "slug": "simplify-text",
            "prompt": """Simplify the text. Answer in the language of the text. Act as if you were explaining to a kid.

                    ###start of the text###

                    {text}

                    ###end of the text###"""
        },
        {
            "name": "Résumer un document",
            "description": "Résume un document avec une introduction, un développement contenant les faits principaux et une conclusion",
            "slug": "summarization",
            "prompt": """###Role###
                    Change the gender of the text

                    ###Instructions###
                    1.  
                    2. Keep each sentence stating that a member leaves the meeting. 
                    3. The size of the summary must be approximately 30% of the volume of the source text.

                    ###Text to summarize###
                    {text}"""
        }
    ]

}
