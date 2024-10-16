import os
from dotenv import load_dotenv
from groq import Groq
import streamlit as st 
import typing_extensions as typing
import logging
import json
import concurrent.futures
import time


GROQ_API_KEY = st.secrets["GROQ_API_KEY"]

# load_dotenv()
# GROQ_API_KEY = os.getenv('GROQ_API_KEY')

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Text Processing functions

def groq_model_generation(prompt: str, system_message: str, model: str) -> dict:
    """Model names: llama3_1, mixtral, gemma"""
    try:
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": f"{system_message}"
                },
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model=model,
            temperature=0,
            response_format={"type": "json_object"},
        )

        result = response.choices[0].message.content
        logger.info(f"Response: {result}")

        # Parse result and raise exception if it's not valid JSON
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            logger.error("Invalid JSON output string")
            raise

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        raise


def groq_inference(system_message: str, model_name: str, rule_name: str, sales_deck: str) -> typing.Optional[str]:
    """Perform inference using the groq api models and return the generated response."""
    input_text = f"""
    The rule is: {rule_name}
    The sales deck to evaluate is: {sales_deck}
    Your MUST provide an output in JSON representation with the following fields:
    "rule_name",
    "label",
    "part",
    "suggestion"
    """
    model_output = groq_model_generation(input_text, system_message, model_name)
    return model_output


def rule_check(rule: str, system_message: str, model_name: str, sales_deck: str):
    rule_name = rule['rule_name']
    rule_text = rule['rule_text']
    complete_rule_text =f"{rule_name}: {rule_text}"
    llm_result = groq_inference(system_message, model_name, complete_rule_text, sales_deck)
    return llm_result


def fca_checker_results(rules_list: list, system_message: str, model_name: str, sales_deck: str, max_retries: int = 3):
    not_respected_fca_handbooks = []
    not_respected_rules = []
    suggestions = []

    # Function to process a single rule with retry logic
    def process_rule_with_retry(rule, retries=0):
        rule_name = rule["rule_name"]
        handbooks = rule["handbooks"]

        try:
            # Simulate the rule check function
            llm_result = rule_check(rule, system_message, model_name, sales_deck)

            if llm_result["label"] == False:
                return {
                    'rule_name': rule_name,
                    'handbooks': handbooks,
                    'llm_result': llm_result
                }
            return None
        except Exception as e:
            if retries < max_retries:
                print(f"Error processing rule '{rule_name}'. Retrying ({retries + 1}/{max_retries})...")
                time.sleep(1)  # Optional: Add delay before retry
                return process_rule_with_retry(rule, retries + 1)
            else:
                print(f"Failed to process rule '{rule_name}' after {max_retries} retries. Error: {e}")
                return None

    # Use ThreadPoolExecutor to process rules in parallel
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Map the process_rule_with_retry function to each rule in rules_list
        results = list(executor.map(process_rule_with_retry, rules_list))

    # Process the results after parallel execution
    for result in results:
        if result:
            rule_name = result['rule_name']
            handbooks = result['handbooks']
            llm_result = result['llm_result']

            not_respected_fca_handbooks.extend(handbooks)
            not_respected_rules.append(rule_name)
            suggestions.append({
                'not_respected_rule': rule_name,
                'related_handbooks': handbooks,
                'responsible_parts': llm_result["part"],
                'suggestions': llm_result["suggestion"]
            })

    # Use sets to remove duplicates
    unique_not_respected_fca_handbooks = set(not_respected_fca_handbooks)
    unique_not_respected_rules = set(not_respected_rules)

    output_dict = {'not_respected_fca_handbooks': unique_not_respected_fca_handbooks,
                   'not_respected_rules': unique_not_respected_rules,
                   'suggestions': suggestions
                   }
    return output_dict


# Video Processing functions


def video_card_generation(transcript: str, model: str) -> str:
    """Model names: llama3_1, mixtral, gemma"""
    system_message = """
    Your task is to generate a concise summary from the given video transcript.
    Please follow these instructions return a markdown text:

    1. Extract Key Information:
    - Identify the company name.
    - Determine the industry, if applicable.
    - Summarize the product or service being discussed.

    2. Output Format:
    - **Company Name**: [Extracted company name]
    - **Industry**: [Extracted industry, if available]
    - **Product Summary**: [Brief summary of the product or service]

    Example:
    For a video discussing "FinGuard’s new portfolio management tool designed to help investors track and optimize their asset allocations," your output might look like:

    - Company Name: FinGuard
    - Industry: Financial Services
    - Product Summary: A portfolio management tool that assists investors in tracking and optimizing their asset allocations for improved investment outcomes.
    """
    try:
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": f"{system_message}"
                },
                {
                    "role": "user",
                    "content": f"Here is the transcript to use: {transcript}",
                }
            ],
            model=model,
            temperature=0,
        )

        result = response.choices[0].message.content
        logger.info(f"Response: {result}")
        return result
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        raise
