from google.adk.agents import LlmAgent, SequentialAgent
from tools import BrowserTool, search_knowledge_base
from google.adk.tools import FunctionTool

SearchTool = FunctionTool(func=search_knowledge_base)