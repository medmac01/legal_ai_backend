# rules_engine.py

# Translated rules from "3.1 Instructions specific to NDAs"
NDA_DRAFTING_RULES = {
    "Preamble and Parties": {
        "description": "The introductory section identifying the parties and effective date.",
        # "instructions": "Draft a standard preamble for a Non-Disclosure Agreement between [Party 1 Name], [Party 1 Type and Address], and [Party 2 Name], [Party 2 Type and Address]. The effective date should be [Effective Date]. Clearly identify which party is the Disclosing Party and which is the Receiving Party based on the user's role selection. If it's a bilateral agreement, state that both parties will act as Disclosing and Receiving Parties.",
        "instructions": [
            "This Non-Disclosure Agreement (the \"Agreement\") is entered into as of [Effective Date] (the \"Effective Date\"), between\n",
            "[Party 1 Name], a public limited liability company duly organized and existing under the laws of Morocco, with a share capital of [Capital], having its registered office at [First Party Address], incorporated with the Register of Companies of Casablanca under number [First Party Registration Number], represented by [First Party Representative], duly empowered (hereinafter referred to as the 'Disclosing Party');\n And,\n",
            "[Party 2 Name], a public limited liability company duly organized and existing under the laws of Morocco, with a share capital of [Capital], having its registered office at [Second Party Address], incorporated with the Register of Companies of Benguerir under number [Second Party Registration Number], represented by [Second Party Representative], duly empowered (hereinafter referred to as the 'Receiving Party');\n\n",
            "The Disclosing Party and the Receiving Party are hereinafter collectively referred to as the \"Parties\" and individually as a \"Party\".\n",
        ]
    },
    "Purpose": {
        "description": "The 'Whereas' or 'Background' clause.",
        "instructions": "Draft a 'Purpose' clause explaining why the confidential information is being shared. Use the following user-provided purpose: '[Purpose]'."
    },
    "Representatives": {
        "description": "Definition of who can receive the information.",
        "receiving": [
            "Define 'Representatives' narrowly. Limit the scope strictly to what is needed for the Purpose.",
            "The Receiving Party's liability for misuse by Representatives should be limited to its employees and directors only. (Mandatory)"
        ],
        "disclosing": [
            "Define 'Representatives' broadly to include employees, directors, officers, affiliates, and advisors (like banks, accountants).",
            "The Receiving Party must be held legally responsible for any breach by any of its Representatives. This must be an explicit clause. (Mandatory)"
        ],
        "mutual": "Draft a fair and balanced definition of 'Representatives', typically including employees, directors, and professional advisors (legal, financial) on a need-to-know basis. Both Parties shall be responsible for breaches by their respective Representatives."
    },
    "Confidential Information": {
        "description": "The core definition of what is considered confidential.",
        "receiving": [
            "Define 'Confidential Information' narrowly by listing the specific types of information to be shared. (Mandatory)",
            "Include a clause requiring information to be explicitly marked 'Confidential' to be protected (Optional, but preferred for Recipient).",
            "Minimum acceptable exclusions are: (a) already public, (b) received from a third party without breach, (c) already in recipient's possession, (d) independently developed. (Mandatory)"
        ],
        "disclosing": [
            "Define 'Confidential Information' as broadly as possible, covering all forms of information (written, oral, electronic). (Mandatory)",
            "Ensure oral disclosures are included and must be summarized in writing within a short period (e.g., 15 days) to be protected.",
            "Refuse any extended or non-standard exclusions. Stick to the basic public domain/prior knowledge exceptions. (Mandatory)"
        ],
        "mutual": "Draft a broad but fair definition of 'Confidential Information', including oral disclosures. Use standard exclusions that are acceptable to both sides."
    },
    "Third-Party" : {
        "description": "Definition of third-party entities and their obligations.",
        "receiving": [
            "Add as is : any natural person, legal person, corporate body, non-corporate body or any other entity, not being a Party to the Agreement nor a Representative of any of the Parties",
        ],
        "disclosing": [
            "Add as is : any natural person, legal person, corporate body, non-corporate body or any other entity, not being a Party to the Agreement nor a Representative of any of the Parties",
        ],
        "mutual": "Add as is : any natural person, legal person, corporate body, non-corporate body or any other entity, not being a Party to the Agreement nor a Representative of any of the Parties"
    },
    "Permitted Use": {
        "description": "How the information can be used by the Parties.",
        "receiving": [
            "Use Confidential Information only for the defined 'Purpose'.",
            "Do not disclose Confidential Information to any third parties during and after the term of this Agreement."
        ],
        "disclosing": [
            "Use Confidential Information only for the defined 'Purpose'.",
            "Do not disclose Confidential Information to any third parties during and after the term of this Agreement."
        ],
        "mutual": "Both Parties agree to use Confidential Information solely for the Purpose and to protect it from unauthorized disclosure during and after the term of this Agreement."
    },
    # "Use of Information": {
    #     "description": "Restrictions on how the information can be used.",
    #     "receiving": [
    #         "Limit the use of Confidential Information strictly to the defined 'Purpose'.",
    #         "Do not add extra obligations beyond a reasonable standard of care (i.e., the same care used for its own confidential information)."
    #     ],
    #     "disclosing": [
    #         "Limit the use of Confidential Information strictly to the defined 'Purpose' and prohibit any other use. (Mandatory)",
    #         "Add obligations prohibiting reverse engineering, decompiling, or unauthorized copying. (Mandatory)",
    #         "Require that disclosure is limited to Representatives on a strict 'need-to-know' basis."
    #     ],
    #     "mutual": "Draft a standard 'Permitted Use' clause limiting use to the Purpose. Include a standard of care commitment for both parties."
    # },
    "Legally Required Disclosure": {
        "description": "What happens if the Receiving Party is legally compelled to disclose information.",
        "receiving": [
            "The above provisions are applicable, unless: \n",
            "a) disclosure is required by binding law and non-disclosure could expose the Party bound by confidentiality to criminal or administrative responsibility or,\n",
            "b) disclosure is required or indispensable to protect the Party’s interests in judicial or administrative proceedings, \n",
            "c) in such case provided that the Parties – immediately after being informed on a possible duty or need for disclosure and as far as it will be possible prior to such disclosure - take all reasonable steps to promptly and sufficiently notify each other thereof. \n",
        ],
        "disclosing": [
            "The above provisions are applicable, unless: \n",
            "a) disclosure is required by binding law and non-disclosure could expose the Party bound by confidentiality to criminal or administrative responsibility or,\n",
            "b) in such case provided that the Parties – immediately after being informed on a possible duty or need for disclosure and as far as it will be possible prior to such disclosure - take all reasonable steps to promptly and sufficiently notify each other thereof. \n",
        ],
        "mutual": [
            "Both Parties agree to notify each other promptly if legally compelled to disclose Confidential Information, and to cooperate in seeking a protective order or other remedy."
        ]
    },
    "Exclusions from Confidential Information": {
        "description": "What is not considered confidential.",
        "receiving": [
            "Information that is already public knowledge at the time of disclosure or becomes public through no fault of the Receiving Party.",
            "Information received from a third party without breach of any obligation of confidentiality.",
            "Information already in the Receiving Party's possession before disclosure.",
            "Information independently developed by the Receiving Party without use of or reference to the Disclosing Party's Confidential Information."
        ],
        "disclosing": [
            "Information that is already public knowledge at the time of disclosure or becomes public through no fault of the Receiving Party.",
            "Information received from a third party without breach of any obligation of confidentiality.",
            "Information already in the Receiving Party's possession before disclosure.",
            "Information independently developed by the Receiving Party without use of or reference to the Disclosing Party's Confidential Information."
        ],
        "mutual": [
            "Information that is already public knowledge at the time of disclosure or becomes public through no fault of the Receiving Party.",
            "Information received from a third party without breach of any obligation of confidentiality.",
            "Information already in the Receiving Party's possession before disclosure.",
            "Information independently developed by the Receiving Party without use of or reference to the Disclosing Party's Confidential Information."
        ]
    },
    "Use of Confidential Information": {
        "description": "How the Receiving Party can use the information.",
        "receiving": [
            "Each Party undertakes to keep the same standard of care in protecting such other Party’s Confidential Information as a Party normally employs to preserve and safeguard its own Confidential Information.",
            "Confidential Information may be disclosed solely to those Representatives of a Party who have a need to know such information for the purposes of the cooperation.",
            "All Confidential Information and any copies thereof shall be returned to the other Party promptly upon written request."
        ],
        "disclosing": [
            "Each Party undertakes to keep the same standard of care in protecting such other Party’s Confidential Information as a Party normally employs to preserve and safeguard its own Confidential Information.",
            "Confidential Information may be disclosed only to those Representatives of the Receiving Party who have a strict need to know such information solely for the purposes of the cooperation, and who are bound by confidentiality obligations no less protective than those in this Agreement.",
            "The Receiving Party shall not reproduce, copy, or otherwise duplicate any Confidential Information without the prior written consent of the Disclosing Party.",
            "The Receiving Party agrees to take all necessary steps to safeguard the Confidential Information from loss, theft, unauthorized access, or destruction, and to ensure its secure handling and storage.",
            "All Confidential Information and any copies thereof shall be returned to the other Party promptly upon written request, or destroyed at the Disclosing Party's option, with a written certificate of destruction provided by the Receiving Party."
        ],
        "mutual": [
            "Each Party undertakes to keep the same standard of care in protecting the other Party’s Confidential Information as it normally employs to preserve and safeguard its own Confidential Information.",
            "Confidential Information may be disclosed only to those Representatives of the Receiving Party who have a strict need to know such information solely for the purposes of the cooperation, and who are bound by confidentiality obligations no less protective than those in this Agreement.",
            "All Confidential Information and any copies thereof shall be returned to the other Party promptly upon written request, or destroyed at the Disclosing Party's option, with a written certificate of destruction provided by the Receiving Party."
        ]
    },
    "Duration": {
        "description": "The term of the agreement and the survival of confidentiality obligations.",
        "instructions": ["The confidentiality obligations shall remain in effect for [Duration] months from the Effective Date. After this period, the Receiving Party's obligations regarding Confidential Information shall continue indefinitely for any information that remains confidential by its nature.\n",
                        "All information provided by the Disclosing Party shall remain the property of the Disclosing Party. The Receiving Party agrees to return [OR to destroy] all Confidential Information to the Disclosing Party within fifteen (15) calendar days of written demand by the Disclosing Party. The risk for the Receiving Party is to remain liable too long so duration should strictly cover the time where Confidential Information will be used."
        ]
    },
    "Responsibility": {
        "description": "Who is responsible for breaches by Representatives.",
        "receiving": [
            "Each Party hereto is fully liable for damages to the other Party for any harm or damage caused to the other Party or that Party’s customers or business partners due to violation of the terms of this Agreement, including for any harm or damage caused by the breaching Party’s Representatives.",
        ],
        "disclosing": [
            "Each Party hereto is fully liable for damages to the other Party for any harm or damage caused to the other Party or that Party’s customers or business partners due to violation of the terms of this Agreement, including for any harm or damage caused by the breaching Party’s Representatives.",
        ],
        "mutual": "Each Party hereto is fully liable for damages to the other Party for any harm or damage caused to the other Party or that Party’s customers or business partners due to violation of the terms of this Agreement, including for any harm or damage caused by the breaching Party’s Representatives."
    },
    "Notices": {
        "description": "Standard boilerplate clause for notices.",
        "receiving": "Any notifications and statements pursuant to this Agreement shall be made in writing and sent via courier services or via registered mail to the Parties’ addresses [Party 1 Type and Address] for [Party 1 Name] and [Party 2 Type and Address] for [Party 2 Name] set forth in the heading of this Agreement or to the e-mail addresses agreed between the Parties.",
        "disclosing": "Any notifications and statements pursuant to this Agreement shall be made in writing and sent via courier services or via registered mail to the Parties’ addresses [Party 1 Type and Address] for [Party 1 Name] and [Party 2 Type and Address] for [Party 2 Name] set forth in the heading of this Agreement or to the e-mail addresses agreed between the Parties.",
        "mutual": "Any notifications and statements pursuant to this Agreement shall be made in writing and sent via courier services or via registered mail to the Parties’ addresses [Party 1 Type and Address] for [Party 1 Name] and [Party 2 Type and Address] for [Party 2 Name] set forth in the heading of this Agreement or to the e-mail addresses agreed between the Parties."
    },

    "Applicable Law and Jurisdiction": {
        "description": "The legal framework for the contract.",
        "instructions": "The governing law shall be [Applicable Law]. And should apply in any issue arising out of this Agreement."
    },
    "Litigation": {
        "description": "Dispute resolution mechanism.",
        "instructions": " Any dispute, controversy, or claim arising out of, or in relation to, this Agreement, including the validity, invalidity, breach, or termination thereof, which may not be effectively settled by negotiations, shall be resolved by arbitration in accordance with the [Litigation] in force on the date on which the Notice of Arbitration is submitted in accordance with these Rules. The number of arbitrators shall be one. The seat of the arbitration shall be [Litigation]. The arbitral proceedings shall be conducted in [Language]."
    },
    "General Provisions": {
        "description": "Boilerplate clauses like 'Modification', 'Non Solicitation', 'Non Assignable'.",
        "instructions": "Include standard boilerplate clauses for 'Non Solicitation', 'Modification', and 'Non Assignable'."
    },
}

