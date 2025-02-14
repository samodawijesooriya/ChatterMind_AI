from langchain.document_loaders import TextLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Pinecone as LangchainPinecone
from langchain import PromptTemplate
from langchain.llms import HuggingFaceHub
from pinecone import ServerlessSpec,Pinecone
from dotenv import load_dotenv
import os

class ChatBot():
    load_dotenv()
    loader = TextLoader('../text.txt', encoding='utf-8')
    documents = loader.load()
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=4)
    docs = text_splitter.split_documents(documents)

    embeddings = HuggingFaceEmbeddings()
    pc = Pinecone(
        api_key=os.environ.get("PINECONE_API_KEY")
    )
    index_name = "langchain-demo"

    if index_name not in pc.list_indexes().names():
        pc.create_index(
            name=index_name,
            dimension=768,
            metric='cosine',
            spec=ServerlessSpec(
                cloud='aws',
                region="us-east-1"
            )
        )
        docsearch = LangchainPinecone.from_documents(docs, embeddings, index_name=index_name)
    else:
        docsearch = LangchainPinecone.from_documents(docs, embeddings, index_name=index_name)

    repo_id = "mistralai/Mixtral-8x7B-Instruct-v0.1"
    llm = HuggingFaceHub(
        repo_id=repo_id, model_kwargs={"temperature": 0.8, "top_p": 0.8, "top_k": 50}, huggingfacehub_api_token=os.getenv('HUGGINGFACE_API_KEY')
    )

    template = """
    You are a knowledgeable assistant. Users will ask you questions about the content of PDF documents. Use the following context extracted from the PDF to answer the question. 
    If you don't know the answer, just say you don't know. 
    Provide a concise answer, no longer than 2 sentences.

    Context: {context}
    Question: {question}
    Answer: 

    """

    prompt = PromptTemplate(template=template, input_variables=["context", "question"])

    from langchain.schema.runnable import RunnablePassthrough
    from langchain.schema.output_parser import StrOutputParser

    rag_chain = (
        {"context": docsearch.as_retriever(), "question": RunnablePassthrough()} 
        | prompt 
        | llm
        | StrOutputParser() 
    )

#result = ChatBot.rag_chain.invoke(input("Enter the question: "))

#print(result)