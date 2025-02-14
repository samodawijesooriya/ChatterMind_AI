from langchain.document_loaders import TextLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Pinecone as LangchainPinecone
from langchain import PromptTemplate
from langchain.llms import HuggingFaceHub
from pinecone import ServerlessSpec, Pinecone
from dotenv import load_dotenv
import os

class ChatBot:
    def __init__(self):
        self.loader = None
        self.documents = None
        self.text_splitter = None
        self.docs = None
        self.index_name = None
        self.embeddings = None
        self.pc = None
        self.docsearch = None
        self.llm = None
        self.prompt = None
        self.rag_chain = None

    def setbot(self, text_file_path, index_name):
        self.loader = TextLoader(text_file_path, encoding='utf-8')
        self.documents = self.loader.load()
        self.text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=4)
        self.docs = self.text_splitter.split_documents(self.documents)
        self.index_name = index_name
        self.setup_index()
    def setup_index(self):
        load_dotenv()


        self.embeddings = HuggingFaceEmbeddings()
        self.pc = Pinecone(
            api_key=os.environ.get("PINECONE_API_KEY")
        )

        print(self.pc.list_indexes().names())



        if self.index_name not in self.pc.list_indexes().names():
            self.pc.create_index(
                name=self.index_name,
                dimension=768,
                metric='cosine',
                spec=ServerlessSpec(
                    cloud='aws',
                    region="us-east-1"
                )
            )
            self.docsearch = LangchainPinecone.from_documents(self.docs, self.embeddings, index_name=self.index_name)
        else:
            self.docsearch = LangchainPinecone.from_documents(self.docs, self.embeddings, index_name=self.index_name)

        self.setup_llm()

    def setup_llm(self):
        repo_id = "mistralai/Mixtral-8x7B-Instruct-v0.1"
        self.llm = HuggingFaceHub(
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

        self.prompt = PromptTemplate(template=template, input_variables=["context", "question"])

        from langchain.schema.runnable import RunnablePassthrough
        from langchain.schema.output_parser import StrOutputParser

        self.rag_chain = (
            {"context": self.docsearch.as_retriever(), "question": RunnablePassthrough()} 
            | self.prompt 
            | self.llm
            | StrOutputParser() 
        )

    def ask_question(self, question):
        response = self.rag_chain.invoke(question).split("Answer:")[-1].strip()
        if not response:
            return "Out of scope"
        return response
        

