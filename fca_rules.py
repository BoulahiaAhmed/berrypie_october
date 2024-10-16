"""defining the list of rules"""


fca_handbook_list = ["FSMA", "FCA CONC", "FCA PRIN", "FCA COBS", "Financial promotions on social media"]


Authorization_and_Approval = {
    'rule_name': "Authorization and Approval",
    'handbooks': [fca_handbook_list[0]],
    'rule_text': "The video's content must be authorized by an appropriate person within the firm. If the video promotes an investment activity, it needs approval from an FCA-authorized individual. This helps ensure the video's content is compliant and accurate."
}

Clear_Fair_and_Not_Misleading = {
    'rule_name': "Clear, Fair, and Not Misleading",
    'handbooks': [fca_handbook_list[1], fca_handbook_list[2], fca_handbook_list[3], fca_handbook_list[4]],
    'rule_text': "This overarching principle is repeatedly emphasized across various FCA guidelines. The video's content must be presented clearly, fairly, and in a way that doesn't mislead viewers. This applies to the overall message, the presentation of risks and benefits, and any claims or statements made."
}

Risk_Warnings = {
    'rule_name': "Risk Warnings",
    'handbooks': [fca_handbook_list[1], fca_handbook_list[3], fca_handbook_list[4]],
    'rule_text': "The video must include clear and prominent risk warnings, especially if it features high-cost short-term credit (HCSTC) products or high-risk investments (HRIs). These warnings should be easily visible and understandable, not hidden in captions or supplementary text."
}

Consumer_Understanding = {
    'rule_name': "Consumer Understanding",
    'handbooks': [fca_handbook_list[2], fca_handbook_list[4]],
    'rule_text': "The video should be designed to be easily understood by its target audience. It should avoid using jargon or complex language, particularly when targeting retail clients. The information should be presented in a way that avoids confusion and empowers viewers to make informed decisions."
}

Stand_Alone_Compliance = {
    'rule_name': "Stand-Alone Compliance",
    'handbooks': [fca_handbook_list[4]],
    'rule_text': "The video must be compliant on its own, without requiring viewers to seek external information for crucial details. Risk warnings and other essential information should be clearly presented within the video itself."
}

Avoidance_of_High_Pressure_Selling = {
    'rule_name': "Avoidance of High-Pressure Selling",
    'handbooks': [fca_handbook_list[1]],
    'rule_text': "The video should not employ high-pressure tactics or create an undue sense of urgency. Viewers should be given adequate time to consider their options without feeling pressured or manipulated."
}

Suitability_of_Social_Media = {
    'rule_name': "Suitability of Social Media",
    'handbooks': [fca_handbook_list[4]],
    'rule_text': "If the video is shared on social media platforms like TikTok or Instagram, consider the platform's suitability for promoting financial products. Platforms with character limitations or specific design features might not be appropriate for complex financial products that require detailed explanations."
}


rules_list = [Authorization_and_Approval, Clear_Fair_and_Not_Misleading, Risk_Warnings, Consumer_Understanding, Stand_Alone_Compliance, Avoidance_of_High_Pressure_Selling, Suitability_of_Social_Media]
