from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from fastapi import FastAPI
from api.v1.routes.document import document_router
load_dotenv()

llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro")
# result=llm.invoke("Hi how are you?")

app = FastAPI()


app.include_router(document_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)