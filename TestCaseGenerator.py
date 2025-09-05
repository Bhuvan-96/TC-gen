import streamlit as st
import pandas as pd
import google.generativeai as genai
import io
import re


# Configure Gemini API
# API_KEY = os.getenv("GEM_API_KEY")

API_KEY = "AIzaSyA0VzTUpQOFBXqhNOFf-6H-0qCKPy7al9U"
genai.configure(api_key=API_KEY)
# model = genai.GenerativeModel("gemini-2.5-flash")

model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    generation_config=genai.types.GenerationConfig(
        temperature=0.2,
        top_p=0.7
        # top_k=10
    )
)


st.set_page_config(page_title="AI Test Case Generator", layout="wide")
st.title("📋 AI Test Case Generator")

# Step 1: Upload Requirement Excel
requirement_file = st.file_uploader("Upload Requirement Excel file", type=["xlsx"])
if requirement_file:
    requirement_df = pd.read_excel(requirement_file)
    st.subheader("📄 Requirement Data Preview")
    st.dataframe(requirement_df)

# Step 2: Collect Prompts
if requirement_file:
    st.markdown("### 👤 Intro Prompt")
    intro_prompt = st.text_area("Describe yourself and the purpose of this test case generation")

    st.markdown("### ✍️ Prompts for Each Requirement Column")
    requirement_prompts = {
        col: st.text_input(f"Prompt for column: {col}", key=f"req_{col}")
        for col in requirement_df.columns
    }

    st.markdown("### 🧾 Conclusion Prompt")
    conclusion_prompt = st.text_area("Add any final instructions or summary for Gemini AI")

# Step 3: Upload Test Case Template
template_file = st.file_uploader("Upload Test Case Template Excel file", type=["xlsx"])
if template_file:
    template_df = pd.read_excel(template_file)
    st.subheader("📄 Test Case Template Preview")
    st.dataframe(template_df)

# Step 4: Generate Test Cases
if requirement_file and template_file and st.button("Generate Test Cases"):
    with st.spinner("Generating test cases using Gemini AI..."):
        # Build the full prompt
        prompt_parts = [f"Context:\n{intro_prompt.strip()}\n"]
        for col, user_prompt in requirement_prompts.items():
            if user_prompt.strip():
                prompt_parts.append(f"{col}: {user_prompt.strip()}")
        if conclusion_prompt.strip():
            prompt_parts.append(f"\nConclusion:\n{conclusion_prompt.strip()}")

        combined_prompt = "\n".join(prompt_parts)
        combined_prompt += "\n\nRequirement Sample Data:\n"
        combined_prompt += requirement_df.head(10).to_csv(index=False)
        combined_prompt += "\n\nGenerate test cases structured according to the following columns:\n"
        combined_prompt += ", ".join(template_df.columns)

        # Send to Gemini
        response = model.generate_content(combined_prompt)
        st.subheader("✅ Generated Test Cases")
        st.markdown(response.text)

        # Step 5: Parse markdown table from response
        lines = response.text.strip().split("\n")
        table_lines = [line for line in lines if "|" in line and not line.strip().startswith("|:")]
        parsed_rows = []
        for line in table_lines:
            cells = [re.sub(r'<[^>]+>', '', cell.strip()) for cell in line.strip().split("|")[1:-1]]
            parsed_rows.append(cells)

        # Create DataFrame from parsed rows
        output_df = pd.DataFrame(parsed_rows[1:], columns=parsed_rows[0])
        output_df = output_df.reindex(columns=template_df.columns)

        # Save to Excel
        excel_output = io.BytesIO()
        with pd.ExcelWriter(excel_output, engine='openpyxl') as writer:
            output_df.to_excel(writer, index=False, sheet_name='GeneratedTestCases')
        excel_output.seek(0)

        st.download_button(
            label="📥 Download Generated Test Cases as Excel",
            data=excel_output,
            file_name="TestCases.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # Step 6: Save prompt, request, and response as TXT
        txt_content = f"=== INTRO PROMPT ===\n{intro_prompt.strip()}\n\n"
        txt_content += "=== REQUIREMENT COLUMN PROMPTS ===\n"
        txt_content += "\n".join([f"{col}: {requirement_prompts[col].strip()}" for col in requirement_df.columns if requirement_prompts[col].strip()])
        txt_content += f"\n\n=== CONCLUSION PROMPT ===\n{conclusion_prompt.strip()}\n\n"
        txt_content += f"=== FULL REQUEST ===\n{combined_prompt}\n\n"
        txt_content += f"=== RESPONSE ===\n{response.text}"

        txt_bytes = io.BytesIO(txt_content.encode("utf-8"))
        st.download_button(
            label="📥 Download Prompt and Response as TXT",
            data=txt_bytes,
            file_name="prompt_and_response.txt",
            mime="text/plain"
        )
