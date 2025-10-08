from crewai import Agent, Crew, Task, Process, LLM
from crewai.project import CrewBase, agent, task, crew, tool, llm, before_kickoff, after_kickoff
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List

from agents.tools.retriever_reranker import RetrieverRerankerTool
from agents.tools.conversation import ConversationTool
from config.config import Config

@CrewBase
class PolicyCrew:
    agents_config = 'agents.yaml'
    tasks_config = 'tasks.yaml'
    
    agents: List[BaseAgent]
    tasks: List[Task]
    
    def __init__(self):
        self.session_data = {}

    @agent
    def guardrail_agent(self) -> Agent:
        return Agent(config=self.agents_config['guardrail_agent'])

    @task
    def guardrail_task(self) -> Task:
        return Task(config=self.tasks_config['guardrail_task'])

    @agent
    def memorized_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['memorized_agent'],
            tools=[self.conversation(), self.retriever_reranker()]
        )

    @task
    def memorized_task(self) -> Task:
        return Task(config=self.tasks_config['memorized_task'])

    @agent
    def llm_agent(self) -> Agent:
        return Agent(config=self.agents_config['llm_agent'])

    @task
    def llm_task(self) -> Task:
        return Task(config=self.tasks_config['llm_task'])

    @tool
    def conversation(self) -> ConversationTool:
        return ConversationTool()
    
    @tool
    def retriever_reranker(self) -> RetrieverRerankerTool:
        return RetrieverRerankerTool()

    @llm
    def local_llm(self) -> LLM:
        return LLM(
            model=f"ollama/{Config.LLM_MODEL_NAME}",
            base_url=Config.OLLAMA_BASE_URL,
            temperature=0.1,
            max_tokens=64000,
            timeout=300,
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[self.guardrail_agent(), self.memorized_agent(), self.llm_agent()],
            tasks=[self.guardrail_task(), self.memorized_task(), self.llm_task()],
            process=Process.sequential,  # async_execution:true enables parallel execution
            verbose=True,
        )
    
    @before_kickoff
    def prepare_inputs(self, inputs):
        chat_id = inputs.get('chat_id', 'default_chat')
        query = inputs.get('query', '')
        
        self.session_data = {
            'chat_id': chat_id,
            'query': query
        }
        
        conversation = ConversationTool()
        conversation._run(chat_id=chat_id, message=query, role='user')
        
        return inputs
    
    @after_kickoff
    def store_assistant_response(self, result):
        if result and hasattr(result, 'tasks_output') and result.tasks_output:
            chat_id = self.session_data.get('chat_id', 'default_chat')
            conversation = ConversationTool()
            
            final_task_output = result.tasks_output[-1]
            if final_task_output and hasattr(final_task_output, 'raw') and final_task_output.raw:
                conversation.default_chat_id = chat_id
                conversation.store_assistant_response(response=final_task_output.raw)
        return result