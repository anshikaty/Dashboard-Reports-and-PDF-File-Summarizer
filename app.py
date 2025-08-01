import streamlit as st
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import google.generativeai as genai
from langchain_community.vectorstores import FAISS
# from langchain.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
from gtts import gTTS
import io
# import tempfile
# import pyttsx3


load_dotenv()
GOOGLE_API_KEY=os.getenv("GOOGLE_API_KEY")

# GOOGLE_API_KEY=st.secrets("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("API Key not found. Please check your .env file.")


def get_pdf_text(pdf_docs):
    text=""
    for pdf in pdf_docs:
        pdf_reader= PdfReader(pdf)
        for page in pdf_reader.pages:
            text+= page.extract_text()
    return  text



def get_text_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=1000)
    chunks = text_splitter.split_text(text)
    return chunks


def get_vector_store(text_chunks):
    embeddings = GoogleGenerativeAIEmbeddings(model = "models/embedding-001")
    vector_store = FAISS.from_texts(text_chunks, embedding=embeddings)
    vector_store.save_local("faiss_index")


def get_conversational_chain():

    prompt_template = """
    Answer the question as detailed as possible from the provided context, make sure to provide all the details, if the answer is not in
    provided context just say, "answer is not available in the context", don't provide the wrong answer\n\n
    Context:\n {context}?\n
    Question: \n{question}\n

    Answer:
    """

    model = ChatGoogleGenerativeAI(model="gemini-2.5-flash",
                             temperature=0.3)

    prompt = PromptTemplate(template = prompt_template, input_variables = ["context", "question"])
    chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)

    return chain



def user_input(user_question):
    embeddings = GoogleGenerativeAIEmbeddings(model = "models/embedding-001")
    
    new_db = FAISS.load_local("faiss_index", embeddings,allow_dangerous_deserialization=True)
    docs = new_db.similarity_search(user_question)

    chain = get_conversational_chain()

    
    response = chain(
        {"input_documents":docs, "question": user_question}
        , return_only_outputs=True)
    
    output_text = response["output_text"]
    st.write("Reply: ", output_text)

    # Save response to session state for TTS
    st.session_state.generated_response = output_text

    # print(response)
    # st.write("Reply: ", response["output_text"])

    



def main():
    st.set_page_config("Chat PDF")
    st.header("Dashboard Reports and PDF Summarizer💁")

    user_question = st.text_input("Ask a Question from the uploaded Reports and PDF Files")

    if user_question:
        user_input(user_question)

        # "Speak the Answer" 
        if st.session_state.generated_response:
            if st.button("🔊 Speak the Answer"):
                try:
                
                    tts = gTTS(text=st.session_state.generated_response, lang='en', slow=False)

                
                    audio_bytes_io = io.BytesIO()
                    tts.write_to_fp(audio_bytes_io)
                    audio_bytes_io.seek(0) 

                
                    st.audio(audio_bytes_io.read(), format="audio/mp3")
                    st.success("Playing audio...")
                except Exception as e:
                        st.error(f"Error generating or playing audio: {e}")
                        st.info("Please ensure your device has an active internet connection for text-to-speech.")

        # if "generated_response" in st.session_state:
        #     if st.button("🔊 Speak the Answer"):
        #         engine = pyttsx3.init()
        #         engine.say(st.session_state.generated_response)
        #         engine.runAndWait()

    with st.sidebar:
        st.title("Menu:")
        pdf_docs = st.file_uploader("Upload your Reports or PDF Files and Click on the Submit & Process Button", accept_multiple_files=True)
        if st.button("Submit & Process"):
            with st.spinner("Processing..."):
                raw_text = get_pdf_text(pdf_docs)
                text_chunks = get_text_chunks(raw_text)
                get_vector_store(text_chunks)
                st.success("Done")



if __name__ == "__main__":
    main()