GENERAL_DRAFTING_INSTRUCTIONS = """
- Use capital letters and bold text for Defined Terms (e.g., **"Confidential Information"**).
- Use capital letters every time a defined term is used subsequently.
- Check all cross-references to ensure they are logical (the LLM should handle this implicitly).
- Ensure professional, clear, and unambiguous legal language throughout.
- The final output should be a single, complete document, ready for signature. Do not include any of these instructions or any commentary in the final text.
"""

def get_role_key(party_role):
    """Translates user-friendly role to a dictionary key."""
    if party_role == "Receiving Party":
        return "receiving"
    elif party_role == "Disclosing Party":
        return "disclosing"
    else: # "Both"
        return "mutual"

def build_llm_prompt(user_inputs):
    """Builds a structured prompt for the LLM based on user inputs and rules."""
    
    role_key = get_role_key(user_inputs["first_party_role"])

    prompt = f"""
You are an expert legal AI assistant. Your task is to draft a complete Non-Disclosure Agreement based on the following context and specific clause-by-clause instructions.

**OVERALL CONTEXT:**
- This is a {user_inputs['nature_of_obligations']} Non-Disclosure Agreement.

- First Party: {user_inputs['first_party']}.
- First Party Role: {user_inputs['first_party_role']}.
- First Party Address: {user_inputs['first_party_address']}.
- First Party Incorporation State: {user_inputs['first_party_incorporation_state']}.
- First Party Registration Number: {user_inputs['first_party_registration_number']}.
- First Party Representative: {user_inputs['first_party_representative']}.

- Second Party: {user_inputs['second_party']}.
- Second Party Role: {user_inputs['second_party_role']}.
- Second Party Adress: {user_inputs['second_party_adress']}.
- Second Party Incorporation State: {user_inputs['second_party_incorporation_state']}.
- Second Party Registration Number: {user_inputs['second_party_registration_number']}.
- Second Party Representative: {user_inputs['second_party_representative']}.

- Purpose of Disclosure Type: {user_inputs['purpose_type']}
- Purpose of Disclosure: {user_inputs['purpose']}
- Applicable Law: {user_inputs['applicable_law']}
- Dispute Resolution (Litigation): {user_inputs['litigation']}
- Duration of Confidentiality: {user_inputs['duration']} months
- Language of the Contract: {user_inputs['language']}
- Effective Date: {user_inputs.get('effective_date', 'Today')}

**DRAFTING INSTRUCTIONS - CLAUSE BY CLAUSE:**

"""
    # Iterate through the rules and build the prompt chunk by chunk
    for topic, rules in NDA_DRAFTING_RULES.items():
        prompt += f"--- \n"
        prompt += f"**Clause Topic: {topic}**\n"
        
        # Get the specific instructions based on the role
        if "instructions" in rules:
            # For clauses with single instruction set (Preamble, Purpose, etc.)
            instruction_text = rules["instructions"]
        else:
            # For clauses with role-based instructions
            instruction_text = rules[role_key]

        # Format instructions nicely
        if isinstance(instruction_text, list):
            for item in instruction_text:
                prompt += f"- {item}\n"
        else:
            prompt += f"- {instruction_text}\n"

    # Add general formatting instructions at the end
    prompt += "\n--- \n"
    prompt += "**FINAL FORMATTING INSTRUCTIONS:**\n"
    prompt += GENERAL_DRAFTING_INSTRUCTIONS

    # Replace placeholders in the prompt itself
    prompt = prompt.replace("[Party 1 Name]", user_inputs['first_party'])
    prompt = prompt.replace("[Party 2 Name]", user_inputs['second_party'])
    prompt = prompt.replace("[Party 1 Type and Address]", user_inputs['first_party_adress'])
    prompt = prompt.replace("[Party 2 Type and Address]", user_inputs['second_party_adress'])
    prompt = prompt.replace("[Effective Date]", str(user_inputs.get('date', 'Today')))
    prompt = prompt.replace("[Party 1 Role]", user_inputs['first_party_role'])
    prompt = prompt.replace("[Nature of Obligations]", user_inputs['nature_of_obligations'])
    prompt = prompt.replace("[Language]", user_inputs['language'])
    prompt = prompt.replace("[Duration]", str(user_inputs['duration']))
    prompt = prompt.replace("[Purpose]", user_inputs['purpose'])
    prompt = prompt.replace("[Applicable Law]", user_inputs['applicable_law'])
    prompt = prompt.replace("[Litigation]", user_inputs['litigation'])

    return prompt