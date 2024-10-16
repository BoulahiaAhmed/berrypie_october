import streamlit as st
from groq_models_v2 import fca_checker_results, video_card_generation
from video_processing import transcribe_audio_with_whisper, extract_audio_from_video, video_media_processing
import time
import os
from concurrent.futures import ThreadPoolExecutor


default_system_message="""
You are a compliance officer. Your task is to review the following rule and verify whether the provided sales deck complies with it.
Be flexible and not very strict when reviewing the sales deck. Tend to validate rules more than refuse.
The rule should be considered violated only if the sales deck completely disregards it, in all other cases, accept and validate compliance.

Provide your evaluation in JSON format with the following fields:
- rule_name (str): The name or identifier of the rule being evaluated.
- label (bool): Return true if the sales deck complies with the rule, otherwise return false.
- part (list[str]): List of specific text parts from the sales deck that relate directly to the rule, and if the sales deck is missing text related to the rule violation, simply add: "no related content for this rule
- suggestion (list[str]): A list of recommended changes or improvements for each text mentioned in part. If no changes are needed and the rule is fully respected, leave this field empty.

Ensure the output is following this JSON schema:
{
  "rule_name": "",
  "label": true OR false,
  "part": [],
  "suggestion": []
}
"""

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


def get_book_rule_status_and_suggestion(handbook_name:str, transcript_review_output:dict):
    handbook_rules_names = []
    for rule in rules_list:
        if handbook_name in rule['handbooks']:
            handbook_rules_names.append(rule["rule_name"])
    handbook_rules_status = {rule_name: "Respected" for rule_name in handbook_rules_names}
    for suggestion in transcript_review_output['suggestions']:
        if suggestion['not_respected_rule'] in handbook_rules_names:
            handbook_rules_status[suggestion['not_respected_rule']] = {'responsible_parts':suggestion['responsible_parts'], 
                                                                        'suggestions':suggestion['suggestions']}
    return handbook_rules_status


# Define the main function
def main():
    # Set the title of the app
    st.title('Poc: Prompt Testing & Enhancement')
    st.divider()
    st.subheader("🎬 Video Upload, Audio Extraction, and Transcription")

    # File uploader for video files
    video_file = st.file_uploader("Upload a Video", type=["mp4", "mov", "avi", "mkv"])

    if video_file is not None:
        # Create the directory if it doesn't exist
        temp_video_dir = "temp_video"
        os.makedirs(temp_video_dir, exist_ok=True)
        # Save the uploaded video to the directory
        temp_video_path = os.path.join(temp_video_dir, video_file.name)
        with open(temp_video_path, "wb") as f:
            f.write(video_file.read())
        
        if video_file is not None:
            # Create the directory for the audio if it doesn't exist
            temp_audio_dir = "temp_audio"
            os.makedirs(temp_audio_dir, exist_ok=True)
            # Define the path for the extracted audio file
            temp_audio_path = os.path.join(temp_audio_dir, "extracted_audio.mp3")
            # Extract audio from the video
            audio_path = extract_audio_from_video(temp_video_path, temp_audio_path)
        
        st.success("Audio extracted successfully!")

        # Display the video
        st.video(video_file)

        # Transcribe the audio using Whisper
        st.write("Transcribing audio...")
        sales_deck = transcribe_audio_with_whisper(audio_path)
        st.text_area("Video Transcript:", sales_deck, height=250)
    st.divider()
    st.subheader('✨ AI Model Selection')
    # Dropdown to select the model
    appearing_model_name = st.radio("Select Model", ['llama-3.1-70b', 'llama-3.2-90b', 'mixtral-8x7b', 'gemma2-9b'], horizontal=True)

    if appearing_model_name == 'llama-3.1-70b':
        model_name = 'llama-3.1-70b-versatile'
        st.info("Rate limit: 30 Request Per Minute")

    if appearing_model_name == 'llama-3.2-90b':
        model_name = 'llama-3.2-90b-text-preview'
        st.info("Rate limit: 30 Request Per Minute")

    if appearing_model_name == 'mixtral-8x7b':
        model_name = 'mixtral-8x7b-32768'
        st.info("Rate limit: 30 Request Per Minute")

    if appearing_model_name == 'gemma2-9b':
        model_name = 'gemma2-9b-it'
        st.info("Rate limit: 30 Request Per Minute")

    # st.divider()
    # st.subheader('Enter Sales Deck to evaluate here: ')
    # sales_deck = st.text_area("Sales Deck:", value=default_sales_deck, height=250)

    # New rules section (no user interference)
    st.divider()
    st.subheader('👮 AI FCA officer')
    for elm in fca_handbook_list:
        st.write(f"**{elm}**")  # Displays each element in bold for clarity

    # st.divider()
    # st.subheader('🧩 Prompt Engineering')
    # st.write("Modify this prompt to evaluate the model output")
    # # Input for prompt
    # system_message = st.text_area("Prompt:", value=default_system_message, height=500)
    system_message = default_system_message

    st.divider()
    st.subheader('Model Output')
    # Call the generate function
    generate_output = st.button('Generate output')
    if generate_output:
        start = time.time()
        with st.spinner(text="Reviewing In progress..."):
            with ThreadPoolExecutor() as executor:
                # Submit both tasks to run in parallel
                future_transcript = executor.submit(fca_checker_results, rules_list, system_message, model_name, sales_deck)
                future_video = executor.submit(video_media_processing, temp_video_path)
                
                # Get results
                transcript_review_output = future_transcript.result()
                video_review_output = future_video.result()
                output = {'transcript_review_output': transcript_review_output, 'video_review_output': video_review_output}

        end = time.time()

        st.write(f"Reviewing Duration: {end-start:.2f} seconds")

        st.subheader("Audio Media reviewing results")
        for handbook in fca_handbook_list:
            if handbook in output['transcript_review_output']['not_respected_fca_handbooks']:
                with st.expander(f"{handbook} ❌", expanded=False):
                    handbook_rules_status = get_book_rule_status_and_suggestion(handbook, transcript_review_output)
                    for rule in handbook_rules_status.keys():
                        if isinstance(handbook_rules_status[rule], str):
                            st.write(f"{rule} ✔️")
                        else:
                            st.write(f"{rule} ❌")
                            with st.popover("Responsible Parts & Suggestions"):
                                for i, part in enumerate(handbook_rules_status[rule]['responsible_parts']):
                                    st.write(f"{i+1} Part to modify: {part}")
                                    st.write(f"Suggestion: {handbook_rules_status[rule]['suggestions'][i]}")
                                    st.divider()
            else:
                with st.expander(f"{handbook} ✔️", expanded=False):
                    handbook_rules_status = get_book_rule_status_and_suggestion(handbook, transcript_review_output)
                    for rule in handbook_rules_status.keys():
                        st.write(f"{rule} ✔️")

                    
        st.subheader("Video Media reviewing results")
        disclaimer_status = output['video_review_output']["disclaimer_is_exist"]
        disclaimer_text = output['video_review_output']["disclaimer_text"]
        if disclaimer_status:
            st.write("Disclaimer Exist ✔️")
            st.write("Disclaimer: ", disclaimer_text)
        else:
            st.write("No disclaimer found! Please add one ⚠️")

    st.divider()
    st.subheader('Product card')
    generate_model_card = st.button('Product card')
    if generate_model_card:
        with st.spinner(text="Generation In progress..."):
            video_card = video_card_generation(sales_deck, model_name)
        st.markdown(video_card)


# Run the app

if __name__ == "__main__":
    main()
