#---------- MODEL ----------
import streamlit as st

from langchain_openai.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferWindowMemory
from langchain.agents.agent_toolkits import create_conversational_retrieval_agent
from langchain.schema import ChatMessage
from langchain.callbacks.base import BaseCallbackHandler

from settings import settings
from application.chat_tools import tools
from database.functions.sidebar_functions import get_chat_history, save_chat_history



#---------- FRONTEND ----------