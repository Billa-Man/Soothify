from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.tools.wikidata.tool import WikidataAPIWrapper, WikidataQueryRun
from langchain.agents import Tool

from settings import settings

search = DuckDuckGoSearchRun()
wikidata = WikidataQueryRun(api_wrapper=WikidataAPIWrapper())

tools = [
    Tool.from_function(
        func=search.invoke,
        name="duckduckgo_search",
        description="Search the web using DuckDuckGo",
    ),
    Tool.from_function(
        func=wikidata.run,
        name="wikidata_query",
        description="Query Wikidata for information",
    ),
]