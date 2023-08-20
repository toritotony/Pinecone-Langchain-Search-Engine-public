import os
from flask import Flask, render_template, request
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Pinecone
from langchain.llms import OpenAI
from langchain.chains.question_answering import load_qa_chain
from tqdm import tqdm
import pinecone

app = Flask(__name__)

def index_pdf(pdf_path):
    loader = PyPDFLoader(pdf_path)
    data = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=0)
    texts = text_splitter.split_documents(data)

    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
    PINECONE_API_KEY = os.environ.get('PINECONE_API_KEY', '')
    PINECONE_API_ENV = os.environ.get('PINECONE_API_ENV', 'gcp-starter')

    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

    pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_API_ENV)
    index_name = "wolfe-test"
    docsearch = Pinecone.from_texts([t.page_content for t in texts], embeddings, index_name=index_name)

    return docsearch

def perform_query(index, query):
    docs = index.similarity_search(query)

    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
    llm = OpenAI(temperature=0, openai_api_key=OPENAI_API_KEY)
    chain = load_qa_chain(llm, chain_type="stuff")

    response = chain.run(input_documents=docs, question=query)
    return response

@app.route('/static/<path:filename>')
def serve_static(filename):
    return app.send_static_file(filename)

@app.route('/')
def search_form():
    return render_template('search_form.html')

@app.route('/search', methods=['POST'])
def search():
    pdf = request.files['pdf']
    query = request.form['query']

    if pdf and query:
        pdf_path = os.path.join('c:\\Users\\wolfe\\OneDrive\\Desktop\\BOOKS', pdf.filename)
        pdf.save(pdf_path)

        index = index_pdf(pdf_path)
        results = perform_query(index, query)

        return render_template('search_results.html', query=query, results=results)

    return "Please provide both a PDF and a query."

if __name__ == '__main__':
    app.run(debug=True)